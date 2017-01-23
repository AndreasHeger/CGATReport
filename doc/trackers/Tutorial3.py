from CGATReport.Tracker import Tracker

import os
import re
import six


class WordCounter(Tracker):

    """Counting word size."""

    def getTracks(self):
        return ("all", ".py", ".rst")

    def __call__(self, track):
        word_sizes = []

        if track == "all":
            tracks = [".py", ".rst"]
        else:
            tracks = [track]

        for root, dirs, files in os.walk(os.path.dirname(__file__)):
            for f in files:
                fn, ext = os.path.splitext(f)
                if ext not in tracks:
                    continue
                if six.PY2:
                    infile = open(os.path.join(root, f), "r")
                else:
                    infile = open(os.path.join(root, f), "r", encoding="utf-8")
                words = re.split("\s+", "".join(infile.readlines()))
                word_sizes.extend([len(word) for word in words])
                infile.close()

        return {"word sizes": word_sizes}
