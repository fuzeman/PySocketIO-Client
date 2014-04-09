import pysocketio.client as io
import logging

logging.basicConfig(level=logging.DEBUG)
socket = io.connect('http://localhost:8000')

@socket.on('connect')
def connected():
    print "connected"


while True:
    raw_input()
