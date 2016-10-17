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
    install_requires.extend(['web.py>=0.37',
                             'xlwt>=0.7.4',
                             'matplotlib-venn>=0.5'])
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

# external dependencies
# R
# sqlite
# R - ggplot2
# R - RSqlite
# R - gplots (for r-heatmap)
# graphvis - for dependency graphs in documentation

setup(name='CGATReport',
      version='0.5.0',
      description='CGATReport : a report generator in python based on sphinx',
      author='Andreas Heger',
      author_email='andreas.heger@gmail.com',
      packages=find_packages(),
      package_dir={'CGATReport': 'CGATReport',
                   'CGATReportPlugins': 'CGATReportPlugins'},
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
          'CGATReport.plugins': [
              'matplotlib='
              'CGATReportPlugins.MatplotlibPlugin:MatplotlibPlugin',
              'rplot='
              'CGATReportPlugins.RPlotPlugin:RPlotPlugin',
              'html='
              'CGATReportPlugins.HTMLPlugin:HTMLPlugin',
              'rst='
              'CGATReportPlugins.RSTPlugin:RSTPlugin',
              'xls='
              'CGATReportPlugins.XLSPlugin:XLSPlugin',
              'bokeh='
              'CGATReportPlugins.BokehPlugin:BokehPlugin',
              'transform-stats=CGATReportPlugins.Transformer:TransformerStats',
              'transform-correlation='
              'CGATReportPlugins.Transformer:TransformerCorrelationPearson',
              'transform-pearson='
              'CGATReportPlugins.Transformer:TransformerCorrelationPearson',
              'transform-contingency='
              'CGATReportPlugins.Transformer:TransformerContingency',
              'transform-spearman='
              'CGATReportPlugins.Transformer:TransformerCorrelationSpearman', 
              'transform-test-mwu='
              'CGATReportPlugins.Transformer:TransformerMannWhitneyU', 
              'transform-aggregate='
              'CGATReportPlugins.Transformer:TransformerAggregate',
              'transform-histogram='
              'CGATReportPlugins.Transformer:TransformerHistogram',
              'transform-histogram-stats='
              'CGATReportPlugins.Transformer:TransformerHistogramStats',
              # 'transform-tolabels=CGATReportPlugins.Transformer:TransformerToLabels',
              'transform-filter='
              'CGATReportPlugins.Transformer:TransformerFilter',
              # 'transform-indicator=CGATReportPlugins.Transformer:TransformerIndicator',
              # 'transform-select=CGATReportPlugins.Transformer:TransformerSelect',
              # 'transform-swop=CGATReportPlugins.Transformer:TransformerSwop',
              # 'transform-group=CGATReportPlugins.Transformer:TransformerGroup',
              # 'transform-combinations=CGATReportPlugins.Transformer:TransformerCombinations',
              # 'transform-combine=CGATReportPlugins.Transformer:TransformerCombinations',
              # 'transform-tolist=CGATReportPlugins.Transformer:TransformerToList',
              # 'transform-toframe=CGATReportPlugins.Transformer:TransformerToDataFrame',
              'transform-pandas='
              'CGATReportPlugins.Transformer:TransformerPandas',
              'transform-melt='
              'CGATReportPlugins.Transformer:TransformerMelt',
              'transform-pivot='
              'CGATReportPlugins.Transformer:TransformerPivot',
              # 'transform-count='
              # 'CGATReportPlugins.Transformer:TransformerCount',
              'transform-hypergeometric='
              'CGATReportPlugins.TransformersGeneLists:TransformerHypergeometric',
              # 'transform-label-paths='
              # 'CGATReportPlugins.TransformersGeneLists:TransformerPathToLabel',
              'transform-venn=CGATReportPlugins.TransformersGeneLists:TransformerVenn',
              'transform-p-adjust='
              'CGATReportPlugins.TransformersGeneLists:TransformerMultiTest',
              'transform-odds-ratio='
              'CGATReportPlugins.TransformersGeneLists:TransformerOddsRatio',
              'render-user='
              'CGATReportPlugins.Renderer:User',
              'render-debug='
              'CGATReportPlugins.Renderer:Debug',
              'render-dataframe='
              'CGATReportPlugins.Renderer:DataFrame',
              'render-table='
              'CGATReportPlugins.Renderer:Table',
              'render-rst-table='
              'CGATReportPlugins.Renderer:RstTable',
              'render-xls-table='
              'CGATReportPlugins.Renderer:XlsTable',
              'render-html-table='
              'CGATReportPlugins.Renderer:HTMLTable',
              'render-glossary-table='
              'CGATReportPlugins.Renderer:GlossaryTable',
              'render-matrix='
              'CGATReportPlugins.Renderer:TableMatrix',
              'render-matrixNP='
              'CGATReportPlugins.Renderer:NumpyMatrix',
              'render-status='
              'CGATReportPlugins.Renderer:Status',
              'render-status-matrix='
              'CGATReportPlugins.Renderer:StatusMatrix',
              'render-line-plot='
              'CGATReportPlugins.Plotter:LinePlot',
              # for backwards compatibility
              'render-density-plot='
              'CGATReportPlugins.Seaborn:KdePlot',
              'render-histogram-plot='
              'CGATReportPlugins.Plotter:HistogramPlot',
              # 'render-histogram-gradient-plot='
              # 'CGATReportPlugins.Plotter:HistogramGradientPlot',
              'render-pie-plot='
              'CGATReportPlugins.Plotter:PiePlot',
              'render-scatter-plot=CGATReportPlugins.Plotter:ScatterPlot',
              'render-scatter-rainbow-plot='
              'CGATReportPlugins.Plotter:ScatterPlotWithColor',
              'render-matrix-plot='
              'CGATReportPlugins.Plotter:TableMatrixPlot',
              'render-matrixNP-plot='
              'CGATReportPlugins.Plotter:NumpyMatrixPlot',
              'render-hinton-plot='
              'CGATReportPlugins.Plotter:HintonPlot',
              'render-gallery-plot='
              'CGATReportPlugins.Plotter:GalleryPlot',
              'render-slideshow-plot='
              'CGATReportPlugins.SlideShow:SlideShowPlot',
              'render-bar-plot='
              'CGATReportPlugins.Plotter:BarPlot',
              'render-stacked-bar-plot='
              'CGATReportPlugins.Plotter:StackedBarPlot',
              'render-interleaved-bar-plot='
              'CGATReportPlugins.Plotter:InterleavedBarPlot',
              'render-venn-plot='
              'CGATReportPlugins.Plotter:VennPlot',
              # ggplot
              'render-ggplot='
              'CGATReportPlugins.GGPlotter:GGPlot',
              # pandas plotting
              'render-pdplot='
              'CGATReportPlugins.PandasPlotter:PandasPlot',
              # seaborn plots
              'render-sb-box-plot='
              'CGATReportPlugins.Seaborn:BoxPlot',
              'render-sb-violin-plot='
              'CGATReportPlugins.Seaborn:ViolinPlot',
              'render-sb-kde-plot='
              'CGATReportPlugins.Seaborn:KdePlot',
              'render-sb-pair-plot='
              'CGATReportPlugins.Seaborn:PairPlot',
              'render-sb-dist-plot='
              'CGATReportPlugins.Seaborn:DistPlot',
              'render-sb-heatmap-plot='
              'CGATReportPlugins.Seaborn:HeatmapPlot',
              'render-sb-clustermap-plot='
              'CGATReportPlugins.Seaborn:ClustermapPlot',
              # R plots
              'render-r-line-plot='
              'CGATReportPlugins.RPlotter:LinePlot',
              'render-r-box-plot='
              'CGATReportPlugins.RPlotter:BoxPlot',
              'render-r-smooth-scatter-plot='
              'CGATReportPlugins.RPlotter:SmoothScatterPlot',
              'render-r-heatmap-plot='
              'CGATReportPlugins.RPlotter:HeatmapPlot',
              'render-r-ggplot='
              'CGATReportPlugins.RPlotter:GGPlot',
              # Bokeh plots
              'render-b-line-plot='
              'CGATReportPlugins.BokehPlotter:LinePlot',
              # backwards compatibility
              'render-box-plot='
              'CGATReportPlugins.Seaborn:BoxPlot',
              'render-violin-plot='
              'CGATReportPlugins.Seaborn:ViolinPlot',
          ]
      },)

# fix file permission for executables
# set to "group writeable"
# also updates the "sphinx" permissions
if "install" in sys.argv:
    print ("updating file permissions for scripts")
    file_glob = os.path.join(
        distutils.sysconfig.project_base,
        "cgatreport-*")
    for x in glob.glob(file_glob):
        try:
            os.chmod(x, os.stat(x).st_mode | stat.S_IWGRP)
        except OSError:
            pass

    # replace the hardcoded python with /bin/env python. This
    # allows using the install within a virtual environment.
    print ("setting python to /bin/env python")
    statement = 'perl -p -i -e "s/\/ifs\/apps\/apps\/python-2.7.1\/bin\/python2.7/\/bin\/env python/" ' + file_glob
    print(statement)
    subprocess.call(statement, shell=True)
        
