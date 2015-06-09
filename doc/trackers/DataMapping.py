from CGATReport.Tracker import Tracker
from collections import OrderedDict as odict
from random import randint
import pandas


class ReturnValue(Tracker):
    tracks = ("track1", "track2", "track3")

    def __call__(self, track):
        return randint(0, 100)


class ReturnValueWithSlice(Tracker):
    tracks = ("track1", "track2", "track3")
    slices = ("slice1", "slice2")

    def __call__(self, track, slice):
        return randint(0, 100)


class ReturnValueInDictionary(Tracker):
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice):

        if slice == "slice1":
            return odict((("column1", randint(0, 100)),
                          ("column2", randint(0, 100)),))
        elif slice == "slice2":
            return odict((("column1", randint(0, 100)),
                          ("column2", randint(0, 100)),
                          ("column3", randint(0, 100)),))

class ReturnArray(Tracker):
    tracks = ("track1", "track2", "track3")

    def __call__(self, track):
        return [randint(0, 20) for x in range(10)]


class ReturnVariableLengthArray(Tracker):
    tracks = ("track1", "track2", "track3")

    def __call__(self, track):
        lengths = {'track1': 10,
                   'track2': 12,
                   'track3': 14}
        return [randint(0, 20) for x in range(lengths[track])]


class ReturnArrayWithSlice(Tracker):
    tracks = ("track1", "track2", "track3")
    slices = ("slice1", "slice2")

    def __call__(self, track, slice=None):
        return [randint(0, 20) for x in range(10)]


class ReturnArrayWithSliceAsDataframe(Tracker):
    tracks = ("track1", "track2", "track3")
    slices = ("slice1", "slice2")

    def __call__(self, track, slice=None):
        return pandas.DataFrame({'value': [randint(0, 20) for x in range(10)]})


class ReturnVariableLengthArrayWithSlice(Tracker):
    tracks = ("track1", "track2", "track3")
    slices = ("slice1", "slice2")

    def __call__(self, track, slice=None):
        lengths = {'track1': 10,
                   'track2': 12,
                   'track3': 14}
        return [randint(0, 20) for x in range(lengths[track])]


class ReturnDataFrameSimple(Tracker):
    tracks = ("track1", "track2", "track3")

    def __call__(self, track):
        return pandas.DataFrame(
            [randint(0, 20) for x in range(20)])


class ReturnDataFrameWithColumnLabel(Tracker):
    tracks = ("track1", "track2", "track3")

    def __call__(self, track):
        return pandas.DataFrame(
            {'column1': [randint(0, 20) for x in range(20)],
             'column2': [randint(0, 20) for x in range(20)]})


class ReturnDataFrameWithColumnLabels(Tracker):
    tracks = ("track1", "track2", "track3")

    def __call__(self, track):
        return pandas.DataFrame(
            [randint(0, 20) for x in range(20)],
            columns=[track])


class ReturnDataFrameWithIndex(Tracker):
    tracks = ("track1", "track2", "track3")

    def __call__(self, track):
        return pandas.DataFrame(
            [randint(0, 20) for x in range(20)],
            index=['index_%s' % track for x in range(20)])
