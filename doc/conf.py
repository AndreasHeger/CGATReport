
# -*- coding: utf-8 -*-
#
# Test documentation build configuration file, created by
# sphinx-quickstart on Mon Mar 23 15:27:57 2009.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

import sys, os

# add CGATReport config variables
import CGATReport.Utils

print CGATReport.Utils
PARAMS = CGATReport.Utils.get_parameters()

sys.exit(0)

# If extensions (or modules to document with autodoc) are in another
# directory, add these directories to sys.path here. If the directory
# is relative to the documentation root, use os.path.abspath to make
# it absolute, like shown here.
sys.path.extend( [os.path.join('..', 'CGATReport'), 
                  os.path.abspath('trackers'), 
                  os.path.abspath('.') ] )


# The cachedir holding the data from the Trackers. If not defined, no
# cache will be used.
cgatreport_cachedir=os.path.abspath("_cache")

# urls to include within the annotation of an image
cgatreport_urls=("code", "rst", "data")

# The Database backend. Possible values are mysql, psql and sqlite
cgatreport_sql_backend="sqlite:///%s/csvdb" % os.path.abspath(".")

# add errors into the document
cgatreport_show_errors = True

# add warnings into the document
cgatreport_show_warnings = True

# static images to create for each plot
# a tuple of (id, format, dpi).
cgatreport_images=(("hires", "hires.png", 200),
                   # ( "eps", "eps", 50 ),
                   ("svg", "svg", 50 ))

# -- General configuration ---------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
    'sphinx.ext.pngmath',
    'sphinx.ext.ifconfig',
    'sphinx.ext.todo',
    'CGATReport.only_directives',
    'CGATReport.roles',
    'CGATReport.errors_directive',
    'CGATReport.warnings_directive',
    'CGATReport.report_directive']

# inheritance_diagram broken in python3
if sys.version_info[0] == 2:
    extensions.append('sphinx.ext.inheritance_diagram')

# Included at the end of each rst file
rst_epilog='''
.. _CGAT Training Programme: http://www.cgat.org
.. _python: http://python.org
.. _pysam: http://code.google.com/p/pysam/
.. _samtools: http://samtools.sourceforge.net/
.. _tabix: http://samtools.sourceforge.net/tabix.shtml/
.. _Galaxy: https://main.g2.bx.psu.edu/
.. _numpy: http://www.numpy.org/
.. _cython: http://cython.org/
.. _pyximport: http://www.prescod.net/pyximport/
.. _sphinx: http://sphinx-doc.org/
.. _ruffus: http://www.ruffus.org.uk/
.. _cgatreport: http://code.google.com/p/sphinx-report/
.. _sqlite: http://www.sqlite.org/
.. _make: http://www.gnu.org/software/make
.. _UCSC: http://genome.ucsc.edu
.. _mysql: https://mariadb.org/
.. _postgres: http://www.postgresql.org/
.. _bedtools: http://bedtools.readthedocs.org/en/latest/
.. _UCSC Tools: http://genome.ucsc.edu/admin/git.html
.. _seaborn: https://github.com/mwaskom/seaborn
.. _ggplot: https://github.com/yhat/ggplot/
.. _ggplot2: http://ggplot2.org/
.. _rpy2: http://rpy.sourceforge.net/rpy2.html
.. _pandas: http://pandas.pydata.org/
.. _ipython: http://ipython.org/
.. _jssor: http://www.jssor.com/
'''

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The encoding of source files.
#source_encoding = 'utf-8'

# The master toctree document.
master_doc = 'contents'

# General information about the project.
project = u'CGATReport'
copyright = u'2009, Andreas Heger'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = '1.0'
# The full version, including alpha/beta/rc tags.
release = '1.0a2'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['_build']

# The reST default role (used for this markup: `text`) to use for all documents.
#default_role = None

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# A list of ignored prefixes for module index sorting.
#modindex_common_prefix = []

# If true, include todo list
todo_include_todos = True

# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = 'cgat'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ["."]

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
html_logo = '_templates/CGATReport.png'

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
html_additional_pages = { 'index' : 'index.html', } 
                          # 'gallery' : 'gallery.html' }

# If false, no module index is generated.
#html_use_modindex = True

# If false, no index is generated.
#html_use_index = True

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = 'Testdoc'


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [
  ('contents', 
   'Test.tex', 
   r'Test Documentation',
   r'Andreas Heger', 
   'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True
