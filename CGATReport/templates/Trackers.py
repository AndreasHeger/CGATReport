from CGATReport.Tracker import Tracker
from collections import OrderedDict as odict


class SimpleExampleData(Tracker):
    """Simple Example Data.
    """

    tracks = ["bicycle", "car"]

    def __call__(self, track):
        if track == "car":
            return odict((("wheels", 4), ("max passengers", 5)))
        elif track == "bicycle":
            return odict((("wheels", 2), ("max passengers", 1)))
