var io = require('socket.io')();

io.on('connection', function (socket) {
    socket.emit('news', { hello: 'world' });

    socket.on('my other event', function (data) {
        console.log(data);
    });
});

io.listen(8000);