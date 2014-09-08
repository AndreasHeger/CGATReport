=============
CGATReport
=============

CGATReport is a report generator that is implemented as an extension
to sphinx_.

Its purpose is to facilitate writing scientific reports interpreting
large and changing datasets. It is designed to assist the iterative
analysis during the development of a computational scientific pipeline
as understanding of the data grows.  Once the pipeline settles down,
CGATReport permits an easy transition towards the automatic report
generation needed when the pipeline is run on new data sets.

CGATReport is easy to use and powerful enough to give all the
flexibility needed during the development of computational pipelines
and robustness during the production use of a pipeline.  It is
intended for developers and computational scientists with python_
scripting experience.

CGATReport comes with all the batteries included thanks to python_
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

Documentation is available
`here <https://www.cgat.org/downloads/public/CGATReport/documentation>`_.

Some quick links are below:

* `Contents <https://www.cgat.org/downloads/public/CGATReport/documentation/contents.html>`_
* `Tutorials <https://www.cgat.org/downloads/public/CGATReport/documentation/Tutorials.html>`_
* `Reference <https://www.cgat.org/downloads/public/CGATReport/documentation/Reference.html>`_

Installation
============

CGATReport is available on pypi_, to install, type::

    pip install CGATReport

CGATReport is under active development, the lastest development
snapshot can be found ot github_::

   git clone git@github.com:AndreasHeger/CGATReport.git

.. _ipython: http://ipython.org/notebook.html
.. _python: http://www.python.org
.. _pypi: http://pypi.python.org/pypi/CGATReport
.. _github: https://github.com/AndreasHeger/CGATReport
.. _restructured text: http://docutils.sourceforge.net/rst.html
.. _sphinx: http://sphinx-doc.org/
