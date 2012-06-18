import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(name='CGATSphinxReportPlugins',
      version='1.0',
      description='SphinxReport : CGAT plugins',
      author='Andreas Heger',
      author_email='andreas.heger@gmail.com',
      packages=find_packages(),
      package_dir = { 'CGATSphinxReportPlugins': 'CGATSphinxReportPlugins' },
      keywords="report generator sphinx matplotlib sql",
      long_description='SphinxReport : CGAT plugins',
      entry_points = \
          {
              'SphinxReport.plugins': [
            'transform-count=CGATSphinxReportPlugins.CGATTransformer:TransformerCount',
            ]
              },
      )

