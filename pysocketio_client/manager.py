from pysocketio_client.util import delayed_call, delayed_cancel
from pysocketio_client.socket import Socket

from pyemitter import Emitter, on
import pyengineio_client as eio
import pysocketio_parser as parser
import logging

log = logging.getLogger(__name__)


class Manager(Emitter):
    def __init__(self, uri, opts=None):
        """`Manager` constructor.

        :param uri: engine uri
        :type uri: str

        :param opts: options
        :type opts: dict
        """
        if opts is None:
            opts = {}

        opts['path'] = opts.get('path') or '/socket.io'

        self.nsps = {}
        self.subs = []
        self.opts = opts

        self.ready_state = 'closed'
        self.uri = uri
        self.connected = 0

        self.encoding = False
        self.packet_buffer = []

        self.encoder = parser.Encoder()
        self.decoder = parser.Decoder()

        self.engine = None

        self._reconnection = opts.get('reconnection', True)
        self._reconnection_attempts = opts.get('reconnection_attempts')
        self._reconnection_delay = opts.get('reconnection_delay', 1000)
        self._reconnection_delay_max = opts.get('reconnection_delay_max', 5000)

        self._timeout = opts.get('timeout', 20000)

        self.open_reconnect = False
        self.reconnecting = False
        self.attempts = 0

        self.open()

    @property
    def reconnection(self):
        return self._reconnection

    @reconnection.setter
    def reconnection(self, value):
        """Sets the `reconnection` config.

        :param value: True if we should automatically reconnect
        :type value: bool
        """
        self._reconnection = value

    @property
    def reconnection_attempts(self):
        return self._reconnection_attempts

    @reconnection_attempts.setter
    def reconnection_attempts(self, value):
        """Sets the reconnection attempts config.

        :param value: max reconnection attempts before giving up
        :type value: int
        """
        self._reconnection_attempts = value

    @property
    def reconnection_delay(self):
        return self._reconnection_delay

    @reconnection_delay.setter
    def reconnection_delay(self, value):
        """Sets the delay between reconnections.

        :param value: delay (in milliseconds)
        :type value: int
        """
        self._reconnection_delay = value

    @property
    def reconnection_delay_max(self):
        return self._reconnection_delay_max

    @reconnection_delay_max.setter
    def reconnection_delay_max(self, value):
        """Sets the maximum delay between reconnections.

        :param value: max delay (in milliseconds)
        :type value: int
        """
        self._reconnection_delay_max = value

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        """Sets the connection timeout.

        :param value: timeout (in milliseconds) or `False` to disable
        :type value: int or False
        """
        self._timeout = value

    def maybe_reconnect(self):
        """Starts trying to reconnect if reconnection is enabled and we have not
           started reconnecting yet"""

        if not self.open_reconnect and not self.reconnecting and self.reconnection:
            self.open_reconnect = True
            self.reconnect()

    def open(self, func=None):
        """Sets the current transport `socket`.

        :param func: callback
        :type func: function
        """
        log.debug('readyState %s', self.ready_state)

        if self.ready_state.startswith('open'):
            return self

        log.debug('opening %s', self.uri)
        self.engine = eio.connect(self.uri, self.opts)
        socket = self.engine
        self.ready_state = 'opening'

        # emit 'open'
        @on(socket, 'open')
        def open_sub():
            self.on_open()

            # Trigger callback
            if func:
                func()

        # emit 'connect_error'
        @on(socket, 'error')
        def error_sub(data):
            log.debug('connect_error')
            self.cleanup()
            self.ready_state = 'closed'
            self.emit('connect_error', data)

            if func:
                func(Exception('Connection error', data))

            self.maybe_reconnect()

        # TODO emit 'connect_timeout'
        if self._timeout:
            timeout = self._timeout
            log.debug('connect attempt will timeout after %s', timeout)

            # set timer
            #var timer = setTimeout(function(){
            #    debug('connect attempt timed out after %d', timeout);
            #    openSub.destroy();
            #    socket.close();
            #    socket.emit('error', 'timeout');
            #    self.emit('connect_timeout', timeout);
            #}, timeout)

            #self.subs.push({
            #    destroy: function(){
            #        clearTimeout(timer);
            #    }
            #})

        self.subs.append(open_sub)
        self.subs.append(error_sub)

        return self

    def on_open(self):
        """Called upon transport open."""
        log.debug('open')

        # clear old subs
        self.cleanup()

        # mark as open
        self.ready_state = 'open'
        self.emit('open')

        # add new subs
        socket = self.engine
        self.subs.append(on(socket, 'data', self.on_data))
        self.subs.append(on(self.decoder, 'decoded', self.on_decoded))
        self.subs.append(on(socket, 'error', self.on_error))
        self.subs.append(on(socket, 'close', self.on_close))

    def on_data(self, data):
        """Called with data."""
        self.decoder.add(data)

    def on_decoded(self, packet):
        """Called when parser fully decodes a packet."""
        self.emit('packet', packet)

    def on_error(self, err):
        """Called upon socket error."""
        log.debug('error %s', err)
        self.emit('error', err)

    def socket(self, nsp):
        """Creates a new socket for the given `nsp`.

        :rtype: Socket
        """
        socket = self.nsps.get(nsp)

        if not socket:
            socket = Socket(self, nsp)
            self.nsps[nsp] = socket

            @socket.on('connect')
            def socket_connected():
                self.connected += 1

        return socket

    def destroy(self, socket):
        """Called upon a socket close.

        :param socket: Socket to destroy
        :type socket: Socket
        """
        self.connected -= 1

        if not self.connected:
            self.close()

    def packet(self, packet):
        """Writes a packet.

        :param packet: packet
        :type packet: dict
        """
        log.debug('writing packet %s', packet)

        if not self.encoding:
            self.encoding = True

            def encoded(packets):
                for p in packets:
                    self.engine.write(p)

                self.encoding = False
                self.process_packet_queue()

            self.encoder.encode(packet, encoded)
        else:
            self.packet_buffer.append(packet)

    def process_packet_queue(self):
        """If packet buffer is non-empty, begins encoding the
           next packet in line."""
        if self.packet_buffer and not self.encoding:
            pack = self.packet_buffer.pop(0)
            self.packet(pack)

    def cleanup(self):
        """Clean up transport subscriptions and packet buffer."""
        # TODO unbind `subs`

        self.encoding = False
        self.packet_buffer = []

        self.decoder.destroy()

    def close(self):
        """Close the current socket."""
        self.skip_reconnect = True
        self.engine.close()

    def on_close(self, reason):
        """Called upon engine close."""
        log.debug('close')

        self.cleanup()
        self.ready_state = 'closed'
        self.emit('close', reason)

        if self.reconnection and not self.skip_reconnect:
            self.reconnect()

    def reconnect(self):
        """Attempt a reconnection."""
        if self.reconnecting:
            return self

        attempts_max = self.reconnection_attempts

        self.attempts += 1

        if attempts_max is not None and self.attempts > attempts_max:
            log.debug('reconnection failed')
            self.emit('reconnect_failed')
            self.reconnecting = False
        else:
            delay = self.attempts * self.reconnection_delay
            delay = min(delay, self.reconnection_delay_max)
            delay = float(delay) / 1000

            log.debug('will wait %ss before reconnection attempt', delay)
            self.reconnecting = True

            @delayed_call(delay)
            def attempt():
                log.debug('attempting reconnect')
                self.emit('reconnect_attempt')

                def open_callback(exc=None):
                    if exc:
                        log.debug('reconnect attempt error')
                        self.reconnecting = False
                        self.reconnect()
                        self.emit('reconnect_error', exc)
                    else:
                        log.debug('reconnect success')
                        self.on_reconnect()

                self.open(open_callback)

            self.subs.append({
                'destroy': lambda: delayed_cancel(attempt)
            })

    def on_reconnect(self):
        """Called upon successful reconnect."""
        attempt = self.attempts

        self.attempts = 0
        self.reconnecting = False

        self.emit('reconnect', attempt)
