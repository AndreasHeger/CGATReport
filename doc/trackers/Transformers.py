'''Test cases for transformers.'''
from CGATReport.Tracker import *

import pandas


def TrackerFilter():
    return {'a': {'x': 1, 'y': 2},
            'b': {'x': 3, 'y': 4}}


def TrackerSelect():
    return {'a': {'x': 1, 'y': 2},
            'b': {'x': 3, 'y': 4}}


def TrackerToLabels():
    return {'a': odict((('keys', ['x', 'y', 'z']),
                        ('values', [1, 2, 3])))}


def TrackerToList():
    return odict((('a', {'x': 1,
                         'y': 2,
                         'z': 3}),
                  ('b', {'x': 4,
                         'y': 5,
                         'z': 6}),
                  ))


def TrackerToDataFrame():
    return {'experiment1': odict((('expression', [1, 2, 3]),
                                  ('counts', [3, 4, 5]))),
            'experiment2': odict((('expression', [8, 9, 10]),
                                  ('counts', [4, 5, 6])))}


def TrackerIndicator():
    return {}


def TrackerGroup():
    return odict((('a', {'x': ['id1', 'id2'],
                         'y': [2, 3],
                         'z': [3, 4]}),
                  ('b', {'x': ['id1', 'id2'],
                         'y': [2, 5],
                         'z': [1, 6]}),
                  ))


def TrackerCombinations():
    return odict((('a', {'x': 1}),
                  ('b', {'x': 2}),
                  ('c', {'x': 3})
                  ))


def TrackerStats():
    return [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def TrackerPairwise():
    return {'set1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'set2': [3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            'set3': [5, 6, 7, 8, 9, 10, 11, 12, 14, 15],
            }


def TrackerHistogram():
    return {'x': [1, 1, 1, 1, 1, 2, 2, 2, 4, 4, 5]}


def TrackerAggregate():
    return {
        'x': [1., 1.8, 2.6, 3.4, 4.2],
        'frequency': [5, 3, 0, 2, 1]}


def TrackerHistogramStats():
    return pandas.DataFrame.from_records(
        [(1, 2, 3, 0,),
         (2, 3, 4, 1),
         (3, 4, 2, 1),
         (4, 1, 1, 0)],
        columns=["bins", "A", "B", "C"])
