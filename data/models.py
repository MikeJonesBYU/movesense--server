#!/usr/bin/env python3
import asyncio
import enum
import uuid

from sqlalchemy import (Table, Column, String, Integer, ForeignKey,
                        Float, Enum, BigInteger)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import exists
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from model_keys import *
from .types import UUID_ID

def is_uuid4(obj):
    try:
        uuid_obj = uuid.UUID(str(obj), version=4)
        return True
    except:
        return False

# Intermediate table to allow many-to-many for events & qualitative attributes
event_qual_association_table = Table(
    'event_qual_association', Base.metadata,
    Column('event_id', UUID_ID(), ForeignKey('event.id')),
    Column('qualitative_attribute_id', UUID_ID(),
           ForeignKey('qualitative_attribute.id')))


class Session(Base):
    class Sport(enum.Enum):
        SKATING = 0
        VOLLEYBALL = 1
        SWIMMING = 2
    
        def __str__(self):
            return '{}'.format(self.name).lower()

    """
    Class for periods with recorded sensor data on athletic performance.

    ...

    Attributes
    ----------
    id : uuid4
        unique identifier for the session. Generally created by the app.
    athlete : uuid4
        unique identifier for a given athlete. Generally created by the app.
    sport : str
        Name of the sport being analyzed in the session.
    start : int
        Unix timestamp of when the session began.
    end : int
        Unix timestamp of when the session ended.
    sensors : list[SensorPlacement]
        Sensors used in the session.
    events : list[Event]
        Events found by the analyzer in the session.

    Class Methods
    -------
    find_by_athlete(db:sqlalchemy.Session, athlete:uuid4)
        Helper function for finding Sessions with a given athlete
    get_session_sensors(db:sqlalchemy.Session, id:str)
        Helper function for getting a list of sensors used in a given session
    get_session_events(db:sqlalchemy.Session, id:str)
        Helper function for getting a list of events in a given session
    get_session_readings(db:sqlalchemy.Session, id:str)
        Helper function for getting a list of readings in a given session
    get_sensor_by_serial(serial:str)
        Helper function for getting a sensor with the specified serial from
        the session
    get_readings()
        Helper function that returns the list of readings in the session
    dictionary()
        Returns Session object in dictionary format 
    """
    __tablename__ = 'session'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    athlete = Column('athlete', UUID_ID(), nullable=False)
    sport = Column('sport', Enum(Sport))
    start = Column('start', Integer)
    end = Column('end', Integer)
    sensors = relationship('SensorPlacement')
    events = relationship('Event')

    @classmethod
    def find_by_athlete(cls, db, athlete):
        return db.query(cls).filter_by(athlete=athlete).all()

    @classmethod
    def get_session_sensors(cls, db, id):
        session = db.query(cls).filter_by(id=id).first()
        if session is not None:
            return session.sensorsto
    @classmethod
    def get_session_events(cls, db, id):
        session = db.query(cls).filter_by(id=id).first()
        if session is not None:
            return session.events
        return []

    @classmethod
    def get_session_readings(cls, db, id):
        session = db.query(cls).filter_by(id=id).first()
        if session is not None:
            return session.get_readings()
        return []

    def get_sport_display(self):
        return str(self.sport)

    def get_sensor_by_serial(self, serial):
        found = None
        for sensor in self.sensors:
            if sensor.sensor == serial:
                found = sensor
                break
        return found

    def get_readings(self):
        # Helper function for when the session isn't stored in the database
        ## TODO: If this list is spliced when multiple sensors are included,
        ##       it could drop some sensor readings.
        ##       Organize list by oldest -> latest readings.
        readings = []
        for sensor in self.sensors:
            readings.extend(sensor.readings)
        return readings

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            ATHLETE_ID: str(self.athlete),
            SPORT: self.sport.value,
            START_TIME: self.start,
            END_TIME: self.end,
            SENSOR_PLACEMENTS: [sensor.dictionary(db) for sensor in self.sensors],
            EVENTS: [event.dictionary(db) for event in self.events]
        }

    def __repr__(self):
        return "<Session(id='%s', athlete='%s, sport='%s', \
                start=%s, end=%s)>" % (
            self.id, self.athlete_id, self.sport, self.start, self.end)

    def __str__(self):
        return self.__repr__()


