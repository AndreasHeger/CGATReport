########################################################################
# Import setuptools
# Use existing setuptools
try:
    from setuptools import setup, find_packages
except ImportError:
    # try to get via ez_setup
    # ez_setup did not work on all machines tested as
    # it uses curl with https protocol, which is not
    # enabled in ScientificLinux
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

import glob
import sys
import os
import re
import distutils.sysconfig
import stat
import subprocess

major, minor1, minor2, s, tmp = sys.version_info


#####################################################################
# Code to install dependencies from a repository
#####################################################################
# Modified from http://stackoverflow.com/a/9125399
#####################################################################
def which(program):
    """
    Detect whether or not a program is installed.
    Thanks to http://stackoverflow.com/a/377028/70191
    """
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

REPO_REQUIREMENT = re.compile(
    r'^-e (?P<link>(?P<vcs>git|svn|hg|bzr).+#egg=(?P<package>.+)-(?P<version>\d(?:\.\d)*))$')
HTTPS_REQUIREMENT = re.compile(
    r'^-e (?P<link>.*).+#(?P<package>.+)-(?P<version>\d(?:\.\d)*)$')
install_requires = []
dependency_links = []

for requirement in (l.strip() for l in open('requires.txt')
                    if not l.startswith("#")):
    match = REPO_REQUIREMENT.match(requirement)
    if match:
        assert which(match.group('vcs')) is not None, \
            "VCS '%(vcs)s' must be installed in order " \
            "to install %(link)s" % match.groupdict()
        install_requires.append("%(package)s==%(version)s" % match.groupdict())
        dependency_links.append(match.group('link'))
        continue

    if requirement.startswith("https"):
        install_requires.append(requirement)
        continue

    match = HTTPS_REQUIREMENT.match(requirement)
    if match:
        install_requires.append(
            "%(package)s>=%(version)s" % match.groupdict())
        dependency_links.append(match.group('link'))
        continue

    install_requires.append(requirement)

if major == 2:
    install_requires.extend(['matplotlib-venn>=0.5'])
                             
elif major == 3:
    pass

if major == 2 and minor1 < 5 or major < 2:
    raise SystemExit("""CGATReport requires Python 2.5 or later.""")

classifiers = """
Development Status :: 4 - Beta
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved
Programming Language :: Python
Topic :: Software Development
Topic :: Scientific/Engineering
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""

# collect CGATReport version
sys.path.insert(0, "CGATReport")
import version
version = version.__version__

# external dependencies
# R
# sqlite
# R - ggplot2
# R - RSqlite
# R - gplots (for r-heatmap)
# graphvis - for dependency graphs in documentation

setup(name='CGATReport',
      version=version,
      description='CGATReport : a report generator in python based on sphinx',
      author='Andreas Heger',
      author_email='andreas.heger@gmail.com',
      packages=find_packages(),
      package_dir={'CGATReport': 'CGATReport'},
      url="https://github.com/AndreasHeger/CGATReport/",
      package_data={'CGATReport': [
          './templates/*.*',
          './templates/Makefile',
          './templates/js/*',
          './images/*']},
      license="MIT",
      platforms=["any"],
      keywords="report generator sphinx matplotlib sql",
      long_description='CGATReport : a report generator in python based '
      'on sphinx',
      classifiers=[_f for _f in classifiers.split("\n") if _f],
      install_requires=install_requires,
      zip_safe=False,
      include_package_data=True,
      test_suite="tests",
      # python 3 conversion, requires distribute
      # use_2to3 = True,
      entry_points={
          'console_scripts': [
              'cgatreport-build = CGATReport.build:main',
              'cgatreport-clean = CGATReport.clean:main',
              'cgatreport-test = CGATReport.test:main',
              'cgatreport-quickstart = CGATReport.quickstart:main',
              'cgatreport-get = CGATReport.get:main',
              'cgatreport-profile = CGATReport.profile:main',
              'cgatreport-serve = CGATReport.serve:main',
          ],
          'distutils.commands': [
              'build_sphinx = cgatreport.setup_command:BuildDoc',
          ],
      },)

