import sys, os, re, random

from SphinxReport.Tracker import Tracker
from SphinxReport.odict import OrderedDict as odict

class LabeledDataExample( Tracker ):
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        if slice == "slice1":
            return odict( (("column1", 10),
                          ("column2", 20 ),) )
        elif slice == "slice2":
            return odict ( (("column1", 20),
                           ("column2", 10),
                           ("column3", 5),) )

class SingleColumnDataExample( Tracker ):
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        s = [random.randint(0,10) for x in range(20)]
        random.shuffle( s )
        return odict( (("data", s),) )

class MultipleColumnDataExample( Tracker ):
    '''multiple columns each with a column with data.'''
    mColumns = [ "col1", "col2", "col3" ]
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2"
    def __call__(self, track, slice = None):
        data = []
        if slice == "slice1":
            for x in range(len(self.mColumns)-1):
                data.append( [ y + random.gauss( 0, 0.2 ) for y in range(20) ] )
        elif slice == "slice2":
            for x in range(len(self.mColumns)):
                data.append( [ y + random.gauss( 0, 0.5 ) for y in range(20) ] )
        return odict( zip(self.mColumns, data) )

class MultipleColumnDataFullExample( Tracker ):
    '''multiple columns each with a column with data.'''
    mColumns = [ "col1", "col2", "col3" ]
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2"
    def __call__(self, track, slice = None):
        data = []
        if slice == "slice1":
            for x in range(len(self.mColumns)):
                data.append( [ y + random.gauss( 0, 0.2 ) for y in range(20) ] )
        elif slice == "slice2":
            for x in range(len(self.mColumns)):
                data.append( [ y + random.gauss( 0, 0.5 ) for y in range(20) ] )
        return odict( zip(self.mColumns, data) )

class MultipleColumnsExample( Tracker ):
    '''multiple columns each with single value.'''
    mColumns = [ "col1", "col2", "col3" ]
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2"
    def __call__(self, track, slice = None):
        data = []
        if slice == "slice1":
            for x in range(len(self.mColumns)-1):
                data.append( x+1 )
        elif slice == "slice2":
            for x in range(len(self.mColumns)):
                data.append( x+1 )
        return odict( zip(self.mColumns, data) )


    
