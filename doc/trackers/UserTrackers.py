import os
import random
import glob

from CGATReport.Tracker import Tracker
from collections import OrderedDict as odict
from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from CGATReport import Utils

from matplotlib import pyplot as plt

try:
    from rpy2.robjects import r as R
except ImportError:
    R = None


class MatplotlibData(Tracker):

    '''create plot using matplotlib.'''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice):
        s = [random.randint(0, 20) for x in range(40)]
        random.shuffle(s)

        # do the plotting
        fig = plt.figure()
        plt.plot(s)
        return {"text": "#$mpl %i$#" % fig.number}


class RPlotData(Tracker):

    '''create plot using R.'''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")

    def __call__(self, track, slice=None):
        if not R:
            return

        s = [random.randint(0, 20) for x in range(40)]
        random.shuffle(s)
        # do the plotting
        R.x11()
        R.plot(s, s)

        return {"text": "#$rpl %i$#" % R["dev.cur"]()[0]}


IMAGEDIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "images")


class Images(Tracker):

    tracks = glob.glob(os.path.join(IMAGEDIR, "*.png"))

    def __call__(self, track, slice=None):

        rst_text = '''
This is a preface

.. figure:: %s

Some more text for the figure\n''' % track

        return {"rst": rst_text}


class Images2(Tracker):

    tracks = "all"

    def __call__(self, track, slice=None):

        blocks = ResultBlocks()

        block = '''
.. figure:: %(image)s
   :height: 300
'''
        for image in glob.glob(os.path.join(IMAGEDIR, "*.png")):
            blocks.append(ResultBlock(text=block % locals(),
                                      title="image"))

        return odict((("rst", "\n".join(
            Utils.layoutBlocks(blocks, layout="columns-2"))),))
