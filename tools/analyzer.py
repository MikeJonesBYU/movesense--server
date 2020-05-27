#!/usr/bin/env python3

import pickle
from sklearn.ensemble import RandomForestClassifier

from tools.errors import AnalyzerError


class Analyzer:
    def __init__(self, pickled_clf=None):
        self.latest_clf = pickled_clf
        if pickled_clf is not None:
            self.load(self.latest_clf)
        else:
            self.classifier = None

    def load(self, clf_file):
        with open(clf_file, 'rb') as f:
            self.classifier = pickle.load(f)
            f.close()

    def analyze(self, features):
        if self.classifier is None:
            raise AnalyzerError('Classifier not setup, unable to analyze data')

        return self.classifier.predict(features)

    def score(self, features, labels):
        if self.classifier is None:
            raise AnalyzerError('Classifier not setup, unable to score')

        return self.classifier.score(features, labels)

    def get_decision_path(self, features):
        if self.classifier is None:
            raise AnalyzerError('Classifier not setup, unable to get decision path')

        return self.classifier.decision_path(features)

    def save(self, filename=None):
        if self.classifier is not None:
            if filename is None and self.latest_clf is None:
                filename = 'clf.pkl'
            elif filename is None:
                filename = self.latest_clf
            with open(filename, 'wb') as f:
                pickle.dump(self.classifier, f)

    def __str__(self):
        return '<Analyzer classifier={}>'.format(self.classifier)
