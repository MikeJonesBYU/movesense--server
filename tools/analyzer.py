#!/usr/bin/env python3

import pickle
import pandas as pd
import numpy as np
from random import randint
from sklearn.ensemble import RandomForestClassifier

from tools.errors import AnalyzerError

JUMP_TYPES = [
    "none", "axel", "toe", "flip", "lutz", "loop", "sal", "half-loop", "waltz"]


class Analyzer:
    """
    A wrapper class for the pickled classifier trained by 
    the supercomputer.

    ...

    Attributes
    ----------
    BOOL_PARAMS_FILE : str
        File path to a text file containing the parameters for the bool
        preprocessing/classifier
    TYPE_PARAMS_FILE : str
        File path to a text file containing the parameters for the type
        preprocessing/classifier
    bool_clf : boolean classifier
        analyzes data for the occurrence of an event
    type_clf : type classifier 
        analyzes data for the type of an event
    window_size : int
        # rows to be sent to classifiers
    sample_interval : int
        # rows to wait before starting next analysis

    Methods
    -------
    load_bool(clf_file:str)
        Loads boolean classifier from pickle path. Resets window.
    load_type(clf_file:str)
        Loads type classifier from pickle path. Resets window.
    bool_can_analyze(reading_count:int)
        Checks current reading count against bool window size/interval to
        determine if new analysis is possible.
    bool_can_analyze(reading_count:int)
        Checks current reading count against type window size/interval to
        determine if new analysis is possible.
    preprocess_bool(readings:list[Reading])
        Formats a list of Readings into useable state for bool classifier.
    preprocess_type(readings:list[Reading])
        Formats a list of Readings into useable state for type classifier.
    is_event(readings:list[Reading])
        Runs bool preprocessor/classifier on Reading window.
        True if an event is found.
    predict_event_type(readings:list[Reading])
        Runs type preprocessor/classifier on Reading window.
        Returns an event type name.
    """

    BOOL_PARAMS_FILE = 'analyzer/skater/jump_count_params.txt'
    TYPE_PARAMS_FILE = 'analyzer/skater/jump_type_params.txt'

    AGGREGATE_AVERAGE = 'average'
    AGGREGATE_MAX = 'max'
    AGGREGATE_MIN = 'min'


    def __init__(self, pickled_bool_clf=None, pickled_type_clf=None,
                 bool_window_size=150, bool_sample_interval=75,
                 type_window_size=100, type_sample_interval=5):
        """
        Parameters
        ----------
        pickled_bool_clf : str, optional
            path to pickled boolean classifier file
        pickled_type_clf : str, optional
            path to pickled type classifier file
        bool_window_size : int, optional
            Window size for the bool classifier
        bool_sample_interval int, optional
            Interval size for the bool classifier, # of new entries between
            each prediction
        type_window_size : int, optional
            Window size for the type classifier
        type_sample_interval : int, optional
            Interval size for readings to be aggregated together for type
            classifier's predictions
        """

        self.bool_clf = None
        self.type_clf = None
        self.bool_window_size = bool_window_size
        self.bool_interval = bool_sample_interval
        self.type_window_size = type_window_size
        self.type_interval = type_sample_interval
        type_params = self.get_params(self.TYPE_PARAMS_FILE)
        self.type_agg_method = type_params[-1]
        if pickled_bool_clf is not None:
            self.load_bool(pickled_bool_clf)
        if pickled_type_clf is not None:
            self.load_type(pickled_type_clf)

    def get_params(self, file):
        with open(file, 'r') as f:
            contents = f.read()

        return contents.split()

    def load_bool(self, clf_file):
        """
        Parameters
        ----------
        clf_file : str
            path to pickled boolean classifier
        """

        with open(clf_file, 'rb') as f:
            self.bool_clf = pickle.load(f)
            f.close()
    
    def load_type(self, clf_file):
        """
        Parameters
        ----------
        clf_file : str
            path to pickled type classifier
        """

        with open(clf_file, 'rb') as f:
            self.type_clf = pickle.load(f)
            f.close()

    def bool_can_analyze(self, reading_count):
        """
        Checks to see if the number of readings warrants another
        bool classifier prediction

        Parameters
        ----------
        reading_count : int
            # readings in session
        """

        return reading_count >= self.bool_window_size and \
            reading_count % self.bool_interval == 0

    def type_can_analyze(self, reading_count):
        """
        Checks to see if the number of readings warrants another
        type classifier prediction

        Parameters
        ----------
        reading_count : int
            # readings in session
        """

        return reading_count >= self.type_window_size

    def preprocess_bool(self, readings):
        """
        Formats a list of readings into a dataframe useable by the
        bool classifier.

        All readings in a window are collapsed into a 1-row dataframe
        (Shown here in multiple lines for readability)

        Data frame format
        --------------------------------------------
        Accelerometer-X-0      |Accelerometer-Y-0      |Accelerometer-Z-0      |
        Gyroscope-X-0          |Gyroscope-Y-0          |Gyroscope-Z-0          |
        Magnetometer-X-0       |Magnetometer-Y-0       |Magnetometer-Z-0       |
        ...
        Accelerometer-X-(size) |Accelerometer-Y-(size) |Accelerometer-Z-(size) |
        Gyroscope-X-(size)     |Gyroscope-Y-(size)     |Gyroscope-Z-(size)     |
        Magnetometer-X-(size)  |Magnetometer-Y-(size)  |Magnetometer-Z-(size)

        Parameters
        ----------
        readings : list[Reading]
            List of Readings to be formatted
        """

        data = []
        header = []
        count = 0
        for reading in readings:
            header.extend([
                f'Accelerometer-X-{count}', f'Accelerometer-Y-{count}', f'Accelerometer-Z-{count}',
                f'Gyroscope-X-{count}', f'Gyroscope-Y-{count}', f'Gyroscope-Z-{count}',
                f'Magnetometer-X-{count}', f'Magnetometer-Y-{count}', f'Magnetometer-Z-{count}'])
            values = [
                reading.accelerometer.x,
                reading.accelerometer.y,
                reading.accelerometer.z,
                reading.gyroscope.x,
                reading.gyroscope.y,
                reading.gyroscope.z,
                reading.magnetometer.x,
                reading.magnetometer.y,
                reading.magnetometer.z
            ]
            data.extend(values)
            count += 1
        return pd.DataFrame([data], columns=header)

    def preprocess_type(self, readings):
        """
        Formats a list of readings into a dataframe useable by the
        type classifier.

        All readings in a window are collapsed into a 1-row dataframe
        (Shown here in multiple lines for readability)

        Data frame format
        --------------------------------------------

        Accelerometer-X                   |Accelerometer-Y                   |Accelerometer-Z                   |
        Gyroscope-X                       |Gyroscope-Y                       |Gyroscope-Z                       |
        Magnetometer-X                    |Magnetometer-Y                    |Magnetometer-Z                    |
        Accelerometer-X-past-[interval]   |Accelerometer-Y-past-[interval]   |Accelerometer-Z-past-[interval]   |
        Gyroscope-X-past-[interval]       |Gyroscope-Y-past-[interval]       |Gyroscope-Z-past-[interval]       |
        Magnetometer-X-past-[interval]    |Magnetometer-Y-past-[interval]    |Magnetometer-Z-past-[interval]    |
        ...
        Accelerometer-X-future-[interval] |Accelerometer-Y-future-[interval] |Accelerometer-Z-future-[interval] |
        Gyroscope-X-future-[interval]     |Gyroscope-Y-future-[interval]     |Gyroscope-Z-future-[interval]     |
        Magnetometer-X-future-[interval]  |Magnetometer-Y-future-[interval]  |Magnetometer-Z-future-[interval]


        Parameters
        ----------
        readings : list[Reading]
            List of Readings to be formatted
        """

        header = ['Accelerometer-X', 'Accelerometer-Y', 'Accelerometer-Z',
                  'Gyroscope-X', 'Gyroscope-Y', 'Gyroscope-Z',
                  'Magnetometer-X', 'Magnetometer-Y', 'Magnetometer-Z']
        # Insert past half of aggregated headers, working backwords
        # E.g. Accelerometer-X|Y|Z-past-5, 10, 15...
        # Followed by future half of aggregated headers, working forwards
        half = len(readings)//2
        past = []
        future = []
        for i in range(1, half, self.type_interval):
            past.extend([
                f'Accelerometer-X-past-{i}',
                f'Accelerometer-Y-past-{i}',
                f'Acceleromter-Z-past-{i}',
                f'Gyroscope-X-past-{i}',
                f'Gyroscope-Y-past-{i}',
                f'Gyroscope-Z-past-{i}',
                f'Magnetometer-X-past-{i}',
                f'Magnetometer-Y-past-{i}',
                f'Magnetometer-Z-past-{i}'])
            future.extend([
                f'Accelerometer-X-future-{i}',
                f'Accelerometer-Y-future-{i}',
                f'Acceleromter-Z-future-{i}',
                f'Gyroscope-X-future-{i}',
                f'Gyroscope-Y-future-{i}',
                f'Gyroscope-Z-future-{i}',
                f'Magnetometer-X-future-{i}',
                f'Magnetometer-Y-future-{i}',
                f'Magnetometer-Z-future-{i}'])
        header.extend(past)
        header.extend(future)

        # Reorganize list to make it easier to work with
        # Resulting list order: [middle reading, middle->start, middle->end]
        reorganized = [readings[half-1]]
        reorganized.extend(readings[:half][::-1])
        reorganized.extend(readings[half:])

        data = [
            reorganized[0].accelerometer.x,
            reorganized[0].accelerometer.y,
            reorganized[0].accelerometer.z,
            reorganized[0].gyroscope.x,
            reorganized[0].gyroscope.y,
            reorganized[0].gyroscope.z,
            reorganized[0].magnetometer.x,
            reorganized[0].magnetometer.y,
            reorganized[0].magnetometer.z
        ]
        # Step through, aggregating reading intervals after first
        for i in range(1, len(reorganized), self.type_interval):
            agg = self.aggregate_readings(reorganized[i:i+self.type_interval])
            data.extend([
                agg['accelerometer']['x'],
                agg['accelerometer']['y'],
                agg['accelerometer']['z'],
                agg['gyroscope']['x'],
                agg['gyroscope']['y'],
                agg['gyroscope']['z'],
                agg['magnetometer']['x'],
                agg['magnetometer']['y'],
                agg['magnetometer']['z']
            ])


        return pd.DataFrame([data], columns=header)

    def aggregate_readings(self, readings):
        """
        Aggregates readings based on the method specified.
        Methods include mean, max, or min values. 
        """

        data = []
        for reading in readings:
            data.append([
                reading.accelerometer.x,
                reading.accelerometer.y,
                reading.accelerometer.z,
                reading.gyroscope.x,
                reading.gyroscope.y,
                reading.gyroscope.z,
                reading.magnetometer.x,
                reading.magnetometer.y,
                reading.magnetometer.z
            ])

        if self.type_agg_method == self.AGGREGATE_MAX:
            aggregated = np.max(data, axis=0)
        elif self.type_agg_method == self.AGGREGATE_MIN:
            aggregated = np.min(data, axis=0)
        else:
            aggregated = np.mean(data, axis=0)
        
        return {
            'accelerometer': {
                'x': aggregated[0],
                'y': aggregated[1],
                'z': aggregated[2]
            },
            'gyroscope': {
                'x': aggregated[3],
                'y': aggregated[4],
                'z': aggregated[5]
            },
            'magnetometer': {
                'x': aggregated[6],
                'y': aggregated[7],
                'z': aggregated[8]
            }
        }

    async def is_event(self, readings):
        """
        Runs boolean classifier on readings to look for an event occurrence
        If no boolean classifier is in use, randomly guess whether an event occurred
        
        Parameters
        ----------
        readings : list[Reading]
            List of Readings in the window to be analyzed
        """

        preprocessed = self.preprocess_bool(readings)

        if self.bool_clf is None:
            print('Still running fake classifier...')
            # TODO: Use real analyzer
            # Placeholder analysis that randomly selects an event or not
            idx = randint(0, 9) % 3
            return idx == 0

            # raise AnalyzerError(
            #     'Event bool classifier not setup, unable to analyze data')

        predictions = self.bool_clf.predict(preprocessed)
        for prediction in predictions:
            if prediction > 0:
                return True

        return False
    
    async def predict_event_type(self, readings):
        """
        Run type classifier on readings to look for an event occurrence
        If no type classifier is in use, always guess event type was Lutz
        
        Parameters
        ----------
        readings : list[Reading]
            List of Readings in the window to be analyzed
        """

        if self.type_clf is None:
             # TODO: Use real analyzer
            # Placeholder analysis that always returns a Lutz jump
            return 'Lutz'

            # raise AnalyzerError(
            #     'Event type classifier is not setup, unable to analyze data')
        preprocessed = self.preprocess_type(readings)
        prediction = self.type_clf.predict(preprocessed)
        return JUMP_TYPES[int(prediction[0])]
        

    def __str__(self):
        return '<Analyzer bool_clf={}, type_clf={}>'.format(
            self.bool_clf, self.type_clf)