class Event(Base):
    __tablename__ = 'event'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    type = Column('type', String())
    session = Column('session', UUID_ID(), ForeignKey('session.id'))
    bool_classifier = Column('bool_classifier', String())
    type_classifier = Column('type_classifier', String())
    subevents = relationship('Subevent')
    qualitative_attributes = relationship(
        'QualitativeAttribute', secondary=event_qual_association_table)
    quantitative_attributes = relationship('QuantitativeAttribute')

    def get_start(self):
        start = float('inf')
        for sub in self.subevents:
            if sub.time < start:
                start = sub.time
        if start == float('inf'):
            start = 1
        return start

    def get_end(self):
        end = 0
        for sub in self.subevents:
            if sub.time > end:
                end = sub.time
        return end

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            TYPE: self.type,
            START_TIME: self.get_start(),
            END_TIME: self.get_end(),
            SESSION_ID: str(self.session),
            BOOL_CLASSIFIER: self.bool_classifier,
            TYPE_CLASSIFIER: self.type_classifier,
            SUBEVENTS: [
                subevent.dictionary(db) for subevent in self.subevents],
            QUALITATIVE_ATTRIBUTES: [
                quality.dictionary(db) for quality \
                in self.qualitative_attributes],
            QUANTITATIVE_ATTRIBUTES: [
                quantity.dictionary(db) for quantity \
                    in self.quantitative_attributes]
        }

    def __repr__(self):
        return "<Event(id='%s', session='%s', type='%s')>" % (
            self.id, self.session_id, self.type)

    def __str__(self):
        return self.__repr__()


class Subevent(Base):
    __tablename__ = 'subevent'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    event = Column('event', UUID_ID(), ForeignKey('event.id'))
    type = Column('type', String, nullable=False)
    time = Column('value', BigInteger)

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            EVENT_ID: str(self.event),
            TYPE: self.type,
            TIME: self.time
        }

    def __repr__(self):
        return "<Subevent(event_id='%s', type='%s', time=%s)>" % (
            self.event_id, self.type, self.time)

    def __str__(self):
        return self.__repr__()


class QualitativeAttribute(Base):
    __tablename__ = 'qualitative_attribute'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)

    events = relationship(
        'Event', secondary=event_qual_association_table,
        back_populates='qualitative_attributes')
    attribute = Column('attribute', String, nullable=False, unique=True)

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            ATTRIBUTE: self.attribute
        }

    def __repr__(self):
        return "<QualitativeAttribute(id='%s', attribute='%s')>" % (
            self.id, self.attribute)

    def __str__(self):
        return self.__repr__()


class QuantitativeAttribute(Base):
    __tablename__ = 'quantitative_attribute'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    event = Column('event', UUID_ID(), ForeignKey('event.id'))
    attribute = Column('attribute', String)
    units = Column('units', String)
    value = Column('value', Float)

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            EVENT_ID: str(self.event),
            ATTRIBUTE: self.attribute,
            UNITS: self.units,
            VALUE: self.value
        }

    def __repr__(self):
        return "<QuantitativeAttribute(event='%s', attribute='%s', \
                units='%s', value=%s)>" % (
                    self.event_id, self.attribute, self.units, self.value)

    def __str__(self):
        return self.__repr__()


class SensorPlacement(Base):
    class Location(enum.Enum):
        LEFT_WRIST = 0
        RIGHT_WRIST = 1
        SMALL_OF_BACK = 2
        LEFT_FOOT = 3
        RIGHT_FOOT = 4
        WAIST = 5

        def __str__(self):
            return '{}'.format(self.name).lower()

    __tablename__ = 'sensor_placement'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    sensor = Column('sensor', String)
    session = Column('session', UUID_ID(), ForeignKey('session.id'))
    location = Column('location', Enum(Location), nullable=False)
    readings = relationship('Reading')

    def get_location_display(self):
        return str(self.location)

    def get_reading_by_timestamp(self, timestamp):
        found = None
        for reading in self.readings:
            if reading.timestamp == timestamp:
                found = reading
                break
        return found

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            SENSOR_ID: self.sensor,
            SESSION_ID: str(self.session),
            LOCATION: self.location.value,
            READINGS: [reading.dictionary(db) for reading in self.readings]
        }

    def __repr__(self):
        return "<SensorPlacement(id='%s', session='%s', sensor='%s', \
                location='%s')>" % (
                    self.id, self.session, self.sensor, self.location)

    def __str__(self):
        return self.__repr__()


