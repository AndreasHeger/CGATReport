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

