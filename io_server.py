from aiohttp import web
import socketio

from constants import *


class IOServer:
    def __init__(self):
        self.sio = socketio.AsyncServer()
        self.app = web.Application()
        self.sio.attach(self.app)

        @self.sio.on(CONNECT)
        def connect(sid, environ):
            print('IO::CONNECT::ID={}'.format(sid))

        @self.sio.on(CLIENT_DATA)
        async def receive_client_data(sid, data):
            print('IO::RECEIVE::ID={}, data={}'.format(sid, data))
            await self.send(SERVER_DATA, {'msg': 'Hello there!'})

        @self.sio.on(DISCONNECT)
        def diconnect(sid):
            print('IO::DISCONNECT::ID={}'.format(sid))

    def serve(self):
        web.run_app(self.app)

    async def send(self, event, data):
        await self.sio.emit(event, data)


if __name__ == '__main__':
    server = IOServer()
    server.serve()