class Reading(Base):
    __tablename__ = 'reading'
    
    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    sensor = Column('sensor', UUID_ID(), ForeignKey('sensor_placement.id'))
    timestamp = Column('timestamp', BigInteger)
    accelerometer = relationship('AccelerometerReading', uselist=False,
                                 back_populates='reading')
    gyroscope = relationship('GyroscopeReading', uselist=False,
                             back_populates='reading')
    magnetometer = relationship('MagnetometerReading', uselist=False,
                                back_populates='reading')

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        placement = db.query(SensorPlacement).filter_by(id=self.sensor).one()
        return {
            ID: str(self.id),
            SENSOR_ID: placement.sensor,
            TIME: self.timestamp,
            ACCELEROMETER: self.accelerometer.dictionary(db),
            GYROSCOPE: self.gyroscope.dictionary(db),
            MAGNETOMETER: self.magnetometer.dictionary(db)
        }

    def __repr__(self):
        return "<Reading(id='%s', sensor='%s', time=%s)>" % (
            self.id, self.sensor, self.accelerometer)

    def __str__(self):
        return self.__repr__()


class AccelerometerReading(Base):
    UNITS = 'm/s^2'

    __tablename__ = 'accelerometer_reading'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    reading_id = Column('reading_id', UUID_ID(), ForeignKey('reading.id'))
    reading = relationship('Reading', back_populates='accelerometer')
    x = Column('x', Float)
    y = Column('y', Float)
    z = Column('z', Float)
    units = Column('units', String(length=10), default=UNITS)

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            READING_ID: str(self.reading_id),
            X: self.x,
            Y: self.y,
            Z: self.z,
            UNITS: self.units
        }

    def __repr__(self):
        return "<AccelerometerReading(reading='%s', x=%s, y=%s, z=%s, \
                units='%s')>" % (self.reading_id, self.x, self.y,
                                 self.z, self.units)
    
    def __str__(self):
        return self.__repr__()


class GyroscopeReading(Base):
    UNITS = 'deg/sec'

    __tablename__ = 'gyroscope_reading'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    reading_id = Column('reading_id', UUID_ID(), ForeignKey('reading.id'))
    reading = relationship('Reading', back_populates='gyroscope')
    x = Column('x', Float)
    y = Column('y', Float)
    z = Column('z', Float)
    units = Column('units', String(length=10), default=UNITS)

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            READING_ID: str(self.reading_id),
            X: self.x,
            Y: self.y,
            Z: self.z,
            UNITS: self.units
        }

    def __repr__(self):
        return "<GyroscopeReading(reading='%s', x=%s, y=%s, z=%s, \
                units='%s')>" % (self.reading_id, self.x, self.y,
                                 self.z, self.units)
    
    def __str__(self):
        return self.__repr__()


class MagnetometerReading(Base):
    UNITS = 'microtesla'

    __tablename__ = 'magnetometer_reading'

    id = Column('id', UUID_ID(), default=uuid.uuid4, nullable=False,
                unique=True, primary_key=True)
    reading_id = Column('reading_id', UUID_ID(), ForeignKey('reading.id'))
    reading = relationship('Reading', back_populates='magnetometer')
    x = Column('x', Float)
    y = Column('y', Float)
    z = Column('z', Float)
    units = Column('units', String(length=10), default=UNITS)

    def dictionary(self, db):
        """
        Returns dictionary of instance fields

        Parameters
        ----------
        db : sqlalchemy.Session
            Pass in sqlalchemy Session to lookup related fields
        """
        return {
            ID: str(self.id),
            READING_ID: str(self.reading_id),
            X: self.x,
            Y: self.y,
            Z: self.z,
            UNITS: self.units
        }

    def __repr__(self):
        return "<MagnetometerReading(reading='%s', x=%s, y=%s, z=%s, \
                units='%s')>" % (self.reading_id, self.x, self.y,
                                 self.z, self.units)
    
    def __str__(self):
        return self.__repr__()
