########################################################################
########################################################################
## Import setuptools
## Use existing setuptools
try:
    from setuptools import setup, find_packages
except ImportError:
    ## try to get via ez_setup
    ## ez_setup did not work on all machines tested as
    ## it uses curl with https protocol, which is not
    ## enabled in ScientificLinux
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages

import glob, sys, os, re

major, minor1, minor2, s, tmp = sys.version_info

#####################################################################
#####################################################################
## Code to install dependencies from a repository
#####################################################################
## Modified from http://stackoverflow.com/a/9125399
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

REPO_REQUIREMENT = re.compile(r'^-e (?P<link>(?P<vcs>git|svn|hg|bzr).+#egg=(?P<package>.+)-(?P<version>\d(?:\.\d)*))$')
HTTPS_REQUIREMENT = re.compile(r'^-e (?P<link>.*).+#(?P<package>.+)-(?P<version>\d(?:\.\d)*)$')
install_requires = []
dependency_links = []

for requirement in (l.strip() for l in open('requires.txt') if not l.startswith("#")):
    match = REPO_REQUIREMENT.match(requirement)
    if match:
        assert which(match.group('vcs')) is not None, \
            "VCS '%(vcs)s' must be installed in order to install %(link)s" % match.groupdict()
        install_requires.append("%(package)s==%(version)s" % match.groupdict())
        dependency_links.append(match.group('link'))
        continue

    if requirement.startswith("https"):
        install_requires.append(requirement)
        continue

    match = HTTPS_REQUIREMENT.match(requirement)
    if match:
        install_requires.append("%(package)s>=%(version)s" % match.groupdict())
        dependency_links.append(match.group('link'))
        continue

    install_requires.append(requirement)

if major==2:
    install_requires.extend( [ 'web.py>=0.37',
                               'xlwt>=0.7.4', 
                               'matplotlib-venn>=0.5' ] )
elif major==3:
    pass

if major==2 and minor1<5 or major<2:
    raise SystemExit("""SphinxReport requires Python 2.5 or later.""")

