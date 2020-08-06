#!/usr/bin/env python3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as dbmaker
import urllib.parse
import uuid

from db_settings import (DB_DIALECT, DB_DRIVER, DB_HOST, DB_NAME, DB_PASS,
                         DB_PORT, DB_USER)
from data import models
from model_keys import *
from .analyzer import Analyzer


class DBManager:
    """
    Database class to handle DB connections, lookups, and updates.
    Also maintains recording session data.

    ...

    Attributes
    ----------
    db : sqlalchemy.Session
        Connection to database
    sessions : dict<str, Session>
        Sessions currently accepting sensor data.
    
    Methods
    -------
    _construct_engine_url(dialect:str, driver:str, host:str, name:str,
                          user:str, pw:str, port:int)
        Creates url for sqlalchemy engine to connect to database
    get_athlete_sessions(athlete:str)
        Returns a list of Sessions for the requested athlete
    get_session_readings(session_id:uuid)
        Returns a list of Readings for the requested Session
    save()
        Commits changes to the database
    save_session(session:Session)
        Updates Session in the database
    get_session(session_id:uuid)
        Returns the session requested for. If not found, returns None.
    start_session(id:uuid, athlete:str, sport:str, start:int,
                  placements:list[Sensor] optional)
        Initializes a session for recording.
        If SensorPlacements are already known, adds those to the Session.
    end_session(id:uuid, end:int)
        Saves the Session and removes it from dict of sessions currently
        being recorded.
    add_event(event_id:uuid, session_id:uuid, event_type:str,
              start:int, end:int)
        Adds the event to the session. If session is already over,
        immediately saves it to database.
    add_reading(session_id:uuid, sensor_id:str, reading_id:uuid,
                timestamp:int, accel_data:dict, gyro_data:dict, mag_data:dict)
        Adds a Reading to the session.
    get_reading_count(session_id:uuid)
        Returns # of Readings in the session
    get_readings(session_id:uuid)
        Returns the list of Readings in the session 
    """

    def __init__(self, dialect=DB_DIALECT, driver=DB_DRIVER, host=DB_HOST,
                 name=DB_NAME, user=DB_USER, pw=DB_PASS, port=DB_PORT):
        """
        Parameters (defaults defined by db_settings)
        --------------------------------------------
        dialect : str, optional
            Dialect for database (PostgreSQL, MySQL, SQLite, etc).
        driver : str, optional
            Driver for database (psycopg2 for PostgreSQL).
        host : str, optional
            Database host url
        name : str, optional
            Name of database
        user : str, optional
            User for database login
        pw : str, optional
            User password for database
        port : int, optional        
            Port database is listening on
        """

        url = self._construct_engine_url(dialect, driver, host, name,
                                         user, pw, port)
        engine = create_engine(url)
        models.Base.metadata.create_all(engine)
        DB = dbmaker(bind=engine)
        self.db = DB()
        
        # Map of athletic session currently recording
        self.sessions = {}

    def _construct_engine_url(self, dialect, driver, host, name,
                              user, pw, port):
        # Default settings if not specified
        if dialect == '':
            dialect = 'postgresql'
        if driver == '':
            driver = 'psycopg'
        if host == '':
            host = 'localhost'

        url = '{}+{}://{}:{}@{}'.format(dialect, driver, user,
                                        urllib.parse.quote_plus(pw),
                                        host)
        if not port == '':
            url += port
        
        return url + '/{}'.format(name)

    def get_athlete_sessions(self, athlete):
        return models.Session.find_by_athlete(self.db, athlete)

    def get_session_readings(self, session_id):
        if session_id in self.sessions.keys():
            return self.sessions[session_id].get_readings()
        return list(models.Session.get_readings(self.db, session_id))

    def get_all_sessions(self, athletes):
        sessions = []
        for athlete in athletes:
            sessions.extend(self.get_athlete_sessions(athlete))
        return sessions

    def save_session(self, id):
        session = self.sessions[id]
        self.db.add(session)
        for event in session.events:
            self.db.add(event)
            for subevent in event.subevents:
                self.db.add(subevent)
            for quality in event.qualitative_attributes:
                self.db.add(quality)
            for quantity in event.quantitative_attributes:
                self.db.add(quantity)
        for sensor in session.sensors:
            self.db.add(sensor)
            for reading in sensor.readings:
                self.db.add(reading)
                self.db.add(reading.accelerometer)
                self.db.add(reading.gyroscope)
                self.db.add(reading.magnetometer)
        self.save()

    def save(self):
        self.db.commit()

    def shutdown(self):
        self.sessions = {}
        self.db.close()

    def get_session(self, id):
        if id in self.sessions.keys():
            return self.sessions[id]
        return self.db.query(models.Session).filter_by(id=id).one()

    def start_session(self, id, athlete, sport, start, placements=[]):
        end = start + 24 * 60 * 60 # 24 hours from the start time; default for creation
        sensors = []
        for placement in placements:
            sensor = models.SensorPlacement(
                id=uuid.uuid4(),
                sensor=placement[SENSOR_ID], session=id,
                location=models.SensorPlacement.Location(int(placement[LOCATION])),
                readings=[])
            self.db.add(sensor)
            sensors.append(sensor)

        self.sessions[id] = models.Session(
            id=id, athlete=athlete, sport=models.Session.Sport(int(sport)),
            start=start, end=end, sensors=sensors)

    def end_session(self, id, end):
        if id in self.sessions.keys():
            self.sessions[id].end = end
            self.save_session(id)
            del self.sessions[id]

    def add_event(self, event_id, session_id, event_type, start, end,
                  bool_clf, type_clf):
        ## TODO: How are we getting qualitative attributes,
        ##       quantitative attributes, and subevents?
        qualities, quantities, subevents = [], [], []
        session_over = False

        if session_id not in self.sessions.keys():
            session_over = True
            # Session might be over before the classifier returned the event type
            session = self.db.query(models.Session).filter_by(id=session_id).one()
            if session is None:
                # Can't find the session, ignore request
                return
        else:
            session = self.sessions[session_id]
        
        event = models.Event(
            id=event_id, type=event_type, session=session_id,
            bool_classifier=bool_clf, type_classifier=type_clf,
            start=start, end=end, subevents=subevents,
            qualitative_attributes=qualities,
            quantitative_attributes=quantities)
        session.events.append(event)

        if session_over:
            self.db.add(event)
            self.db.add(session)
            self.save()
        
        return event

    def add_reading(self, session_id, sensor_id, reading_id, timestamp,
                    accel_data, gyro_data, mag_data):
        if session_id not in self.sessions.keys() or \
            self.sessions[session_id].get_sensor_by_serial(sensor_id) is None:
            return
        sensor = self.sessions[session_id].get_sensor_by_serial(sensor_id)
        if sensor.get_reading_by_timestamp(timestamp) is None:
            accel = models.AccelerometerReading(
                reading_id=reading_id,
                x=accel_data[X],
                y=accel_data[Y],
                z=accel_data[Z],
                units=accel_data[UNITS])
            self.db.add(accel)
            gyro = models.GyroscopeReading(
                reading_id=reading_id,
                x=gyro_data[X],
                y=gyro_data[Y],
                z=gyro_data[Z],
                units=gyro_data[UNITS])
            self.db.add(gyro)
            mag = models.MagnetometerReading(
                reading_id=reading_id,
                x=mag_data[X],
                y=mag_data[Y],
                z=mag_data[Z],
                units=mag_data[UNITS])

            reading = models.Reading(
                id=reading_id, sensor=sensor.id, timestamp=timestamp,
                accelerometer=accel, gyroscope=gyro, magnetometer=mag)
            self.db.add(reading)
            sensor.readings.append(reading)

    def get_reading_count(self, session_id):
        if session_id not in self.sessions.keys():
            return len(models.Session.get_session_readings(
                self.db, session_id))
        return len(self.sessions[session_id].get_readings())

    def get_readings(self, session_id):
        if session_id not in self.sessions.keys():
            return models.Session.get_session_readings(self.db, session_id)
        return self.sessions[session_id].get_readings()

    def __str__(self):
        return 'DBManager:\nengine: {}\ndb: {}'.format(self.engine, self.db)
