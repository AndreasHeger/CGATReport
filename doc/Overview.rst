.. _Overwiew:

********
Overview
********

The :mod:`SphinxReport` module is an extension for :mod:`sphinx`
that provides facilities for data retrieval and data rendering
within reStructured text. 

.. _Features:

Features
********

:mod:`SphinxReport` is a report generator that is implemented as an extension
to :mod:`Sphinx`. It is easy to use and powerful enough to give all the flexibility 
needed during the development of computational pipelines and robustness during the
production use of a pipeline.

It is intended for developers and computational scientists with ``python`` scripting experience.

Briefly, the :mod:`SphinxReport` is a report generator that is implemented as an extension
to :mod:`Sphinx`. It

* uses simple markup in the form of restructured text
* supports both automated and narrative analysis
* keeps code and annotation together
* takes care of indexing, formatting to produce something pretty
* produces static html and pdf
* provides the power of python within text

Usage
*****

Three steps are required to include rendered images into restructured text
using :mod:`SphinxReport`:

1. Provide a data source. Data are provided by objects of the type :class:`Tracker`. The data can be obtained from
   data sources like flat files, SQL tables and more. Trackers provide data by :term:`track` and :term:`slice`. 
   Tracks are principal collections of data, for example data measurements taken from different species. Slices 
   are subsections of the data. For example, a :class:`Tracker` might provide *weight* measurements of different species
   according to the slice *gender*.

2. Insert a ``report`` directive into a restructered text document. ``:report:`` directives invoke
   objects of the type :class:`Renderer`. These are provided by the :mod:`SphinxReport` extension 
   and are used to display data as graphs or tables. 

3. Run :file:``sphinxreport-build`` to build the document. 

The following minimal example illustrates how this process works. A ``:report:`` directive like::

   .. report:: Trackers.BarData
      :render: bars

will insert a barplot (:class:`RendererInterleavedBars`) at the current location. The Renderer will 
obtain the data from a python class or function *BarData* in the file
:file:`Trackers.py` that should be somewhere in the python search path (see :ref:`Configuration`).
The :file:`Trackers.py` should contain a function *BarData*, that might look like this::

   def BarData( track, slice = None ): return dict( [("bar1", 10), ("bar2", 20)] )

Instead of plain functions, function objects can be used as well. 

Finally, the document is built using the usual :mod:`Sphinx` process::

   sphinx-build -b html -d _build/doctrees   . _build/html

The :mod:`SphinxReport` module comes with additional utilities for to aid debugging
and the building of large documents. 

See the :ref:`Tutorials` for a more complete introduction on how to use the extension. 
See :ref:`Running` on more advanced building methods.

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
automatic updating. On one end of the spectrum is office software with macros
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

We thought the combination of :mod:``Sphinx`` and :mod:``matplotlib``
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






