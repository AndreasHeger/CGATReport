# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from CGATReport.Tracker import Tracker
from collections import OrderedDict as odict


class LabeledDataExampleUnicode(Tracker):
    slices = ("slüce1", "slüce2")
    tracks = ("träck1", "träck2", "träck3")

    def __call__(self, track, slice=None):

        v = int(track[-1]) * int(slice[-1])
        if slice == "slüce1":
            return odict((("column1", v),
                          ("column2", v * 2),))
        elif slice == "slüce2":
            return odict((("column1", v),
                          ("column2", v * 2),
                          ("column3", v * 3),))
