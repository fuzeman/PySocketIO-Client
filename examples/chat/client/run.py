import pysocketio_client as io
import logging

logging.basicConfig(level=logging.DEBUG)

username = raw_input('username: ')

socket = io.connect('http://localhost:8000')

@socket.on('connect')
def connected():
    socket.emit('chat.login', username)

@socket.on('chat.message')
def message_received(from_user, data):
    print "MESSAGE - %s - %s" % (from_user, data)


@socket.on('chat.users')
def users_changed(users):
    print "USERS - %s" % users


while True:
    message = raw_input()

    if message:
        socket.emit('chat.send', message)
