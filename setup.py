import glob
from distutils.core import setup

setup(name='SphinxReport',
      version='0.1a',
      description='Sphinx Report Extension',
      author='Andreas Heger',
      author_email='andreas.heger@gmail.com',
      packages=[ 'SphinxReport' ],
      package_dir = { 'SphinxReport': 'lib'},
      scripts=[ 'scripts/sphinxreport-%s' % x for x in ("build", "clean", "test", "quickstart", "gallery") ] ,
      package_data={'SphinxReport': ['./templates/*']},
      )
