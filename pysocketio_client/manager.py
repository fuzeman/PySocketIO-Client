from pyemitter import Emitter, on
from pysocketio_client.socket import Socket
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

        self.encoding = False
        self.packet_buffer = []

        self.encoder = parser.Encoder()
        self.decoder = parser.Decoder()

        self.engine = None
        self._timeout = None

        self.open()

    def maybe_reconnect(self):
        """Starts trying to reconnect if reconnection is enabled and we have not
           started reconnecting yet"""
        raise NotImplementedError()

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

            #socket.on('connect', function(){
            #    self.connected++;
            #});

        return socket

    def destroy(self, socket):
        """Called upon a socket close.

        :param socket: Socket to destroy
        :type socket: Socket
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

    def on_close(self, reason):
        """Called upon engine close."""
        raise NotImplementedError()

    def reconnect(self):
        """Attempt a reconnection."""
        raise NotImplementedError()

    def on_reconnect(self):
        """Called upon successful reconnect."""
        raise NotImplementedError()
