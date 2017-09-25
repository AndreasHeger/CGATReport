"""Use wraith to compare current version against published docs.
"""

import unittest
import os
import copy
import re
import yaml
import subprocess
import contextlib
from distutils.version import LooseVersion
import http.server
import socketserver
import threading

REFERENCE_URL = "https://www.cgat.org/downloads/public/CGATReport/documentation"
WRAITH_WORKDIR = os.path.abspath("wraith")
TEST_PORT=9100
TEST_HOST="localhost"

spider_config_template = """
browser: "phantomjs"
domains:
  test: http://{test_host}:{test_port}
spider_skips:
  - !ruby/regexp /static$/
  - !ruby/regexp /%23/
  - !ruby/regexp /.eps$/
  - !ruby/regexp /.svg$/
  - !ruby/regexp /.xlsx$/
  - !ruby/regexp /notebook/
  - !ruby/regexp /code/
directory: 'shots'
imports: "{wraith_data_config}"
phantomjs_options: '--ignore-ssl-errors=true --ssl-protocol=tlsv1'
"""

capture_config_template = """
browser: "phantomjs"
domains:
  test: http://{test_host}:{test_port}
  current: {reference_url}
spider_skips:
  - !ruby/regexp /static$/
  - !ruby/regexp /%23/
imports: "{wraith_data_config}"
screen_widths:
  - 1280
directory: 'shots'
fuzz: '20%'
threshold: 5
gallery:
  thumb_width:  200
  thumb_height: 200
mode: diffs_only
phantomjs_options: '--ignore-ssl-errors=true --ssl-protocol=tlsv1'
"""

@contextlib.contextmanager
def changedir(path):
    save_dir = os.path.abspath(os.getcwd())
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(save_dir)


def run_server():
    run("python -m http.server {} >& server.log".format(TEST_PORT))

        
@contextlib.contextmanager
def start_server(workdir):

    handler = http.server.SimpleHTTPRequestHandler

    with changedir(workdir):
        # thread = threading.Thread(target=run_server)
        # thread.start()
        print("yielding")
        yield
        print("back from yield")


def run(statement,
        return_stdout=False,
        return_popen=False,
        **kwargs):
    '''execute a command line statement.

    By default this method returns the code returned by the executed
    command. If *return_stdout* is True, the contents of stdout are
    returned as a file object. If *return_popen*, the Popen object is
    returned.

    ``kwargs`` are passed on to subprocess.call,
    subprocess.check_output or subprocess.Popen.

    Raises
    ------

    OSError
       If process failed or was terminated.

    '''

    # remove new lines
    statement = " ".join(re.sub("\t+", " ", statement).split("\n")).strip()
    print(statement)
    
    if "<(" in statement:
        shell = os.environ.get('SHELL', "/bin/bash")
        if "bash" not in shell:
            raise ValueError(
                "require bash for advanced shell syntax: <()")
        # Note: pipes.quote is deprecated. In Py3, use shlex.quote
        # (not present in Py2.7)
        statement = "%s -c %s" % (shell, pipes.quote(statement))

    if return_stdout:
        return subprocess.check_output(statement, shell=True, **kwargs).decode("utf-8")
    elif return_popen:
        return subprocess.Popen(statement, shell=True, **kwargs)
    else:
        retcode = subprocess.call(statement, shell=True, **kwargs)
        if retcode < 0:
            raise OSError("process was terminated by signal %i" % -retcode)
        return retcode


def check_version(cmd, regex, min_version):
    
    version_txt = run(cmd , return_stdout=True)
    version = re.search(regex, version_txt).groups()[0]
    if LooseVersion(version) < LooseVersion(min_version):
        raise ValueError("version check failed: {} < {}, '{}'".format(
            version, min_version, cmd))
    
    return version


class TestWraith(unittest.TestCase):

    def setUp(self):

        source_dir = os.path.join(
            os.path.dirname(os.path.dirname(
                os.path.abspath(__file__))),
            "doc", "_build", "html")
        
        # check if npm is intalled
        npm_version = check_version("npm --version", "(\S+)", "3.10")

        # check if phantomjs is installed
        phantomjs_version = check_version("npm list -g | grep phantom",
                                          "phantomjs@(\S+)",
                                          "2.1")

        
        ruby_version = check_version("ruby --version",
                                     "ruby (\S+)",
                                     "2.1")
        
        wraith_version = check_version(
            "gem list | grep wraith",
            "wraith \((\S+)\)",
            "4.0.1")

        # get gem info
        gem_data = yaml.load(run("gem environment", return_stdout=True))
        gem_paths = []
        for record in gem_data["RubyGems Environment"]:
            for key, value in record.items():
                if key == "GEM PATHS":
                    gem_paths.extend(value)
                    break
        if not gem_paths:
            raise ValueError("could not find GEM PATHS in gem environment")

        filenames = [os.path.join(path,
                                  "gems/wraith-{}/lib/wraith/spider.rb".format(wraith_version))
                     for path in gem_paths]
        if sum([os.path.exists(fn) for fn in filenames]) == 0:
            raise ValueError("could not find file spider.rb to patch in {}".format(filenames))            
        
        for fn in filenames:

            if not os.path.exists(fn):
                continue
            
            with open(fn) as inf:
                data = inf.read()
                
            if "path.downcase" in data:
                with open(fn, "w") as outf:
                    outf.write(re.sub("path.downcase", "path", data))
                    
        # crawl new docs to collect documents to test
        config_dir = os.path.abspath(os.path.join(WRAITH_WORKDIR, "config"))
        wraith_spider_config = os.path.join(config_dir, "wraith_spider.yml")
        wraith_capture_config = os.path.join(config_dir, "wraith_capture.yml")
        wraith_data_config = os.path.join(config_dir, "wraith_data.yml")
        
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        if not os.path.exists(wraith_spider_config):
            # do not crawl with reference, as crawler follows external links
            spider_config = spider_config_template.format(
                wraith_data_config=os.path.basename(wraith_data_config),
                test_host=TEST_HOST,
                test_port=TEST_PORT)
            with open(wraith_spider_config, "w") as outf:
                outf.write(spider_config)

        if not os.path.exists(wraith_data_config):
            with start_server(source_dir) as server:
                run("cd {} && wraith spider {}".format(WRAITH_WORKDIR, wraith_spider_config))

        if not os.path.exists(wraith_capture_config):
            # do not crawl with reference, as crawler follows external links
            capture_config = capture_config_template.format(
                wraith_data_config=os.path.basename(wraith_data_config),
                reference_url=REFERENCE_URL,
                test_host=TEST_HOST,
                test_port=TEST_PORT)
            with open(wraith_capture_config, "w") as outf:
                outf.write(capture_config)

        self.wraith_capture_config = wraith_capture_config
        self.source_dir = source_dir
        
    def test_against_reference(self):
        with start_server(self.source_dir) as server:
            run("cd {} && wraith capture {}".format(WRAITH_WORKDIR,
                                                    self.wraith_capture_config))


if __name__ == "__main__":
    unittest.main()

        
