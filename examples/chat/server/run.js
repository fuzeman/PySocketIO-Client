var io = require('socket.io')(),
    user_sockets = {},
    user_names = {};

io.on('connection', function (socket) {
    socket.on('chat.login', function(username) {
        socket.username = username;

        user_sockets[username] = socket;
        user_names[username] = username;

        socket.emit('chat.message', 'SERVER', 'you have connected');

        socket.broadcast.emit('chat.message', 'SERVER', username + ' has connected');

        io.emit('chat.users', user_names);
    });

    socket.on('chat.send', function(data) {
        io.emit('chat.message', socket.username, data);
    });
});

io.listen(8000);