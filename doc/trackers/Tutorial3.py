from CGATReport.Tracker import Tracker

import os
import re


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

        for root, dirs, files in os.walk('.'):
            for f in files:
                fn, ext = os.path.splitext(f)
                if ext not in tracks:
                    continue
                infile = open(os.path.join(root, f), "r")
                words = re.split("\s+", "".join(infile.readlines()))
                word_sizes.extend([len(word) for word in words])
                infile.close()

        return {"word sizes": word_sizes}
