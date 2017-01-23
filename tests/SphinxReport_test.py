#!/usr/bin/env python
'''unit testing code for SphinxReport
'''

import unittest
import sys

IS_PYTHON3 = sys.version_info[0] >= 3

import CGATReport
import CGATReport.Utils
import CGATReport.Dispatcher


class CGATReportTest(unittest.TestCase):
    ''' '''
    renderer = "table"
    tracker = "tests.TestTrackers.LabeledDataExample"

    def testTracker(self):
        code, tracker, tracker_path = CGATReport.Utils.makeTracker(
            self.tracker, (), {})
        renderer = CGATReport.Utils.getRenderer(
            self.renderer, {})

        dispatcher = CGATReport.Dispatcher.Dispatcher(
            tracker,
            renderer,
            [])
        results = dispatcher({})
        print (results)
        return True


if __name__ == "__main__":
    unittest.main()
