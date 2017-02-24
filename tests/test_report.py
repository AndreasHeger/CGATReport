import unittest
import subprocess
import collections
import os
import re
import tempfile
import shutil
import sys

N_CORES = 4


class TestReportBuilding(unittest.TestCase):

    ignored_errors = [
        "testing",
        "UnknownTracker",
        "GalleryBokeh",
        "TestExceptions",
        "unknown-renderer",
        "unknown-transform"]

    def setUp(self):
        # build_dir = tempfile.mkdtemp(prefix="test_report-results.dir.",
        #                             dir=os.path.abspath(os.curdir))


        self.build_dir = os.path.join(os.path.abspath(os.curdir),
                                      "test_report-results-{}.dir".format(
                                          sys.version.split(" ")[0]))

        self.docs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "doc")
        
        if not os.path.exists(self.docs_dir):
            raise ValueError("doc directory {} does not exist".format(self.docs_dir))

        print ("docs_dir is {}".format(self.docs_dir))
        print ("build_dir is {}".format(self.build_dir))

    def parse_cgatreport_log(self):
        
        errors = []
        counter = collections.defaultdict(int)
        with open(os.path.join(self.build_dir, "cgatreport.log")) as inf:
            for line in inf:
                parts = line[:-1].split(" ")
                if len(parts) < 3:
                    continue
                # ignore errors created in test suite
                skip = False
                for pattern in self.ignored_errors:
                    if pattern in line:
                        skip = True
                        break
                if skip:
                    continue
                counter[parts[2]] += 1
                if parts[2] == "ERROR":
                    errors.append(line)

        # shutil.rmtree(build_dir)
        # filter version specific errors
        if sys.version_info.major == 3 and sys.version_info.minor >= 5:
            # statsmodels 0.6.1 is not py3.5 compatible
            errors = [x for x in errors if not re.search(
                    "seaborn raised error for statement"
                    ".*"
                    "slice indices must be "
                    "integers or None or have an __index__ method", x)]
            errors = [x for x in errors if not re.search(
                    "exception in rendering: <class 'TypeError'>"
                    ".*"
                    "slice indices must be "
                    "integers or None or have an __index__ method", x)]

            counter["ERROR"] = len(errors)
        return counter, errors

    def test_full_docs_build_without_error(self):

        # "cgatreport-build --num-jobs={n_cores} "

        subprocess.check_output(
            "rm -rf {build_dir} && "
            "mkdir {build_dir} && "
            "gunzip < {docs_dir}/csvdb_data.txt.gz | sqlite3 {build_dir}/csvdb && "
            "cp -r {docs_dir}/images {build_dir} && "
            "cp {docs_dir}/*.ini {build_dir}/ && "
            "cd {build_dir} && "
            "xvfb-run -d "
            "sphinx-build "
            "-j {n_cores} "
            "-b html "
            "-d _build/doctrees "
            "{docs_dir} "
            "_build/html >& {build_dir}/build.log".format(
                build_dir=self.build_dir,
                docs_dir=self.docs_dir,
                n_cores=N_CORES),
            shell=True)
        
        counter, errors = self.parse_cgatreport_log()

        self.assertEqual(
            counter["ERROR"], 0,
            "List of errors:\n{lines}\n"
            "There were {nerrors} errors during report building. "
            "See {build_dir}/cgatreport.log "
            "for more information".format(
                lines="".join(errors),
                build_dir=self.build_dir,
                nerrors=counter["ERROR"]))

    def test_quickstart_report_will_pass(self):

        subprocess.check_output(
            "rm -rf {build_dir} && "
            "mkdir {build_dir} && "
            "cgatreport-quickstart -d {build_dir} >& {build_dir}/quickstart.log && "
            "make -C {build_dir} html >& {build_dir}/build.log".format(
                build_dir=self.build_dir,
                docs_dir=self.docs_dir,
                n_cores=N_CORES),
            shell=True)

        counter, errors = self.parse_cgatreport_log()

        self.assertEqual(
            counter["ERROR"], 0,
            "List of errors:\n{lines}\n"
            "There were {nerrors} errors during report building. "
            "See {build_dir}/cgatreport.log "
            "for more information".format(
                lines="".join(errors),
                build_dir=self.build_dir,
                nerrors=counter["ERROR"]))


if __name__ == "__main__":
    unittest.main()    
