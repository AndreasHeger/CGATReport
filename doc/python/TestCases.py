import sys, os, re, random

from SphinxReport.Tracker import Tracker
from SphinxReport.DataTypes import returnLabeledData, returnSingleColumnData, returnMultipleColumnData, returnMultipleColumns

class LongLabelsSmall( Tracker ):
    """example with long labels."""
    mWordSize = 5
    mNumWords = 5
    def getSlices( self, subset = None ): return "small", "large", "gigantic"
    def getTracks( self ): return "track1", "track2", "track3"
    @returnLabeledData
    def __call__(self, track, slice = None):
        if slice == "small": ncolumns = 10
        elif slice == "large": ncolumns = 40
        elif slice == "gigantic": ncolumns = 300

        data = []
        for x in range( 0, ncolumns):
            label = "%s:%i %s" % ( slice, x, " ".join([ "a" * self.mWordSize for y in range(self.mNumWords) ] ))
            data.append( (label, random.randint( 0,100 )) )
        return data

class LargeMatrix( Tracker ):
    """example of a large matrix with long labels."""
    mWordSize = 5
    mNumWords = 5
    mNumTracks = 50

    def getSlices( self, subset = None ): return "small", "large"
    def getTracks( self ): return ["track%i" % i for i in range(self.mNumTracks)]
    @returnLabeledData
    def __call__(self, track, slice = None):
        if slice == "small": ncolumns = 10
        elif slice == "large": ncolumns = 40

        data = []
        for x in range( 0, ncolumns):
            label = "%s:%i %s" % ( slice, x, " ".join([ "a" * self.mWordSize for y in range(self.mNumWords) ] ))
            data.append( (label, random.randint( 0,100 )) )
        return data

class LayoutTest( Tracker ):
    """Layout testing."""
    mNumSlices = 3
    mNumTracks = 5
    mNumSamples = 100

    def getSlices( self, subset = None ): return ["slice%i" % i for i in range(self.mNumSlices)]
    def getTracks( self ): return ["track%i" % i for i in range(self.mNumTracks)]

    @returnSingleColumnData
    def __call__(self, track, slice = None):
        return [ random.gauss( 0,1 ) for x in range(self.mNumSamples) ]
