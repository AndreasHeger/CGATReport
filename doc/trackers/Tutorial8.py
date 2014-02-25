from SphinxReport.Tracker import *

class UserVennTracker(Tracker):
    def __call__(self):
        return odict((("set1", 10), ("set2", 20), ('intersection', 5)))
