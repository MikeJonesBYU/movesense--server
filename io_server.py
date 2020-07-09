#!/usr/bin/env python3

from aiohttp import web
import asyncio
from argparse import ArgumentParser
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
    EVENT_FOUND               = 'event_found'
    EVENT_DATA                = 'event_data'
    SERVER_DATA               = 'server_data'
    ANALYZED_DATA             = 'analyzed_data'
    REQUEST_RESPONSE          = 'request_response'


    def __init__(self, bool_clf_dir=BOOL_CLF_DIR, type_clf_dir=TYPE_CLF_DIR):
        self.sio = socketio.AsyncServer()
        self.app = web.Application()
        self.sio.attach(self.app)

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

    def get_requested_data(self, data):
        data_type = data.get(DATA_TYPE, None)
        if data_type is None:
            return {}

    def init_socketio(self):
        @self.sio.on(self.CONNECT)
        def connect(sid, environ):
            print('IO::{}::ID={}'.format(self.CONNECT, sid))

        @self.sio.on(self.CONNECT_ERROR)
        def connect_error(sid, data):
            print('IO::{}::ID={}, data={}'.format(self.CONNECT_ERROR, sid, data))
        
        @self.sio.on(self.CLIENT_DATA)
        async def receive_client_data(sid, data):
            print('IO::{}::ID={}, data={}'.format(self.CLIENT_DATA, sid, data))
            await self.send(self.SERVER_DATA, {'msg': 'Message received!'})

        @self.sio.on(self.START_SESSION)
        def start_session(sid, data):
            print('IO::{}::ID={}, data={}'.format(self.START_SESSION, sid, data))
            self.db.start_session(data[ID], data[ATHLETE_ID], data[SPORT],
                                  data[START_TIME],
                                  placements=data[SENSOR_PLACEMENTS])

        @self.sio.on(self.READING_ENTRY)
        async def receive_reading(sid, data):
            #print('IO::{}::ID={}, data={}'.format(self.READING_ENTRY, sid, data))
            # Unpack for db
            self.db.add_reading(
                data[SESSION_ID], data[SENSOR_ID], uuid.uuid4(),
                data[TIME], data[ACCELEROMETER],
                data[GYROSCOPE], data[MAGNETOMETER])

            reading_count = self.db.get_reading_count(data[SESSION_ID])
            if self.analyzer.bool_can_analyze(reading_count):
                start = -1*self.analyzer.bool_window_size # Only analyze latest window
                readings = self.db.get_readings(data[SESSION_ID])[start:]

                ## TODO: What do events look like coming out of the analyzer?
                ## TODO: Map sensor serial IDs to readings
                found_event = await self.analyzer.is_event(readings)
                print('found event analysis: {}'.format(found_event))

                if found_event and self.analyzer.type_can_analyze(reading_count):
                    start = -1*self.analyzer.type_window_size # Only analyze latest window
                    readings = self.db.get_readings(data[SESSION_ID])[start:]
                    athlete = self.db.get_session(data[SESSION_ID]).athlete

                    ## TODO: What do events look like coming out of the analyzer?
                    ## TODO: Map sensor serial IDs to readings
                    event_type = await self.analyzer.predict_event_type(
                        readings)
                    ## TODO: Send back notification that we found an event
                    print('IO::{}::FOUND_EVENT'.format(self.READING_ENTRY))
                    event_id = uuid.uuid4()
                    await self.send(self.EVENT_FOUND, {
                        EVENT_ID: str(event_id),
                        SESSION_ID: data[SESSION_ID],
                        ATHLETE_ID: str(athlete),
                        START_TIME: readings[0].timestamp,
                        END_TIME: readings[-1].timestamp
                    })
                    print('IO::{}::SEND_EVENT={}'.format(
                        self.READING_ENTRY, event_type))
                    event = self.db.add_event(
                        event_id, data[SESSION_ID], event_type,
                        readings[0].timestamp, readings[-1].timestamp)

                    ## TODO: Send back notification with the event type
                    await self.send(self.EVENT_DATA, event.dictionary())

        @self.sio.on(self.END_SESSION)
        def end_session(sid, data):
            print('IO::{}::ID={}, data={}'.format(self.END_SESSION, sid, data))
            self.db.end_session(data[ID], data[END_TIME])

        @self.sio.on(self.CLIENT_REQUEST)
        async def handle_request(sid, data):
            print('IO::{}::ID={}, data={}'.format(self.CLIENT_REQUEST, sid, data))
            response = self.get_requested_data(data)
            await self.send(self.REQUEST_RESPONSE, response)

        @self.sio.on(self.DISCONNECT)
        def diconnect(sid):
            print('IO::{}::ID={}'.format(self.DISCONNECT, sid))

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
