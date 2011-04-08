import sys, os, re, random, glob

from SphinxReport.Tracker import Tracker
from SphinxReport.odict import OrderedDict as odict

import matplotlib
from matplotlib import pyplot as plt

from rpy2.robjects import r as R
import rpy2.robjects as ro
import rpy2.robjects.numpy2ri

def getCurrentRDevice():
    '''return the numerical device id of the current device.'''
    #R.dev_off()
    #return R.dev_cur().values()[0]
    return R["dev.cur"]()[0]

class MatplotlibData( Tracker ):
    '''create plot using matplotlib.'''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")
    def __call__(self, track, slice = None):
        s = [random.randint(0,20) for x in range(40)]
        random.shuffle( s )

        # do the plotting
        fig = plt.figure()
        plt.plot( s )
        return odict( (("text", "#$mpl %i$#" % fig.number),) )

class RPlotData( Tracker ):
    '''create plot using R.'''
    slices = ("slice1", "slice2")
    tracks = ("track1", "track2", "track3")
    def __call__(self, track, slice = None):
        s = [random.randint(0,20) for x in range(40)]
        random.shuffle( s )
        # do the plotting
        R.x11()
        R.plot( s, s )
        return odict( (("text", "#$rpl %i$#" % getCurrentRDevice()),) )

IMAGEDIR = os.path.join( os.path.dirname( os.path.abspath( __file__ )), "..", "images")

class Images( Tracker ):
    tracks = glob.glob( os.path.join( IMAGEDIR, "*.png" ) )
    def __call__(self, track, slice = None ):
        rst_text = '''
This is a preface

.. figure:: %s

Some more text for the figure\n''' % track

        return odict( (("rst", rst_text),) )
