import pysocketio_client as io
import logging

logging.basicConfig(level=logging.DEBUG)
socket = io.connect('http://localhost:8000')

@socket.on('connect')
def connected():
    print "connected"

@socket.on('news')
def news(data):
    print "NEWS - %s" % data


while True:
    raw_input()
