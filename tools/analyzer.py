#!/usr/bin/env python3

import pickle
import pandas as pd
from random import randint
from sklearn.ensemble import RandomForestClassifier

from tools.errors import AnalyzerError

from analyzer.skater.gather_data import gather_data
from analyzer.skater.modeling import impute_nans, drop_uneeded_targets
from analyzer.skater.utils import parse_args


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
    window_rate : int
        # rows to wait before starting next analysis

    Methods
    -------
    load_bool(clf_file:str)
        Loads boolean classifier from pickle path. Resets window.
    load_type(clf_file:str)
        Loads type classifier from pickle path. Resets window.
    can_analyze(reading_count:int)
        Checks current reading count against window size/overlap to determine
        if new analysis is possible.
    format_readings(readings:list[Reading])
        Formats a list of Readings into useable state for preprocessing & classifier.
    is_event(readings:list[Reading])
        Runs bool preprocessor/classifier on Reading window.
        True if an event is found.
    predict_event_type(readings:list[Reading])
        Runs type preprocessor/classifier on Reading window.
        Returns an event type name.
    """

    BOOL_PARAMS_FILE = 'analyzer/skater/jump_count_params.txt'
    TYPE_PARAMS_FILE = 'analyzer/skater/jump_type_params.txt'

    def __init__(self, window_size=150, window_rate=75,
                 pickled_bool_clf=None, pickled_type_clf=None):
        """
        Parameters
        ----------
        bool_args : list[str]
            Arguments used by bool preprocessor
        window_size : int, optional
            Default window_size for the analyzer, size of analysis
        window_rate int, optional
            Default for the analyzer, # of entries to receive between each analysis
        pickled_bool_clf : str, optional
            path to pickled boolean classifier file
        pickled_type_clf : str, optional
            path to pickled type classifier file
        """

        self.bool_args = self.set_args(self.BOOL_PARAMS_FILE)
        self.type_args = self.set_args(self.TYPE_PARAMS_FILE)
        self.type_args = []
        self.bool_clf = None
        self.type_clf = None
        self.window_size = window_size
        self.window_rate = window_rate
        if pickled_bool_clf is not None:
            self.load_bool(pickled_bool_clf)
        if pickled_type_clf is not None:
            self.load_type(pickled_type_clf)

    def set_args(self, args_file):
        with open(args_file, 'r') as f:
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

    def can_analyze(self, reading_count):
        """
        Checks to see if the number of readings warrants another analysis

        Parameters
        ----------
        reading_count : int
            # readings in session
        """

        return reading_count >= self.window_size and \
            reading_count % self.window_rate == 0

    def format_readings(self, readings, sensor):
        """
        Formats a list of readings into a dataframe useable by the
        preprocessor/classifier.

        All readings in a window are collapsed into a 1-row dataframe

        Data frame format (top row is column names)
        --------------------------------------------
        |         |Accelerometer-X-0 |Accelerometer-Y-0 |Accelerometer-Z-0 |Gyroscope-X-0 |Gyroscope-Y-0 |Gyroscope-Z-0 |Magnetometer-X-0 |Magnetometer-Y-0 |Magnetometer-Z-0 |...|Magnetometer-Z-<window_size-1>|
        |15565019 |-10.249899        |-0.762756         |-0.729192         |0.307034      |-0.561372     |-0.006084     |45.630714        |1.902777         |-16.7538         |...|-0.729192                     |
        
        

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

    async def is_event(self, readings, sensor):
        """
        Runs boolean classifier on readings to look for an event occurrence
        If no boolean classifier is in use, randomly guess whether an event occurred
        
        Parameters
        ----------
        readings : list[Reading]
            List of Readings in the window to be analyzed
        """

        preprocessed = self.format_readings(readings, sensor)

        if self.bool_clf is None or len(self.bool_args) == 0:
            print('Still running fake classifier...')
            print('bool_clf is None: {}'.format(self.bool_clf is None))
            print('len(bool_args) == 0:'.format(len(self.bool_args) == 0))
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
    
    async def predict_event_type(self, readings, sensor):
        """
        Run type classifier on readings to look for an event occurrence
        If no type classifier is in use, always guess event type was Lutz
        
        Parameters
        ----------
        readings : list[Reading]
            List of Readings in the window to be analyzed
        """

        formatted = self.format_readings(readings, sensor)

        if self.type_clf is None or len(self.type_args) == 0:
             # TODO: Use real analyzer
            # Placeholder analysis that always returns a Lutz jump
            return 'Lutz'

            # raise AnalyzerError(
            #     'Event type classifier is not setup, unable to analyze data')
        preprocessed = self.preprocess_window(self.type_args, formatted)
        return self.type_clf.predict(preprocessed)

    def __str__(self):
        return '<Analyzer bool_clf={}, type_clf={}>'.format(
            self.bool_clf, self.type_clf)
