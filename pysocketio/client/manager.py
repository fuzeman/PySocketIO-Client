from pysocketio.client.events import on
from pysocketio.client.socket import Socket

from pyemitter import Emitter
import pyengineio as eio
import logging

log = logging.getLogger(__name__)


class Manager(Emitter):
    def __init__(self, uri, opts=None):
        self.uri = uri
        self.opts = opts or {}

        self.nsps = {}
        self.subs = []

        self.engine = None
        self.ready_state = 'closed'

        self._timeout = None

    def socket(self, nsp):
        socket = self.nsps.get(nsp)

        if not socket:
            socket = Socket(self, nsp)
            self.nsps[nsp] = socket
            #var self = this;
            #socket.on('connect', function(){
            #    self.connected++;
            #});

        return socket

    def open(self, fn=None):
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
            if fn:
                fn()

        # emit 'connect_error'
        @on(socket, 'error')
        def error_sub(data):
            log.debug('connect_error')
            self.cleanup()
            self.ready_state = 'closed'
            self.emit('connect_error', data)

            if fn:
                fn(Exception('Connection error', data))

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
        log.debug('open')

        # clear old subs
        self.cleanup()

        # mark as open
        self.ready_state = 'open'
        self.emit('open')

        # add new subs
        socket = self.engine
        self.subs.append(on(socket, 'data', self.on_data))
        self.subs.append(on(socket, 'decoded', self.on_decoded()))
        self.subs.append(on(socket, 'error', self.on_error))
        self.subs.append(on(socket, 'close', self.on_close))

    def cleanup(self):
        pass

    def maybe_reconnect(self):
        pass

    def on_data(self):
        pass

    def on_decoded(self):
        pass

    def on_error(self):
        pass

    def on_close(self):
        pass