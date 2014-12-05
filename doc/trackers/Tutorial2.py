from CGATReport.Tracker import Tracker


class MyDataOneTrack(Tracker):

    """My tracked data - one track."""

    def getTracks(self):
        return ["all", ]

    def __call__(self, track):
        return dict((("header1", 10), ("header2", 20)),)


class MyDataTwoTracks(Tracker):

    """My tracked data - two tracks."""

    def getTracks(self):
        return ["track1", "track2"]

    def __call__(self, track):
        if track == "track1":
            return dict((("header1", 10), ("header2", 20)),)
        elif track == "track2":
            return dict((("header1", 20), ("header2", 10)),)
