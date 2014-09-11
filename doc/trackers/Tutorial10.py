from CGATReport.Tracker import Tracker
from collections import OrderedDict as odict
import matplotlib.dates
import datetime


class ProjectDatesExample(Tracker):
    tracks = ("proj1", "proj2", "proj3")

    def __call__(self, track):

        # define a convenience function to convert
        # a three-number tuple to a scalar date float:
        f = lambda year, month, day: matplotlib.dates.date2num(
            datetime.datetime(year, month, day))

        if track == "proj1":
            return odict((("start", f(2012, 1, 1)),
                          ("duration", 100)))
        elif track == "proj2":
            return odict((("start", f(2012, 6, 1)),
                          ("duration", 200)))
        elif track == "proj3":
            return odict((("start", f(2012, 8, 1)),
                          ("duration", 100)))
