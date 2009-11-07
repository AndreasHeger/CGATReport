############################################################
## Tutorial examples

from SphinxReport.DataTypes import *
from SphinxReport.Tracker import *

class MyDataOneTrack(Tracker):
    """My one-tracked data."""
    
    def getTracks( self, subset = None):
        return ["all",]

    def __call__(self, track, slice = None ):
        return dict( (("header1", 10), ("header2", 20)),)

class MyDataTwoTracks(Tracker):
    """My one-tracked data."""

    def getTracks( self, subset = None ):
        return ["track1","track2"]

    def __call__(self, track, slice = None ):
        if track == "track1":
            return dict( (("header1", 10), ("header2", 20)),)
        elif track == "track2":
            return dict( (("header1", 20), ("header2", 10)),)
