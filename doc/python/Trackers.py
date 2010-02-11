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

class LabeledDataWithErrorsExample( Tracker ):
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        if slice == "slice1":
            return odict( ( 
                    ("column1", dict( ( ('data', 20), 
                                        ('error',5), 
                                        ('label','**' ) ) )),
                    ("column2", dict( ( ('data', 10), 
                                        ('error',2), 
                                        ('label', '*' ) ) ) )
                    )) 
        elif slice == "slice2":
            return odict( ( 
                    ("column1", dict( ( ('data', 20), 
                                        ('error',5),
                                        ('label','***' ) ) )),
                    ("column2", dict( ( ('data', 10), 
                                        ('error',1))) ),
                    ("column3", dict( ( ('data', 30), 
                                        ('error',4))) ),
                    ) )

class SingleColumnDataExample( Tracker ):
    '''return a single column of data.'''
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        s = [random.randint(0,20) for x in range(40)]
        random.shuffle( s )
        return odict( (("data", s),) )

class SingleColumnDataWithErrorExample( Tracker ):
    '''return a single column of data.'''
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        s = [random.randint(0,20) for x in range(40)]
        e = [random.randint(0,3) for x in range(40)]
        random.shuffle( s )
        return odict( (("data", s),
                       ("error", e) ) )

class SingleColumnDataExampleWithoutSlices( Tracker ):
    '''return a single column of data.'''
    def getSlices( self, subset = None ): return []
    def getTracks( self, subset = None ): return "track1", "track2", "track3"
    def __call__(self, track, slice = None):
        s = [random.randint(0,20) for x in range(40)]
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

class ErrorInTracker1( Tracker ):
    '''A tracker that creates an error - exception while collecting data.'''
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2"
    def __call__(self, track, slice = None):
        raise ValueError("testing: could not collect data")
    
class ErrorInTracker2( Tracker ):
    '''A tracker that creates an error - problems while returning tracks.'''
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): raise ValueError("testing: did not return trackers.")
    def __call__(self, track, slice = None):
        return odict( (("data", range(0,10)),) )

class ErrorInTracker3( Tracker ):
    '''A tracker that creates an error - problems while returning tracks.'''
    def getSlices( self, subset = None ): return "slice1", "slice2"
    def getTracks( self, subset = None ): return "track1", "track2"
    def __call__(self, track, slice = None):
        return None



    

