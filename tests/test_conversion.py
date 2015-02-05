'''unit testing code for SphinxReport
'''

import itertools
from copy import deepcopy
import unittest

from CGATReport.DataTree import asDataFrame
from collections import OrderedDict as odict


class TestLabeledValues(unittest.TestCase):
    '''test dataframe conversions.'''

    def setUp(self):

        # order is explicitely non-alphabetical
        # to make sure it is preserved.

        self.data = odict((
            ('rowC', odict(
                (('colC', 1),
                 ('colB', 2),
                 ('colA', 3))
            )),
            ('rowB', odict(
                (('colC', 4),
                 ('colB', 5),
                 ('colA', 6))
            )),
            ('rowA', odict(
                (('colC', 7),
                 ('colB', 8),
                 ('colA', 9))
            ))
        ))

    def testSimple(self):

        df = asDataFrame(self.data)
        self.assertEqual(list(df.columns),
                         ["colC", "colB", "colA"])
        self.assertEqual(list(df.index),
                         ["rowC", "rowB", "rowA"])

    def testEmptyRow(self):

        for row in self.data.keys():
            dd = deepcopy(self.data)
            dd[row] = odict()
            df = asDataFrame(dd)
            self.assertEqual(list(df.columns),
                             ["colC", "colB", "colA"])
            self.assertEqual(list(df.index),
                             ["rowC", "rowB", "rowA"])

    def testMissingValues(self):

        for row, col in itertools.product(
                ("rowA", "rowB", "rowC"),
                ("colA", "colB", "colC")):
            dd = deepcopy(self.data)
            del dd[row][col]
            df = asDataFrame(dd)

            if row == "rowC" and col == "colB":
                # first row misses column B, so column A is second
                self.assertEqual(list(df.columns),
                                 ["colC", "colA", "colB"])
            elif row == "rowC" and col == "colC":
                # first row misses column C, so column B is second
                self.assertEqual(list(df.columns),
                                 ["colB", "colA", "colC"])
                
            else:
                self.assertEqual(list(df.columns),
                                 ["colC", "colB", "colA"])

            self.assertEqual(list(df.index),
                             ["rowC", "rowB", "rowA"])


class TestArrayValues(unittest.TestCase):
    '''test dataframe conversions.'''

    def setUp(self):

        # order is explicitely non-alphabetical
        # to make sure it is preserved.

        self.data = odict((
            ('rowC', odict(
                (('colC', [1] * 5),
                 ('colB', [2] * 5),
                 ('colA', [3] * 5))
            )),
            ('rowB', odict(
                (('colC', [4] * 6),
                 ('colB', [5] * 6),
                 ('colA', [6] * 6))
            )),
            ('rowA', odict(
                (('colC', [7] * 7),
                 ('colB', [8] * 7),
                 ('colA', [9] * 7))
            ))
        ))

        self.ref = ["rowC"] * 5 + ["rowB"] * 6 + ["rowA"] * 7

    def testSimple(self):

        df = asDataFrame(self.data)
        self.assertEqual(list(df.columns),
                         ["colC", "colB", "colA"])
        self.assertEqual(list(df.index),
                         self.ref)
        
    def testEmptyRow(self):

        for row in self.data.keys():
            dd = deepcopy(self.data)
            dd[row] = odict()
            df = asDataFrame(dd)
            self.assertEqual(list(df.columns),
                             ["colC", "colB", "colA"])
            self.assertEqual(list(df.index),
                             [x for x in self.ref if x != row])

    def testMissingValues(self):

        for row, col in itertools.product(
                ("rowA", "rowB", "rowC"),
                ("colA", "colB", "colC")):
            dd = deepcopy(self.data)
            del dd[row][col]
            df = asDataFrame(dd)

            if row == "rowC" and col == "colB":
                # first row misses column B, so column A is second
                self.assertEqual(list(df.columns),
                                 ["colC", "colA", "colB"])
            elif row == "rowC" and col == "colC":
                # first row misses column C, so column B is second
                self.assertEqual(list(df.columns),
                                 ["colB", "colA", "colC"])
                
            else:
                self.assertEqual(list(df.columns),
                                 ["colC", "colB", "colA"])

            self.assertEqual(list(df.index),
                             self.ref)

if __name__ == "__main__":
    unittest.main()
