from CGATReport.Tracker import Tracker

import re
import os
import six


class WordCounterWithSlices(Tracker):
    """Counting word size."""

    def getTracks(self):
        return ("all", ".py", ".rst")

    def getSlices(self):
        return ("any", "vocals", "consonants")

    def __call__(self, track, slice):
        word_sizes = []

        if track == "all":
            tracks = [".py", ".rst"]
        else:
            tracks = [track]

        if slice == "any":
            test_f = lambda x: True
        elif slice == "vocals":
            test_f = lambda x: x[0].upper() in "AEIOU"
        elif slice == "consonants":
            test_f = lambda x: x[0].upper() not in "BCDFGHJKLMNPQRSTVWXYZ"

        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for f in files:
                fn, ext = os.path.splitext(f)
                if ext not in tracks:
                    continue
                if six.PY2:
                    infile = open(os.path.join(root, f), "r")
                else:
                    infile = open(os.path.join(root, f), "r", encoding="utf-8")
                words = [
                    w for w in
                    re.split("\s+", "".join(infile.readlines()))
                    if len(w) > 0]
                word_sizes.extend([len(w) for w in words if test_f(w)])
                infile.close()

        return {"word sizes": word_sizes}
