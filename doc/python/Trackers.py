import sys, os, re, random

from SphinxReport.Tracker import Tracker
from SphinxReport.DataTypes import returnLabeledData, returnSingleColumnData, returnMultipleColumnData, returnMultipleColumns

class LabeledData( Tracker ):
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self ): return "track1", "track2", "track3"
    @returnLabeledData
    def __call__(self, track, slice = None):
        if slice == "slice1":
            return [ ("column1", 10),
                     ("column2", 20 ), ]
        elif slice == "slice2":
            return [ ("column1", 20),
                     ("column2", 10 ), ]

class SingleColumnData( Tracker ):
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self ): return "track1", "track2", "track3"
    @returnSingleColumnData
    def __call__(self, track, slice = None):
        s = [random.randint(0,10) for x in range(20)]
        random.shuffle( s )
        return s

class MultipleColumnData( Tracker ):
    mColumns = [ "col1", "col2" ]
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self ): return "track1", "track2"
    @returnMultipleColumnData
    def __call__(self, track, slice = None):
        data = []
        if slice == "slice1":
            for x in range(len(self.mColumns)):
                data.append( [ y + random.gauss( 0, 0.2 ) for y in range(20) ] )
        elif slice == "slice2":
            for x in range(len(self.mColumns)):
                data.append( [ y + random.gauss( 0, 0.5 ) for y in range(20) ] )
        return [ self.mColumns, data ]

class MultipleColumns( Tracker ):
    mColumns = [ "col1", "col2" ]
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self ): return "track1", "track2"
    @returnMultipleColumns
    def __call__(self, track, slice = None):
        data = []
        if slice == "slice1":
            for x in range(len(self.mColumns)):
                data.append( ("%s-a" % track, "%s-b" % track, 2, 3 ) )
        elif slice == "slice2":
            for x in range(len(self.mColumns)):
                data.append( ("%s-c" % track, "%s-d" % track, 1, 4 ) )
        return [ self.mColumns, data ]
