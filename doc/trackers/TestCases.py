import random
from CGATReport.Tracker import Tracker
from collections import OrderedDict as odict


class LongLabelsSmall(Tracker):

    """example with long labels."""
    wordsize = 5
    numwords = 5
    slices = ("small", "large", "gigantic")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        if slice == "small":
            ncolumns = 10
        elif slice == "large":
            ncolumns = 40
        elif slice == "gigantic":
            ncolumns = 100

        if slice == "small":
            ncolumns = 2
        elif slice == "large":
            ncolumns = 2
        elif slice == "gigantic":
            ncolumns = 4

        data = []
        for x in range(0, ncolumns):
            label = "%s:%i %s" % (
                slice, x, " ".join(["a" * self.wordsize
                                    for y in range(self.numwords)]))
            data.append((label, random.randint(0, 100)))

        return odict(sorted(data))


class LargeMatrix(Tracker):

    """example of a large matrix with long labels."""
    wordsize = 5
    numwords = 5

    slices = ("small", "large")
    tracks = ["track%i" % i for i in range(5)]

    def __call__(self, track, slice=None):
        if slice == "small":
            ncolumns = 10
        elif slice == "large":
            ncolumns = 40

        data = []
        for x in range(0, ncolumns):
            # label = "%s:%i %s" % (slice, x, " ".join([ "a" * self.wordsize for y in range(self.numwords) ]))
            label = "%s" % (
                " ".join(["a" * self.wordsize for y in range(self.numwords)]))
            data.append((label, random.randint(0, 100)))
        return odict(data)


class LayoutTest(Tracker):

    """Layout testing."""
    nslices = 3
    nsamples = 100

    slices = ["slice%i" % i for i in range(3)]
    tracks = ["track%i" % i for i in range(5)]

    def __call__(self, track, slice=None):
        return odict((("data", [random.gauss(0, 1) for x in
                                range(self.nsamples)]),))


class SplittingTest(Tracker):

    '''return a single column of data.'''
    tracks = ["track%i" % x for x in range(0, 2)]
    slices = ["slice%i" % x for x in range(0, 10)]

    def __call__(self, track, slice=None):
        s = [random.randint(0, 20) for x in range(10)]
        random.shuffle(s)
        return odict((('x', list(range(len(s)))), ('y', s)))


class MultipleHistogramTest(Tracker):

    """Layout testing."""
    nslices = 3
    nsamples = 100

    slices = ["slice%i" % i for i in range(3)]
    tracks = ["track%i" % i for i in range(5)]

    def __call__(self, track, slice=None):
        return odict((("bin", "value-set1", "value-set2"),
                      (list(range(0, self.nsamples)),
                       [random.gauss(0, 1) for x in range(self.nsamples)],
                       [random.gauss(0, 1) for x in range(self.nsamples)])))


class MultiLevelTable(Tracker):

    ncols = 3
    mNumLevels = 3

    tracks = ["track%i" % i for i in range(5)]

    def __call__(self, track, slice=None):
        data = [
            ["value%i" % y for y in range(self.mNumLevels)]
            for z in range(self.ncols)]

        return odict(list(zip(["col%i" % x for x in range(self.ncols)], data)))


class LargeTable(Tracker):

    '''test case covering rendering large tables.'''

    ncols = 40
    nrows = 200

    tracks = ["track%i" % i for i in range(5)]

    def __call__(self, track, slice=None):

        data = ["value=%i" % random.randint(0, 100) for y in range(self.nrows)]
        return odict([("col%i" % x, data) for x in range(self.ncols)])


class VeryLargeMatrix(Tracker):

    """example of a large matrix with long labels."""

    # do not cache - slow in shelve as many key-value pairs
    cache = False

    ncols = 7000
    tracks = ["track%i" % i for i in range(200)]

    def __call__(self, track, slice=None):

        data = []
        for x in range(0, self.ncols):
            data.append(("col%i%s" % (x, "f" * 193), x))

        return odict(data)


class DeepTree(Tracker):

    '''example of a deeple nested data tree '''
    tracks = ("track1", "track2", "track3")
    nlevels = 8
    nslices = 2

    def __call__(self, track):

        root = odict()
        current = [root]

        for level in range(self.nlevels):
            new = []
            for x in current:
                for y in range(self.nslices):
                    o = odict()
                    x['slice%i' % y] = o
                    new.append(o)
            current = new

        for x in current:
            x['data'] = random.randint(0, 100)

        return root
