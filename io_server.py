from aiohttp import web
import socketio

from constants import *
from handlers.io_routes import setup_routes

class IOServer:
    def __init__(self):
        self.sio = socketio.AsyncServer()
        self.app = web.Application()
        self.sio.attach(self.app)

        @self.sio.on(CONNECT)
        def connect(sid, environ):
            print('IO::{}::ID={}'.format(CONNECT, sid))
        
        @self.sio.on(CLIENT_DATA)
        async def receive_client_data(sid, data):
            print('IO::{}::ID={}, data={}'.format(CLIENT_DATA, sid, data))
            await self.send(SERVER_DATA, {'msg': 'Message received!'})

        @self.sio.on(ANGULAR_VELOCITY_ENTRY)
        def receive_angular_velocity(sid, data):
            print('IO::{}::ID={}, data={}'.format(ANGULAR_VELOCITY_ENTRY, sid, data))
        
        @self.sio.on(LINEAR_ACCELERATION_ENTRY)
        def receive_linear_acceleration(sid, data):
            print('IO::{}::ID={}, data={}'.format(LINEAR_ACCELERATION_ENTRY, sid, data))

        @self.sio.on(HEART_RATE_ENTRY)
        def receive_heart_rate(sid, data):
            print('IO::{}::ID={}, data={}'.format(HEART_RATE_ENTRY, sid, data))

        @self.sio.on(TEMPERATURE_ENTRY)
        def receive_temperature(sid, data):
            print('IO::{}::ID={}, data={}'.format(TEMPERATURE_ENTRY, sid, data))
        
        @self.sio.on(MAGNETIC_FIELD_ENTRY)
        def receive_magnetic_field(sid, data):
            print('IO::{}::ID={}, data={}'.format(MAGNETIC_FIELD_ENTRY, sid, data))

        @self.sio.on(DISCONNECT)
        def diconnect(sid):
            print('IO::{}::ID={}'.format(DISCONNECT, sid))

        setup_routes(self.app)

    def serve(self):
        web.run_app(self.app, port=8080)

    async def send(self, event, data):
        await self.sio.emit(event, data)


if __name__ == '__main__':
    server = IOServer()
    server.serve()

