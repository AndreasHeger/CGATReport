#!/usr/bin/env python
'''unit testing code for SphinxReport
'''

import unittest
import CGATReport
import CGATReport.Dispatcher
from CGATReport.Capabilities import get_renderer, make_tracker


class CGATReportTest(unittest.TestCase):
    ''' '''
    renderer = "table"
    tracker = "tests.TestTrackers.LabeledDataExample"

    def testTracker(self):
        code, tracker, tracker_path = make_tracker(
            self.tracker, (), {})
        renderer = get_renderer(
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
