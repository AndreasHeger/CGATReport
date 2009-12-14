import ez_setup
ez_setup.use_setuptools()

import glob, sys, os
# from distutils.core import setup

from setuptools import setup, find_packages

major, minor1, minor2, s, tmp = sys.version_info

if major==2 and minor1<5 or major<2:
    raise SystemExit("""SphinxReport requires Python 2.5 or later.""")

classifiers="""
Development Status :: 3 - Alpha
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

setup(name='SphinxReport',
      version='1.0.a3',
      description='SphinxReport : a report generator in python based on Sphinx and matplotlib',
      author='Andreas Heger',
      author_email='andreas.heger@gmail.com',
      packages=find_packages(), #['SphinxReport'],
      package_dir = { 'SphinxReport': 'SphinxReport'},
      url="http://code.google.com/p/sphinx-report/",
      scripts=[ 'scripts/sphinxreport-%s' % x for x in ("build", "clean", "test", "quickstart", "gallery") ] ,
      package_data={'SphinxReport': ['./templates/*']},
      license="BSD",
      platforms=["any",],
      keywords="report generator sphinx matplotlib sql",
      long_description='SphinxReport : a report generator in python based on Sphinx and matplotlib',
      classifiers = filter(None, classifiers.split("\n")),
      install_requires = ['sphinx>=0.5-1', "matplotlib>=0.98.1", "sqlalchemy>=0.4.8" ],
      zip_safe = False,
      include_package_data = True,
      entry_points={
            'console_scripts': [
            'sphinxreport-build = SphinxReport.build:main',
            'sphinxreport-clean = SphinxReport.clean:main',
            'sphinxreport-test = SphinxReport.test:main',
            'sphinxreport-quickstart = SphinxReport.quickstart:main',            
        ],
        'distutils.commands': [
            'build_sphinx = sphinxreport.setup_command:BuildDoc',
        ],
    },
      )

# fix file permission for executables
# set to "group writeable" 
# also updates the "sphinx" permissions
import distutils.sysconfig, stat, glob
print "updating file permissions for scripts"
for x in glob.glob( os.path.join(distutils.sysconfig.project_base, "sphinx*")):
    os.chmod( x, os.stat(x).st_mode | stat.S_IWGRP ) 
