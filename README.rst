=============
sphinx-report
=============

!sphinx-report is a report generator that is implemented as an extension
to <a href="http://sphinx.pocoo.org/">Sphinx</a>.

Its purpose is to facilitate writing scientific reports interpreting
large and changing datasets. It is designed to assist the iterative
analysis during the development of a computational scientific pipeline
as understanding of the data grows.  Once the pipeline settles down,
!sphinx-report permits an easy transition towards the automatic report
generation needed when the pipeline is run on new data sets.

!sphinx-report is easy to use and powerful enough to give all the
flexibility needed during the development of computational pipelines
and robustness during the production use of a pipeline.  It is
intended for developers and computational scientists with python_
scripting experience.

!sphinx-report comes with all the batteries included thanks to python_
and sphinx_, in particular, it

  * uses simple markup in the form of `restructured text`_,
  * supports both automated and narrative analysis,
  * keeps code, data and text together,
  * takes care of indexing and formatting to produce something
    presentable,
  * links with ipython_ notebooks
  * produces static html, latex, ps and pdf.

Documentation
================

  * Contents
     * <a href="http://www.cgat.org/~andreas/documentation/sphinx-report/index.html">Contents</a>
  * search the documentation
     * <a href="http://www.cgat.org/~andreas/documentation/sphinx-report/search.html">Search Page</a>
  * all functions, classes, terms
     * <a href="http://www.cgat.org/~andreas/documentation/sphinx-report/genindex.html">General Index</a>
  * quick access to all documented modules
     * <a href="http://www.cgat.org/~andreas/documentation/sphinx-report/modindex.html">Module Index</a>

Installation
============

!sphinx-report is available on pypi_, to install, type::

    pip install sphinx-report

!sphinx-report is under active development, the lastest development
snapshot can be found ot github_::

   git clone git@github.com:AndreasHeger/sphinx-report.git

.. _ipython: http://ipython.org/notebook.html
.. _python: http://www.python.org
.. _pypi: http://pypi.python.org/pypi/sphinx-report
.. _github: https://github.com/AndreasHeger/sphinx-report
.. _restructured text: http://docutils.sourceforge.net/rst.html
