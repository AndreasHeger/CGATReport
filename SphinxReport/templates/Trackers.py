from SphinxReport.Tracker import Tracker
from SphinxReport.DataTypes import *

class SimpleExampleData(Tracker):
   """Simple Example Data.
   """

   def getTracks( self ): return ["bicycle", "car" ]

   @returnLabeledData
   def __call__(self, track, slice = None ):
       if track == "car":
           return ( ("wheels", 4), ("max passengers", 5) )
       elif track == "bicycle":
           return ( ("wheels", 2), ("max passengers", 1) )
