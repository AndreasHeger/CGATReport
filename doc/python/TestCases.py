import sys, os, re, random

from SphinxReport.Tracker import *

class LongLabelsSmall( Tracker ):
    """example with long labels."""
    mWordSize = 5
    mNumWords = 5
    def getSlices( self, subset = None ): return "small", "large", "gigantic"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        if slice == "small": ncolumns = 10
        elif slice == "large": ncolumns = 40
        elif slice == "gigantic": ncolumns = 100

        data = []
        for x in range( 0, ncolumns):
            label = "%s:%i %s" % ( slice, x, " ".join([ "a" * self.mWordSize for y in range(self.mNumWords) ] ))
            data.append( (label, random.randint( 0,100 )) )
        return dict( data )

class LargeMatrix( Tracker ):
    """example of a large matrix with long labels."""
    mWordSize = 5
    mNumWords = 5
    mNumTracks = 50

    def getSlices( self, subset = None ): return "small", "large"
    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.mNumTracks)]
    def __call__(self, track, slice = None):
        if slice == "small": ncolumns = 10
        elif slice == "large": ncolumns = 40

        data = []
        for x in range( 0, ncolumns):
            label = "%s:%i %s" % ( slice, x, " ".join([ "a" * self.mWordSize for y in range(self.mNumWords) ] ))
            data.append( (label, random.randint( 0,100 )) )
        return dict( data )

class LayoutTest( Tracker ):
    """Layout testing."""
    mNumSlices = 3
    mNumTracks = 5
    mNumSamples = 100

    def getSlices( self, subset = None ): return ["slice%i" % i for i in range(self.mNumSlices)]
    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.mNumTracks)]

    def __call__(self, track, slice = None):
        return dict( ( ("data", [ random.gauss( 0,1 ) for x in range(self.mNumSamples) ]),))

class MultipleHistogramTest( Tracker ):
    """Layout testing."""
    mNumSlices = 3
    mNumTracks = 5
    mNumSamples = 100

    def getSlices( self, subset = None ): return ["slice%i" % i for i in range(self.mNumSlices)]
    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.mNumTracks)]

    def __call__(self, track, slice = None):
        return dict( ( ("bin", "value-set1", "value-set2"),
                       (range(0,self.mNumSamples),
                        [ random.gauss( 0,1 ) for x in range(self.mNumSamples) ],
                        [ random.gauss( 0,1 ) for x in range(self.mNumSamples) ] )))


class MultiLevelTable( Tracker ):

    mNumTracks = 5
    mNumCols = 3
    mNumLevels = 3

    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.mNumTracks)]

    def __call__(self, track, slice = None ):
        data = [ \
            [ "value%i" % y for y in range(self.mNumLevels) ] \
                  for z in range(self.mNumCols) ]

        return odict( zip( ["col%i" % x for x in range(self.mNumCols)], data ) )
