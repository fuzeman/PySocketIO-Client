from pysocketio_client.util import has_binary, is_callable
from pyemitter import Emitter, on
import pysocketio_parser as parser
import logging

log = logging.getLogger(__name__)


# Internal events (blacklisted).
# These events can't be emitted by the user.
INTERNAL_EVENTS = [
    'connect',
    'disconnect',
    'error'
]


class Socket(Emitter):
    def __init__(self, io, nsp):
        """`Socket` constructor."""
        self.io = io
        self.nsp = nsp

        self.ids = 0
        self.acks = {}
        self.subs = []
        self.buffer = []

        self.connected = False
        self.disconnected = True

        self.open()

    def open(self):
        """Called upon engine `open`."""
        if self.connected:
            return self

        io = self.io
        io.open()  # ensure open

        self.subs = [
            on(io, 'open', self.on_open),
            on(io, 'error', self.on_error),
            on(io, 'packet', self.on_packet),
            on(io, 'close', self.on_close)
        ]

        if io.ready_state == 'open':
            self.on_open()

        return self

    def send(self, *args):
        """Sends a `message` event."""
        raise NotImplementedError()

    def emit(self, ev, *args):
        """Override `emit`.
           If the event is in `events`, it's emitted normally.

        :param ev: event name
        :type ev: str
        """
        if ev in INTERNAL_EVENTS:
            super(Socket, self).emit(ev, *args)
            return self

        args = [ev] + list(args)
        parser_type = parser.EVENT  # default type

        if has_binary(args):
            parser_type = parser.BINARY_EVENT  # binary type

        packet = {'type': parser_type, 'data': args}

        # event ack callback
        if args and is_callable(args[-1]):
            log.debug('emitting packet with ack id %s', self.ids)
            self.acks[self.ids] = args.pop()
            self.ids += 1

            packet['id'] = self.ids

        self.packet(packet)

        return self

    def packet(self, packet):
        """Sends a packet."""
        packet['nsp'] = self.nsp
        self.io.packet(packet)

    def on_error(self, data):
        """Called upon `error`."""
        raise NotImplementedError()

    def on_open(self):
        """"Opens" the socket."""
        log.debug('transport is open - connecting')

        # write connect packet if necessary
        if self.nsp != '/':
            self.packet({type: parser.CONNECT})

    def on_close(self, reason):
        """Called upon engine `close`."""
        log.debug('close (%s)', reason)

        self.connected = False
        self.disconnected = True

        self.emit('disconnect', reason)

    def on_packet(self, packet):
        """Called with socket packet."""
        if packet.get('nsp') != self.nsp:
            return

        p_type = packet.get('type')

        if p_type == parser.CONNECT:
            return self.on_connect()

        if p_type == parser.EVENT:
            self.on_event(packet)

        if p_type == parser.BINARY_EVENT:
            self.on_event(packet)

        if p_type == parser.ACK:
            self.on_ack(packet)

        if p_type == parser.DISCONNECT:
            self.on_disconnect()

        if p_type == parser.ERROR:
            self.emit('error', packet.get('data'))

    def on_event(self, packet):
        """Called upon a server event."""
        args = packet.get('data') or []
        log.debug('emitting event %s', args)

        if packet.get('id'):
            log.debug('attaching ack callback to event')
            args.append(self.ack(packet['id']))

        if self.connected:
            super(Socket, self).emit(*args)
        else:
            self.buffer.append(args)

    def ack(self, id):
        """Produces an ack callback to emit with an event."""
        raise NotImplementedError()

    def on_ack(self, packet):
        """Called upon a server acknowlegement."""
        raise NotImplementedError()

    def on_connect(self):
        """Called upon server connect."""
        self.connected = True
        self.disconnected = False

        self.emit('connect')
        self.emit_buffered()

    def emit_buffered(self):
        """Emit buffered events."""
        for args in self.buffer:
            super(Socket, self).emit(*args)

        self.buffer = []

    def on_disconnect(self):
        """Called upon server disconnect."""
        raise NotImplementedError()

    def destroy(self):
        """Called upon forced client/server side disconnections,
           this method ensures the manager stops tracking us and
           that reconnections don't get triggered for this.
        """
        raise NotImplementedError()

    def close(self):
        """Disconnects the socket manually."""
        raise NotImplementedError()
