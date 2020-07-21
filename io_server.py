#!/usr/bin/env python3

from aiohttp import web
import asyncio
from argparse import ArgumentParser
from datetime import datetime
import os
import socketio
import uuid

from model_keys import *
from settings import *
from handlers.base import BaseHandler
from tools.analyzer import Analyzer
from tools.db import DBManager

EVENT_LOOP = asyncio.get_event_loop()

class IOServer:
    ##
    # IO Events
    ##
    CONNECT                   = 'connect'
    CONNECT_ERROR             = 'connect_error' 
    DISCONNECT                = 'disconnect'
    HEARTBEAT                 = 'heartbeat'

    ###
    # Client Events
    ###
    CLIENT_DATA               = 'client_data'
    START_SESSION             = 'start_session'
    READING_ENTRY             = 'reading_entry'
    END_SESSION               = 'end_session'
    CLIENT_REQUEST            = 'request_data'

    ###
    # Server Events
    ###
    EVENT_SERVER_SHUTDOWN     = 'shutdown'
    EVENT_NOT_FOUND           = 'no_event_found'
    EVENT_FOUND               = 'event_found'
    EVENT_DATA                = 'event_data'
    SERVER_DATA               = 'server_data'
    ANALYZED_DATA             = 'analyzed_data'
    REQUEST_RESPONSE          = 'request_response'


    def __init__(self, bool_clf_dir=BOOL_CLF_DIR, type_clf_dir=TYPE_CLF_DIR):
        self.sio = socketio.AsyncServer()
        self.app = web.Application()
        self.sio.attach(self.app)
        self.sockets = []

        bool_clf = self.get_latest_clf(BOOL_CLF_DIR)
        type_clf = self.get_latest_clf(TYPE_CLF_DIR)

        self.analyzer = Analyzer(pickled_bool_clf=bool_clf,
                                 pickled_type_clf=type_clf)

        # Setup database to store sessions. Load stored sessions.
        self.db = DBManager()

        # Setup Handlers
        base_handler = BaseHandler(self.analyzer, bool_clf_dir, type_clf_dir)
        self.app.router.add_get('/', handler=base_handler.index)
        self.app.router.add_post(
            '/bool-classifier', handler=base_handler.add_bool_classifier)
        self.app.router.add_post(
            '/type-classifier', handler=base_handler.add_type_classifier)

        # Setup Socket IO
        self.init_socketio()

    def get_latest_clf(self, clf_dir):
        clf_list = [os.path.join(clf_dir, f) for f in os.listdir(clf_dir) if os.path.isfile(
            os.path.join(clf_dir, f)) and f.endswith('.pkl')]
        if len(clf_list) > 0:
            return max(clf_list, key=os.path.getctime)
        return None

    def serve(self, port=PORT):
        web.run_app(self.app, port=port)

    async def send(self, event, data):
        await self.sio.emit(event, data)

    def save_data(self, file, data):
        file = open(file, 'a')
        file.write('{}\n'.format(data))
        file.close()       

    def init_socketio(self):
        @self.sio.on(self.CONNECT)
        async def connect(sid, environ):
            print('{} -- ID={} -- {}'.format(datetime.now(), sid, self.CONNECT))
            await self.send(self.HEARTBEAT, {self.HEARTBEAT: '1'})
            self.sockets.append(sid)
            print('sockets: {}'.format(self.sockets))

        @self.sio.on(self.CONNECT_ERROR)
        def connect_error(sid, data):
            print('{} -- ID={} -- {}'.format(datetime.now(), sid, self.CONNECT_ERROR))
            print('\tdata={}'.format(data))

        @self.sio.on(self.START_SESSION)
        def start_session(sid, data):
            print('{} -- ID={} -- {}'.format(datetime.now(), sid, self.START_SESSION))
            print('\tdata={}'.format(data))
            self.db.start_session(data[ID], data[ATHLETE_ID], data[SPORT],
                                  data[START_TIME],
                                  placements=data[SENSOR_PLACEMENTS])

        @self.sio.on(self.READING_ENTRY)
        async def receive_reading(sid, data):
            #print('{} -- ID={} -- {}, data={}'.format(datetime.now(), sid, self.READING_ENTRY, data))
            # Unpack for db
            self.db.add_reading(
                data[SESSION_ID], data[SENSOR_ID], uuid.uuid4(),
                data[TIME], data[ACCELEROMETER],
                data[GYROSCOPE], data[MAGNETOMETER])

            reading_count = self.db.get_reading_count(data[SESSION_ID])
            if self.analyzer.bool_can_analyze(reading_count):
                start = -1*self.analyzer.bool_window_size # Only analyze latest window
                readings = self.db.get_readings(data[SESSION_ID])[start:]

                found_event = await self.analyzer.is_event(readings)
                print('found event analysis: {}'.format(found_event))

                athlete = self.db.get_session(data[SESSION_ID]).athlete
                bool_clf = self.analyzer.get_bool_clf_name()
                if found_event:
                    print('{} -> {} -- FOUND_EVENT'.format(
                        readings[0].timestamp, readings[-1].timestamp))
                    event_id = uuid.uuid4()
                    await self.send(self.EVENT_FOUND, {
                        EVENT_ID: str(event_id),
                        SESSION_ID: data[SESSION_ID],
                        ATHLETE_ID: str(athlete),
                        BOOL_CLASSIFIER: bool_clf,
                        START_TIME: readings[0].timestamp,
                        END_TIME: readings[-1].timestamp
                    })
                else:
                    print('{} -> {} -- NO EVENT FOUND'.format(
                        readings[0].timestamp, readings[-1].timestamp))
                    await self.send(self.EVENT_NOT_FOUND, {
                        START_TIME: readings[0].timestamp,
                        END_TIME: readings[-1].timestamp
                    })

                # Run type classifier to predict event
                if found_event and self.analyzer.type_can_analyze(reading_count):                    
                    start = -1*self.analyzer.type_window_size # Only analyze latest window
                    readings = self.db.get_readings(data[SESSION_ID])[start:]
                    event_type = await self.analyzer.predict_event_type(
                        readings)
                    type_clf = self.analyzer.get_type_clf_name()
                    print('{} -- {} -- SEND_EVENT={}'.format(
                        datetime.now(), self.READING_ENTRY, event_type))
                    
                    event = self.db.add_event(
                        event_id, data[SESSION_ID], event_type,
                        readings[0].timestamp, readings[-1].timestamp,
                        bool_clf, type_clf)

                    await self.send(self.EVENT_DATA,
                                    event.dictionary(self.db.db))

        @self.sio.on(self.HEARTBEAT)
        async def send_heartbeat(sid, data):
            print('{} -- ID={} -- {}'.format(datetime.now(), sid, self.HEARTBEAT))
            await self.send(self.HEARTBEAT, {self.HEARTBEAT: '1'})

        @self.sio.on(self.END_SESSION)
        def end_session(sid, data):
            print('{} -- ID={} -- {}'.format(datetime.now(), sid, self.END_SESSION))
            print('\tdata={}'.format(data))
            self.db.end_session(data[ID], data[END_TIME])

        @self.sio.on(self.CLIENT_REQUEST)
        async def handle_request(sid, data):
            print('{} -- ID={} -- {}'.format(
                datetime.now(), sid, self.CLIENT_REQUEST))
            print('\tdata={}'.format(data))
            sessions = self.db.get_all_sessions(data[ATHLETE_ID])
            await self.send(self.REQUEST_RESPONSE, {
                SESSION_ID: [
                    session.dictionary(self.db.db) for session in sessions]
            })

        @self.sio.on(self.DISCONNECT)
        def diconnect(sid):
            print('{} -- ID={} -- {}'.format(datetime.now(), sid, self.DISCONNECT))
            self.sockets.remove(sid)

if __name__ == '__main__':
    parser = ArgumentParser(description='Process server settings')
    parser.add_argument('-p', '--port', type=int,
                        required=False, help='Server port number')
    args = parser.parse_args()
    server = IOServer()

    async def on_shutdown(app):
        print('{} >>>>> Server shutdown <<<<<'.format(datetime.now()))
        for sid in server.sockets:
            await server.send(server.EVENT_SERVER_SHUTDOWN, {})
            # await server.sio.disconnect(sid)
        print('{} >>>>> Shutting down db <<<<<'.format(datetime.now()))
        server.db.shutdown()
    server.app.on_shutdown.append(on_shutdown)

    if args.port:
        server.serve(port=args.port)
    else:
        server.serve()
