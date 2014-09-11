.. _Overview:

********
Overview
********

This section explains the main features of cgatreport and demonstrates its usage.

.. _Features:

Features
********

cgatreport is a report generator that is implemented as an extension
to cgatreport`Sphinx`. It is easy to use and powerful enough to give all the flexibility 
needed during the development of computational pipelines and robustness during the
production use of a pipeline.

It is intended for developers and computational scientists with ``python`` scripting experience.

Briefly, the cgatreport is a report generator that is implemented as an extension
to cgatreport`Sphinx`. It

* uses simple markup in the form of restructured text
* supports both automated and narrative analysis
* keeps code and annotation together
* takes care of indexing, formatting to produce something pretty
* produces static html and pdf
* provides the power of python within text

Usage
*****

You can think of cgatreport as providing a
*macro* ability to restructured text documents. These macros will be evaluated every time a restructured text
document is rebuilt.

Macros are added into restructured text documents via the ``:report:``
directive. The ``:report:`` directive has two components. Firstly, there
is a data source (or :term:`tracker`) that provides data. Secondly,
there is a :term:`renderer`, a method to display the data provided by the :term:`tracker`.

Data sources are provided by the user and implemented as python classes
(more specifically, as objects derived of subclasses of the class
:class:`Tracker`). As data sources are implemented by the user,
almost any type of data source can be used: flat files, SQL database,
etc. Data could even be obtained remotely. cgatreport
provides some utility functions for interaction with SQL databases.

cgatreport comes with a collection of pre-defined renderers
covering most basic and common plotting needs.

The following minimal example illustrates how cgatreport
works. On inserting a ``:report:`` directive like the following into a
restructured text document::

   .. report:: Trackers.BarData
      :render: bar-plot

      A bar plot.

will insert a barplot (:class:`CGATReportPlugins.Renderer.BarPlot`) at 
the current location. The :term:`renderer` will obtain the data from a
python class or function called *BarData* in the python module 
:file:`Trackers.py` that should be somewhere in the python search path 
(see :ref:`Configuration`).

The :file:`Trackers.py` should contain a function *BarData*, that might look like this::

   def BarData():
      return dict([("bar1", 20), ("bar2", 10)])

Instead of plain functions, function objects can be used as well. 

Finally, the document is built using the usual cgatreport`Sphinx` process::

   sphinx-build -b html -d _build/doctrees   . _build/html

The resultant-plot is here:

.. report:: Trackers.BarData
   :render: bar-plot

   A bar plot

Of course, the same data could be displayed differently::

   .. report:: Trackers.BarData
      :render: bar-plot

.. report:: Trackers.BarData
   :render: pie-plot

   A pie plot

.. _History:

History
**********

Scientific datasets these days are large and are usually processed by
computational pipelines creating a wealth of derived data, very often 
stored in a database. With computational power always increasing, 
the bottleneck is usually the subsequent analysis. 

Especially during code development and in the early exploratory stages, the data 
are sliced and plotted in multiple ways to find problems and understand the data. 
At the same time, the plots and tables are embedded into text with comments and 
notes that should later result in a publication. As bugs are fixed and the data 
are understood better, the plots and tables need to be frequently updated. Statically
copying and pasting images into a document becomes tedious quickly.

The interactive analysis is later followed by re-runs of the pipeline
on different data sets or with different parameters. Again the data is sliced
and plotted, this time to confirm the successful completion of the pipeline
and to compare results to those of previous runs. This is a mostly automatic
task, in which diagnostic plots are created to provide a high-level view
of the results. There is also an interactive component, where plots are 
selected to highlight unexpected deviations that are the bread-and-butter of science.

We found no tool that easily bridges the divide of interactive analysis and
automation. On one end of the spectrum is office software with macros
or embedded images linked to physical files. Writing in office software is easy, 
there is drag & drop and the result is very close to the desired product: a
publishable manuscript. However, with complicated analyses the macros become 
unwieldy. Images on the hard-disc separate the code to create the images from 
the document and there is always the danger of links being broken. Taking a live
document and applying it to a new dataset is difficult.

At the other end of the spectrum are full-fledged content management systems
that provide dynamic access to the data. These have a steep learning curve and
require a lot of work to build and maintain. Some design is necessary beforehand
to prevent uncontrolled growth. Unfortunately this is usually at odds with
our experience how computational pipelines in science develop. Such effort is 
usually only justifyable for large pipelines, big projects and big teams.

Somewhere in the middle of the spectrum are report generators. These create 
static documents, but are designed to be run often and on different datasets. 
These are powerful, but often have a steep learning curve. We also found them
lacking in plotting capabilities. 

We thought the combination of cgatreport``Sphinx`` and :mod:``matplotlib``
and ideal combination and extended the ``matplotlib`` ``:plot:`` directive
to interactively collect data. We are heavily indebted to these two
projects. 

.. seealso::

   Sphinx: 
      http://sphinx.pocoo.org

   Matplotlib:
      http://matplotlib.sourceforge.net

   Python:
      http://www.python.org

   A restructured text quick reference: 
      http://docutils.sourceforge.net/docs/user/rst/quickref.html






