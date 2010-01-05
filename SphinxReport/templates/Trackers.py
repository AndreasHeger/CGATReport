from SphinxReport.Tracker import *
from SphinxReport.Renderer import *

class SimpleExampleData(Tracker):
   """Simple Example Data.
   """

   def getTracks( self, subset = None ): return ["bicycle", "car" ]

   def __call__(self, track, slice = None ):
       if track == "car":
           return odict( ( ("wheels", 4), ("max passengers", 5) ) )
       elif track == "bicycle":
           return odict( ( ("wheels", 2), ("max passengers", 1) ) )
