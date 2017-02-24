import unittest
import subprocess
import collections
import os
import re
import tempfile
import shutil
import sys

N_CORES = 4

EXAMPLE_OUTPUT1 = """.. ---- TEMPLATE START --------

.. report:: Trackers.LabeledDataExample
   :render: table
   

   add caption here

.. ---- TEMPLATE END ----------

.. ---- OUTPUT-----------------
b''
b''
b''
b''
b'.. csv-table:: '
b'   :header: track,slice,column1,column2,column3'
b''
b'   track1,slice1,1.0,2.0,'
b'   track1,slice2,2.0,4.0,6.0'
b'   track2,slice1,2.0,4.0,'
b'   track2,slice2,4.0,8.0,12.0'
b'   track3,slice1,3.0,6.0,'
b'   track3,slice2,6.0,12.0,18.0'
b'   '
b''
b''
b''
"""


class TestCGATReportTest(unittest.TestCase):

    ignored_errors = [
        "testing",
        "UnknownTracker",
        "GalleryBokeh",
        "TestExceptions",
        "unknown-renderer",
        "unknown-transform"]

    def setUp(self):
        

        self.docs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "doc")
        
        if not os.path.exists(self.docs_dir):
            raise ValueError("doc directory {} does not exist".format(self.docs_dir))            
    def test_tracker_without_prefix_works(self):

        stdout = subprocess.check_output(
            "cgatreport-test "
            "--path={docs_dir}/trackers "
            "--renderer=table "
            "--tracker=LabeledDataExample ".format(
                docs_dir=self.docs_dir),
            shell=True)
        
        self.assertEqual(EXAMPLE_OUTPUT1, stdout)

    def test_tracker_with_prefix_works(self):

        stdout = subprocess.check_output(
            "cgatreport-test "
            "--path={docs_dir}/trackers "
            "--renderer=table "
            "--tracker=Trackers.LabeledDataExample ".format(
                docs_dir=self.docs_dir),
            shell=True)
        
        self.assertEqual(EXAMPLE_OUTPUT1, stdout)

    def test_tracker_with_missing_module_fails(self):

        self.assertRaises(
            subprocess.CalledProcessError,
            subprocess.check_output,
            "cgatreport-test "
            "--path={docs_dir}/trackers "
            "--renderer=table "
            "--tracker=Truckers.LabeledDataExample ".format(
                docs_dir=self.docs_dir),
            shell=True)

    def test_tracker_with_missing_tracker_fails(self):

        self.assertRaises(
            subprocess.CalledProcessError,
            subprocess.check_output,
            "cgatreport-test "
            "--path={docs_dir}/trackers "
            "--renderer=table "
            "--tracker=UnknownLabeledDataExample ".format(
                docs_dir=self.docs_dir),
            shell=True)
        

if __name__ == "__main__":
    unittest.main()    
