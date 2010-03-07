import sys, os, re, random

from SphinxReport.Tracker import *

class LongLabelsSmall( Tracker ):
    """example with long labels."""
    wordsize = 5
    numwords = 5
    def getSlices( self, subset = None ): return "small", "large", "gigantic"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        if slice == "small": ncolumns = 10
        elif slice == "large": ncolumns = 40
        elif slice == "gigantic": ncolumns = 100

        data = []
        for x in range( 0, ncolumns):
            label = "%s:%i %s" % ( slice, x, " ".join([ "a" * self.wordsize for y in range(self.numwords) ] ))
            data.append( (label, random.randint( 0,100 )) )
        return dict( data )

class LargeMatrix( Tracker ):
    """example of a large matrix with long labels."""
    wordsize = 5
    numwords = 5
    ntracks = 50

    def getSlices( self, subset = None ): return "small", "large"
    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.ntracks)]
    def __call__(self, track, slice = None):
        if slice == "small": ncolumns = 10
        elif slice == "large": ncolumns = 40

        data = []
        for x in range( 0, ncolumns):
            label = "%s:%i %s" % ( slice, x, " ".join([ "a" * self.wordsize for y in range(self.numwords) ] ))
            data.append( (label, random.randint( 0,100 )) )
        return dict( data )

class LayoutTest( Tracker ):
    """Layout testing."""
    nslices = 3
    ntracks = 5
    nsamples = 100

    def getSlices( self, subset = None ): return ["slice%i" % i for i in range(self.nslices)]
    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.ntracks)]

    def __call__(self, track, slice = None):
        return dict( ( ("data", [ random.gauss( 0,1 ) for x in range(self.nsamples) ]),))

class MultipleHistogramTest( Tracker ):
    """Layout testing."""
    nslices = 3
    ntracks = 5
    nsamples = 100

    def getSlices( self, subset = None ): return ["slice%i" % i for i in range(self.nslices)]
    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.ntracks)]

    def __call__(self, track, slice = None):
        return dict( ( ("bin", "value-set1", "value-set2"),
                       (range(0,self.nsamples),
                        [ random.gauss( 0,1 ) for x in range(self.nsamples) ],
                        [ random.gauss( 0,1 ) for x in range(self.nsamples) ] )))


class MultiLevelTable( Tracker ):

    ntracks = 5
    ncols = 3
    mNumLevels = 3

    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.ntracks)]

    def __call__(self, track, slice = None ):
        data = [ \
            [ "value%i" % y for y in range(self.mNumLevels) ] \
                for z in range(self.ncols) ]

        return odict( zip( ["col%i" % x for x in range(self.ncols)], data ) )

class LargeTable( Tracker ):
    '''test case covering rendering large tables.'''

    ntracks = 5
    ncols = 40
    nrows = 200

    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.ntracks)]
    
    def __call__(self, track, slice = None ):

        data = [ "value%i" % y for y in range(self.nrows) ]
        return odict( [ ("col%i" % x, data) for x in range(self.ncols)] )

class VeryLargeMatrix( Tracker ):
    """example of a large matrix with long labels."""

    # do not cache - slow in shelve as many key-value pairs
    cache = False

    ncols = 7000
    ntracks = 200

    def getTracks( self, subset = None ): return ["track%i" % i for i in range(self.ntracks)]

    def __call__(self, track, slice = None):
        
        data = []
        for x in range( 0, self.ncols):
            data.append( ("col%i%s" % (x,"f"*193),x ))

        return dict( data )
