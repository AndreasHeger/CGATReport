#!/usr/bin/env python
'''unit testing code for SphinxReport
'''

import unittest
import os, re, sys
import itertools
import collections
import subprocess
import shutil
import logging

IS_PYTHON3 = sys.version_info[0] >= 3

import SphinxReport
import SphinxReport.Utils
import SphinxReport.Dispatcher

class SphinxReportTest(unittest.TestCase):
    ''' '''
    renderer = "table"
    tracker = "tests.TestTrackers.LabeledDataExample"
    
    def testTracker( self ):
        
        code, tracker = SphinxReport.Utils.makeTracker( self.tracker, (), {} )
        renderer = SphinxReport.Utils.getRenderer( self.renderer, {} )

        dispatcher = SphinxReport.Dispatcher.Dispatcher( tracker,
                                                         renderer,
                                                         [] )
        results = dispatcher( {} )
        print (results)
        return True

    
    
