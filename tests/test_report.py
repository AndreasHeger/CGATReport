import unittest
import subprocess
import collections
import os

N_CORES = 4


class TestReportBuilding(unittest.TestCase):

    ignored_errors = [
        "testing",
        "UnknownTracker",
        "GalleryBokeh",
        "TestExceptions",
        "unknown-renderer",
        "unknown-transform"]

    def testFullReport(self):

        build_dir = "test_report-results.dir"
        docs_dir = os.path.abspath("../doc")

        # "cgatreport-build --num-jobs={n_cores} "

        subprocess.check_output(
            "rm -rf {build_dir} && "
            "mkdir {build_dir} && "
            "gunzip < csvdb_data.txt.gz | sqlite3 {build_dir}/csvdb && "
            "cp -r {docs_dir}/images {build_dir} && "
            "cp {docs_dir}/*.ini {build_dir}/ && "
            "cd {build_dir} && "
            "xvfb-run -a "
            "sphinx-build -j {n_cores} "
            "-b html "
            "-d _build/doctrees "
            "{docs_dir} "
            "_build/html".format(
                build_dir=build_dir,
                docs_dir=docs_dir,
                n_cores=N_CORES),
            shell=True)

        errors = []
        counter = collections.defaultdict(int)
        with open(os.path.join(build_dir, "cgatreport.log")) as inf:
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

        self.assertEqual(
            counter["ERROR"], 0,
            "List of errors:\n{lines}\n"
            "There were {nerrors} errors during report building. "
            "See {build_dir}/cgatreport.log "
            "for more information".format(
                lines="".join(errors),
                build_dir=build_dir,
                nerrors=counter["ERROR"]))

if __name__ == "__main__":
    unittest.main()    