classifiers="""
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

setup(name='SphinxReport',
      version='2.3',
      description='SphinxReport : a report generator in python based on Sphinx and matplotlib',
      author='Andreas Heger',
      author_email='andreas.heger@gmail.com',
      packages=find_packages(), #['SphinxReport'],
      package_dir = { 'SphinxReport': 'SphinxReport',
                      'SphinxReportPlugins' : 'SphinxReportPlugins'},
      url="http://code.google.com/p/sphinx-report/",
      scripts=[ 'scripts/sphinxreport-%s' % x 
                for x in ("build", "clean", "test", "quickstart", "gallery") ] ,
      package_data={'SphinxReport': ['./templates/*', './images/*']},
      license="BSD",
      platforms=["any",],
      keywords="report generator sphinx matplotlib sql",
      long_description='SphinxReport : a report generator in python based on Sphinx and matplotlib',
      classifiers = filter(None, classifiers.split("\n")),
      install_requires = install_requires,
      zip_safe = False,
      include_package_data = True,
      test_suite = "tests",
      # python 3 conversion, requires distribute
      # use_2to3 = True,

      entry_points = \
          {
              'console_scripts': [
            'sphinxreport-build = SphinxReport.build:main',
            'sphinxreport-clean = SphinxReport.clean:main',
            'sphinxreport-test = SphinxReport.test:main',
            'sphinxreport-quickstart = SphinxReport.quickstart:main',            
            'sphinxreport-get = SphinxReport.get:main',            
            'sphinxreport-profile = SphinxReport.profile:main',
            'sphinxreport-serve = SphinxReport.serve:main',            
            ],
              'distutils.commands': [
            'build_sphinx = sphinxreport.setup_command:BuildDoc',
            ],
              'SphinxReport.plugins': [
            'matplotlib=SphinxReportPlugins.MatplotlibPlugin:MatplotlibPlugin',
            'rplot=SphinxReportPlugins.RPlotPlugin:RPlotPlugin',
            'html=SphinxReportPlugins.HTMLPlugin:HTMLPlugin',
            'rst=SphinxReportPlugins.RSTPlugin:RSTPlugin',
            'xls=SphinxReportPlugins.XLSPlugin:XLSPlugin',
            'transform-stats=SphinxReportPlugins.Transformer:TransformerStats',
            'transform-correlation=SphinxReportPlugins.Transformer:TransformerCorrelationPearson',
            'transform-pearson=SphinxReportPlugins.Transformer:TransformerCorrelationPearson',
            'transform-contingency=SphinxReportPlugins.Transformer:TransformerContingency',
            'transform-spearman=SphinxReportPlugins.Transformer:TransformerCorrelationSpearman', 
            'transform-test-mwu=SphinxReportPlugins.Transformer:TransformerMannWhitneyU', 
            'transform-aggregate=SphinxReportPlugins.Transformer:TransformerAggregate',
            'transform-histogram=SphinxReportPlugins.Transformer:TransformerHistogram',
            'transform-tolabels=SphinxReportPlugins.Transformer:TransformerToLabels',
            'transform-filter=SphinxReportPlugins.Transformer:TransformerFilter',
            # 'transform-indicator=SphinxReportPlugins.Transformer:TransformerIndicator',
            'transform-select=SphinxReportPlugins.Transformer:TransformerSelect',
            'transform-group=SphinxReportPlugins.Transformer:TransformerGroup',
            'transform-combinations=SphinxReportPlugins.Transformer:TransformerCombinations',
            'transform-combine=SphinxReportPlugins.Transformer:TransformerCombinations',
            'transform-tolist=SphinxReportPlugins.Transformer:TransformerToList',
            'transform-toframe=SphinxReportPlugins.Transformer:TransformerToDataFrame',
            'transform-melt=SphinxReportPlugins.Transformer:TransformerMelt',
            'transform-count=SphinxReportPlugins.Transformer:TransformerCount',
            'transform-hypergeometric=SphinxReportPlugins.TransformersGeneLists:TransformerHypergeometric',
            # 'transform-label-paths=SphinxReportPlugins.TransformersGeneLists:TransformerPathToLabel',
            'transform-venn=SphinxReportPlugins.TransformersGeneLists:TransformerVenn',
            'transform-p-adjust=SphinxReportPlugins.TransformersGeneLists:TransformerMultiTest',
            'transform-odds-ratio=SphinxReportPlugins.TransformersGeneLists:TransformerOddsRatio',
            'render-user=SphinxReportPlugins.Renderer:User',
            'render-debug=SphinxReportPlugins.Renderer:Debug',
            'render-table=SphinxReportPlugins.Renderer:Table',
            'render-rsttable=SphinxReportPlugins.Renderer:RstTable',
            'render-matrix=SphinxReportPlugins.Renderer:TableMatrix',
            'render-matrixNP=SphinxReportPlugins.Renderer:NumpyMatrix',
            'render-glossary=SphinxReportPlugins.Renderer:Glossary',
            'render-status=SphinxReportPlugins.Renderer:Status',
            'render-line-plot=SphinxReportPlugins.Plotter:LinePlot',
            'render-density-plot=SphinxReportPlugins.Plotter:DensityPlot',
            'render-histogram-plot=SphinxReportPlugins.Plotter:HistogramPlot',
            'render-histogram-gradient-plot=SphinxReportPlugins.Plotter:HistogramGradientPlot',
            'render-pie-plot=SphinxReportPlugins.Plotter:PiePlot',
            'render-scatter-plot=SphinxReportPlugins.Plotter:ScatterPlot',
            'render-scatter-rainbow-plot=SphinxReportPlugins.Plotter:ScatterPlotWithColor',
            'render-matrix-plot=SphinxReportPlugins.Plotter:TableMatrixPlot',
            'render-matrixNP-plot=SphinxReportPlugins.Plotter:NumpyMatrixPlot',
            'render-hinton-plot=SphinxReportPlugins.Plotter:HintonPlot',
            'render-gallery-plot=SphinxReportPlugins.Plotter:GalleryPlot',
            'render-bar-plot=SphinxReportPlugins.Plotter:BarPlot',
            'render-stacked-bar-plot=SphinxReportPlugins.Plotter:StackedBarPlot',
            'render-interleaved-bar-plot=SphinxReportPlugins.Plotter:InterleavedBarPlot',
            'render-box-plot=SphinxReportPlugins.Plotter:BoxPlot',
            'render-violin-plot=SphinxReportPlugins.Plotter:ViolinPlot',
            'render-venn-plot=SphinxReportPlugins.Plotter:VennPlot',
            'render-ggplot=SphinxReportPlugins.GGPlotter:GGPlot',        
            'render-r-line-plot=SphinxReportPlugins.RPlotter:LinePlot',
            'render-r-box-plot=SphinxReportPlugins.RPlotter:BoxPlot',
            'render-r-smooth-scatter-plot=SphinxReportPlugins.RPlotter:SmoothScatterPlot',
            'render-r-heatmap-plot=SphinxReportPlugins.RPlotter:HeatmapPlot',        
            'render-r-ggplot=SphinxReportPlugins.RPlotter:GGPlot',        
            ]
            },
      )

# fix file permission for executables
# set to "group writeable" 
# also updates the "sphinx" permissions
import distutils.sysconfig, stat, glob
if sys.argv[0] == "install":
    print ("updating file permissions for scripts")
    for x in glob.glob( os.path.join(distutils.sysconfig.project_base, "sphinx*")):
        try:
            os.chmod( x, os.stat(x).st_mode | stat.S_IWGRP ) 
        except OSError:
            pass
