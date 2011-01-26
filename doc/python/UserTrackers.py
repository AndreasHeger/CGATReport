import sys, os, re, random

from SphinxReport.Tracker import Tracker
from SphinxReport.odict import OrderedDict as odict

import matplotlib
from matplotlib import pyplot as plt

from rpy import r as R

def getCurrentRDevice():
    '''return the numerical device id of the current device.'''
    return R.dev_cur().values()[0]

class MatplotlibData( Tracker ):
    '''create plot using matplotlib.'''
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        s = [random.randint(0,20) for x in range(40)]
        random.shuffle( s )

        # do the plotting
        fig = plt.figure()
        plt.plot( s )
        return odict( (("text", "#$mpl %i$#" % fig.number),) )

class RPlotData( Tracker ):
    '''create plot using R.'''
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        s = [random.randint(0,20) for x in range(40)]
        random.shuffle( s )
        # do the plotting
        R.x11()
        R.plot( s )
        return odict( (("text", "#$rpl %i$#" % getCurrentRDevice()),) )

