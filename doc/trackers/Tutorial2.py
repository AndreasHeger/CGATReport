from CGATReport.Tracker import Tracker
from collections import OrderedDict


class MyDataOneTrack(Tracker):

    """My tracked data - one track."""

    def getTracks(self):
        return ["all", ]

    def __call__(self, track):
        return OrderedDict((("header1", 10), ("header2", 20)),)


class MyDataTwoTracks(Tracker):

    """My tracked data - two tracks."""

    def getTracks(self):
        return ["track1", "track2"]

    def __call__(self, track):
        if track == "track1":
            return OrderedDict((("header1", 10), ("header2", 20)),)
        elif track == "track2":
            return OrderedDict((("header1", 20), ("header2", 10)),)
