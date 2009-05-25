from SphinxReport.DataTypes import *
from SphinxReport.Tracker import *

class ExpressionLevel(TrackerSQL):
    """Expression level measurements."""
    mPattern = "_data$"

    @returnSingleColumnData
    def __call__(self, track, slice = None ):
        statement = "SELECT expression FROM %s_data" % track
        data = self.getValues( statement )
        return data

class ExpressionLevelWithSlices(ExpressionLevel):
    """Expression level measurements."""

    def getSlices( self, subset = None ):
        return ( "housekeeping", "regulation" )
    
    @returnSingleColumnData
    def __call__(self, track, slice = None ):
        if not slice: where = ""
        else: where = "WHERE function = '%s'" % slice
        statement = "SELECT expression FROM %s_data %s" % (track,where)
        data = self.getValues( statement )
        return data
