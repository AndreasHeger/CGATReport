'''This document contains a number of sample trackers.'''

import os
import random
import glob

import numpy

from CGATReport.Tracker import Tracker, Status
from collections import OrderedDict as odict


def BarData(): return dict([("bar1", 20), ("bar2", 10)])


class LabeledDataExample(Tracker):
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        if slice == "slice1":
            return odict((("column1", 10),
                          ("column2", 20),))
        elif slice == "slice2":
            return odict((("column1", 20),
                          ("column2", 10),
                          ("column3", 5),))


class LabeledDataLargeExample(Tracker):
    slices = ("slice1", "slice2")
    tracks = ["track%i" % x for x in range(0, 100)]

    def __call__(self, track, slice=None):
        if slice == "slice1":
            return odict((("column1", 10),
                          ("column2", 20),))
        elif slice == "slice2":
            return odict((("column1", 20),
                          ("column2", 10),
                          ("column3", 5),))


class LabeledDataWithErrorsExample(Tracker):
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        if slice == "slice1":
            return odict((
                ("column1", odict((('data', 20),
                                   ('error', 1),
                                   ))),
                ("column2", odict((('data', 10),
                                   ('error', 2),
                                   ))),
            ))
        elif slice == "slice2":
            return odict((
                ("column1", odict((('data', 20),
                                   ('error', 3),
                                   ))),
                ("column2", odict((('data', 10),
                                   ('error', 4)))),
                ("column3", odict((('data', 30),
                                   ('error', 5)))),
            ))


class LabeledDataWithErrorsAndLabelsExample(Tracker):
    '''use of ordered dictionary important as first
    element is treated as data.
    '''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        if slice == "slice1":
            return odict((
                ("column1", odict((('data', 20),
                                   ('error', 5),
                                   ('label', '**')))),
                ("column2", odict((('data', 10),
                                   ('error', 2),
                                   ('label', '*'))))
            ))
        elif slice == "slice2":
            return odict((
                ("column1", odict((('data', 20),
                                   ('error', 5),
                                   ('label', '***')))),
                ("column2", odict((('data', 10),
                                   ('error', 1)))),
                ("column3", odict((('data', 30),
                                   ('error', 4)))),
            ))


class SingleColumnDataExample(Tracker):
    '''return a single column of data.'''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        s = [random.randint(0, 20) for x in range(40)]
        random.shuffle(s)
        return odict((("data", s),))


class ArrayDataExample(Tracker):
    '''return two arrays of data.'''

    slices = ["slice%i" % x for x in range(0, 2)]
    tracks = ["track%i" % x for x in range(0, 3)]

    def __call__(self, track, slice=None):

        scale = (3 - int(track[-1]))

        data = odict((("x", list(range(0, 50))),
                      ("y", [x * scale for x in range(0, 50)])))

        return data


class SingleColumnDataLargeExample(Tracker):
    '''return a single column of data.'''
    slices = ("slice1", "slice2")
    tracks = ["track%i" % x for x in range(0, 20)]

    def __call__(self, track, slice=None):
        s = [random.randint(0, 20) for x in range(40)]
        random.shuffle(s)
        return odict((("data", s),))


class SingleColumnDataWithErrorExample(Tracker):
    '''return a single column of data.'''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        s = [random.randint(0, 20) for x in range(40)]
        e = [random.randint(0, 3) for x in range(40)]
        random.shuffle(s)
        return odict((("data", s),
                      ("error", e)))


class SingleColumnDataExampleWithoutSlices(Tracker):
    '''return a single column of data.'''
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        s = [random.randint(0, 20) for x in range(40)]
        random.shuffle(s)
        return odict((("data", s),))


class MultipleColumnDataExample(Tracker):
    '''multiple columns each with a column with data.'''
    mColumns = ["col1", "col2", "col3"]
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2")

    def __call__(self, track, slice=None):
        data = []
        if slice == "slice1":
            for x in range(len(self.mColumns) - 1):
                data.append([y + random.gauss(0, 0.2) for y in range(20)])
        elif slice == "slice2":
            for x in range(len(self.mColumns)):
                data.append([y + random.gauss(0, 0.5) for y in range(20)])
        return odict(list(zip(self.mColumns, data)))


class MultipleColumnDataFullExample(Tracker):
    '''multiple columns each with a column with data.'''
    mColumns = ["col1", "col2", "col3"]
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2")

    def __call__(self, track, slice=None):
        data = []
        if slice == "slice1":
            for x in range(len(self.mColumns)):
                data.append([y + random.gauss(0, 0.2) for y in range(20)])
        elif slice == "slice2":
            for x in range(len(self.mColumns)):
                data.append([y + random.gauss(0, 0.5) for y in range(20)])
        return odict(list(zip(self.mColumns, data)))


class ErrorInTracker1(Tracker):
    '''A tracker that creates an error - exception while collecting data.'''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2")

    def __call__(self, track, slice=None):
        raise ValueError("testing: could not collect data")


class ErrorInTracker2(Tracker):
    '''A tracker that creates an error - problems while returning tracks.'''
    slices = ("slice1", "slice2")

    def getTracks(self):
        raise ValueError("testing: could not build tracks")

    def __call__(self, track, slice=None):
        return odict((("data", list(range(0, 10))),))


class ErrorInTracker3(Tracker):
    '''A tracker that creates an error - no data.'''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2")

    def __call__(self, track, slice=None):
        return None


class EmptyTracker(Tracker):
    '''A tracker that creates a warning.'''
    slices = ("slice1", "slice2")
    tracks = []

    def __call__(self, track, slice=None):
        return None


class LabeledDataTest(Tracker):
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        if slice == "slice1":
            return odict((("column1", 10),
                          ("column2", 20),))
        elif slice == "slice2":
            return odict((("column1", 20),
                          ("column2", 10),
                          ("column3", 5),))


class StatusTracker(Status):
    tracks = ("track1", "track2", "track3")

    def testTest1(self, track):
        '''test1 passes'''
        return "PASS", 0.5

    def testTest2(self, track):
        '''test2 fails - 
        A large test.'''
        return "FAIL", 2

    def testTest3(self, track):
        '''test3 gives a warning'''
        return "WARN", "a string"

    def testTest4(self, track):
        '''test4 is not available/applicable'''
        return "NA", None


class MatrixTracker(Tracker):
    '''returns matrices.'''

    tracks = 'example1', 'example2'

    def __call__(self, track):

        if track == 'example1':
            matrix = numpy.arange(0, 10)
        elif track == 'example2':
            matrix = numpy.arange(10, 0, -1)

        matrix.shape = (2, 5)

        r = {'rows': list(map(str, list(range(0, 2)))),
             'columns': list(map(str, list(range(0, 5)))),
             'matrix': matrix}

        return r


def getSingleValue(): return 12

IMAGEDIR = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "..", "images")


class DataWithImagesExample(Tracker):
    tracks = ("all",)

    def __call__(self, track):

        images = glob.glob(os.path.join(IMAGEDIR, "*.png"))

        data = odict()
        data["numbers"] = list(range(len(images)))
        data["images"] = [".. image:: %s" % x for x in images]

        return data


class VennTracker(Tracker):

    tracks = ('two-circle', 'three-circle')

    def __call__(self, track):

        if track == 'two-circle':
            return {'01': 10, '10': 20, '11': 5,
                    'labels': ("SetA", "SetB")}

        elif track == 'three-circle':
            return {'001': 10, '010': 20, '100': 5,
                    '011': 10, '110': 20, '101': 5,
                    '111': 10,
                    'labels': ("SetA", "SetB", "SetC")}
