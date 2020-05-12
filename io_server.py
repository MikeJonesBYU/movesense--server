from argparse import ArgumentParser
from aiohttp import web
import socketio

from constants import *
from settings import *
from handlers.base import BaseHandler
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
                                  attr_types=[
                                      Collection.STRING, Collection.INTEGER,
                                      Collection.REAL, Collection.REAL,
                                      Collection.REAL],
                                  label_count=1)
        self.hr_data = Collection('heart_rate', [],
                                  attr_names=[SENSOR, TIME, AVERAGE],
                                  attr_types=[
                                      Collection.STRING, Collection.INTEGER,
                                      Collection.REAL],
                                  label_count=1)
        self.la_data = Collection('linear_acceleration', [],
                                  attr_names=[SENSOR, TIME, X, Y, Z],
                                  attr_types=[
                                      Collection.STRING, Collection.INTEGER,
                                      Collection.REAL, Collection.REAL,
                                      Collection.REAL],
                                  label_count=1)
        self.mf_data = Collection('magnetic_field', [],
                                  attr_names=[SENSOR, TIME, X, Y, Z],
                                  attr_types=[
                                      Collection.STRING, Collection.INTEGER,
                                      Collection.REAL, Collection.REAL,
                                      Collection.REAL],
                                  label_count=1)
        self.te_data = Collection('temperature', [],
                                  attr_names=[SENSOR, TIME, MEASUREMENT],
                                  attr_types=[
                                      Collection.STRING, Collection.INTEGER,
                                      Collection.REAL],
                                  label_count=1)

        # Setup Handlers
        base_handler = BaseHandler()
        self.app.router.add_get('/', handler=base_handler.index)

        # Setup Socket IO
        self.init_socketio()

    def serve(self, port=PORT):
        web.run_app(self.app, port=port)

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
        async def receive_angular_velocity(sid, data):
            print('IO::{}::ID={}, data={}'.format(ANGULAR_VELOCITY_ENTRY, sid, data))
            analysis = self.av_data.add_entry(data)
            if analysis is not None:
                print('IO::{}::ANALYSIS={}'.format(ANGULAR_VELOCITY_ENTRY, analysis))
                await self.send(SERVER_DATA, analysis)

        @self.sio.on(HEART_RATE_ENTRY)
        async def receive_heart_rate(sid, data):
            print('IO::{}::ID={}, data={}'.format(HEART_RATE_ENTRY, sid, data))
            analysis = self.hr_data.add_entry(data)
            if analysis is not None:
                print('IO::{}::ANALYSIS={}'.format(HEART_RATE_ENTRY, analysis))
                await self.send(SERVER_DATA, analysis)
        
        @self.sio.on(LINEAR_ACCELERATION_ENTRY)
        async def receive_linear_acceleration(sid, data):
            print('IO::{}::ID={}, data={}'.format(LINEAR_ACCELERATION_ENTRY, sid, data))
            analysis = self.la_data.add_entry(data)
            if analysis is not None:
                print('IO::{}::ANALYSIS={}'.format(LINEAR_ACCELERATION_ENTRY, analysis))
                await self.send(SERVER_DATA, analysis)

        @self.sio.on(MAGNETIC_FIELD_ENTRY)
        async def receive_magnetic_field(sid, data):
            print('IO::{}::ID={}, data={}'.format(MAGNETIC_FIELD_ENTRY, sid, data))
            analysis = self.mf_data.add_entry(data)
            if analysis is not None:
                print('IO::{}::ANALYSIS={}'.format(MAGNETIC_FIELD_ENTRY, analysis))
                await self.send(SERVER_DATA, analysis)

        @self.sio.on(TEMPERATURE_ENTRY)
        async def receive_temperature(sid, data):
            print('IO::{}::ID={}, data={}'.format(TEMPERATURE_ENTRY, sid, data))
            analysis = self.temp_data.add_entry(data)
            if analysis is not None:
                print('IO::{}::ANALYSIS={}'.format(TEMPERATURE_ENTRY, analysis))
                await self.send(SERVER_DATA, analysis)

        @self.sio.on(DISCONNECT)
        def diconnect(sid):
            print('IO::{}::ID={}'.format(DISCONNECT, sid))


if __name__ == '__main__':
    parser = ArgumentParser(description='Process server settings')
    parser.add_argument('-p', '--port', type=int,
                        required=False, help='Server port number')
    args = parser.parse_args()
    server = IOServer()

    if args.port:
        server.serve(port=args.port)
    else:
        server.serve()

