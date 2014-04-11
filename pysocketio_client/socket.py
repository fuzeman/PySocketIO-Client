from pyemitter import Emitter, on
import logging

log = logging.getLogger(__name__)


class Socket(Emitter):
    def __init__(self, io, nsp):
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

    def on_open(self):
        log.debug('transport is open - connecting')

        # write connect packet if necessary
        if self.nsp != '/':
            self.packet({type: parser.CONNECT})

    def send(self, *args):
        pass

    def emit(self, ev, *args):
        pass

    def packet(self, packet):
        pass

    def on_error(self, data):
        pass

    def on_close(self, reason):
        pass

    def on_packet(self, packet):
        pass

    def on_event(self, packet):
        pass

    def ack(self, id):
        pass

    def on_ack(self, packet):
        pass

    def on_connect(self):
        pass

    def emit_buffered(self):
        pass

    def on_disconnect(self):
        pass

    def destroy(self):
        pass

    def close(self):
        pass
