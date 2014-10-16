#!/usr/bin/env python
'''unit testing code for SphinxReport
'''

import unittest
import sys

IS_PYTHON3 = sys.version_info[0] >= 3

import SphinxReport
import SphinxReport.Utils
import SphinxReport.Dispatcher


class SphinxReportTest(unittest.TestCase):
    ''' '''
    renderer = "table"
    tracker = "tests.TestTrackers.LabeledDataExample"

    def testTracker(self):
        code, tracker, tracker_path = SphinxReport.Utils.makeTracker(
            self.tracker, (), {})
        renderer = SphinxReport.Utils.getRenderer(
            self.renderer, {})

        dispatcher = SphinxReport.Dispatcher.Dispatcher(
            tracker,
            renderer,
            [])
        results = dispatcher({})
        print (results)
        return True

