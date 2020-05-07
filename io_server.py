from aiohttp import web
import socketio

from constants import *
from handlers.io_routes import setup_routes
from data.collection import Collection


class IOServer:
    def __init__(self):
        self.sio = socketio.AsyncServer()
        self.app = web.Application()
        self.sio.attach(self.app)

        # Import data
        # self.av_data = Collection('angular_velocity')
        # self.av_data.import_data(AV_FILE, 1)
        # self.hr_data = Collection('heart_rate')
        # self.hr_data.import_data(HR_FILE, 1)
        # self.la_data = Collection('linear_acceleration')
        # self.la_data.import_data(LA_FILE, 1)
        # self.mf_data = Collection('magnetic_field')
        # self.mf_data.import_data(MF_FILE, 1)
        # self.te_data = Collection('temperature')
        # self.te_data.import_data(TE_FILE, 1)

        # Initialize with blank data
        self.av_data = Collection('angular_velocity', [],
                                  attr_names=[SENSOR, TIME, X, Y, Z],
                                  attr_types=[REAL, REAL, REAL, REAL, REAL],
                                  label_count=1)
        self.hr_data = Collection('heart_rate', [],
                                  attr_names=[SENSOR, TIME, AVERAGE],
                                  attr_types=[REAL, REAL, REAL],
                                  label_count=1)
        self.la_data = Collection('linear_acceleration', [],
                                  attr_names=[SENSOR, TIME, X, Y, Z],
                                  attr_types=[REAL, REAL, REAL, REAL, REAL],
                                  label_count=1)
        self.mf_data = Collection('magnetic_field', [],
                                  attr_names=[SENSOR, TIME, X, Y, Z],
                                  attr_types=[REAL, REAL, REAL, REAL, REAL],
                                  label_count=1)
        self.te_data = Collection('temperature', [],
                                  attr_names=[SENSOR, TIME, MEASUREMENT],
                                  attr_types=[REAL, REAL, REAL],
                                  label_count=1)

        setup_routes(self.app)
        self.init_socketio()

    def serve(self):
        web.run_app(self.app, port=8080)

    async def send(self, event, data):
        await self.sio.emit(event, data)

    def init_socketio(self):
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
            self.av_data.add_entry(data)

        @self.sio.on(HEART_RATE_ENTRY)
        def receive_heart_rate(sid, data):
            print('IO::{}::ID={}, data={}'.format(HEART_RATE_ENTRY, sid, data))
            self.hr_data.add_entry(data)
        
        @self.sio.on(LINEAR_ACCELERATION_ENTRY)
        def receive_linear_acceleration(sid, data):
            print('IO::{}::ID={}, data={}'.format(LINEAR_ACCELERATION_ENTRY, sid, data))
            self.la_data.add_entry(data)

        @self.sio.on(MAGNETIC_FIELD_ENTRY)
        def receive_magnetic_field(sid, data):
            print('IO::{}::ID={}, data={}'.format(MAGNETIC_FIELD_ENTRY, sid, data))
            self.mf_data.add_entry(data)

        @self.sio.on(TEMPERATURE_ENTRY)
        def receive_temperature(sid, data):
            print('IO::{}::ID={}, data={}'.format(TEMPERATURE_ENTRY, sid, data))
            self.temp_data.add_entry(data)

        @self.sio.on(DISCONNECT)
        def diconnect(sid):
            print('IO::{}::ID={}'.format(DISCONNECT, sid))


if __name__ == '__main__':
    server = IOServer()
    print(server.av_data)
    print()
    print(server.hr_data)
    print()
    print(server.la_data)
    print()
    print(server.mf_data)
    print()
    print(server.te_data)
    print()
    server.serve()

