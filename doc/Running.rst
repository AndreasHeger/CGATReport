.. _Running:

=================
Building reports
=================

Building a restructured text document that includes the :term:`report`
directive is an iterative process that involves usually the following
steps:

0. Setting up a new cgatreport project using
   :ref:`cgatreport-quickstart`.

1. Writing some text and realizing that you need to add a figure to
   support the text.

2. Adding the python code for the :term:`tracker` as a data source
   that provides the data for the figure.

3. Testing the :term:`tracker` and customizing the plot using
   :ref:`cgatreport-test`.

4. Inserting the :term:`report` directive into the text.

5. Optionally, removing existing cached data of this :term:`tracker`
   using :ref:`cgatreport-clean`.

6. Building the full document using :ref:`cgatreport-build` or the
   :ref:`Makefile`.

Steps 1-6 are repeated until the document is finished.

CGATReport provides utilities to assisst in this process.

Command line utilities
======================

This page explains the various utilities that come with cgatreport. See :ref:`Utilities`
for the complete documentation.

.. _cgatreport-quickstart:

cgatreport-quickstart
-----------------------

The :ref:`cgatreport-quickstart` utility sets up a cgatreport`cgatreport`
project. It is called as::

   cgatreport-quickstart -d new_project

.. _makefile:

Amongst other files, this utility will create a makefile in the
project directory. The makefile contains some useful commands for
controlling the build process. Type::

   make help

for a list of all commands available.

.. _cgatreport-build:

cgatreport-build
------------------

At its simplest, cgatreport is a :mod:`Sphinx` extension
and all images are simply built using the usual cgatreport`Sphinx` build.
See the `Sphinx documentation <http://sphinx.pocoo.org/intro.html#running-a-build>`
on how to running sphinx.

However, rendering many images and extracting data takes time. The :ref:`cgatreport-build`
utility can speed up this process by running several rendering processes in parallel.
Note that :ref:`Caching` needs to be enabled for this to work. It also takes care of 
building the :ref:`Gallery`. It is invoked as a prefix to the :file:`sphinx-build`
command, for example::
   
   cgatreport-build --num-jobs=4 sphinx-build -b html -d _build/doctrees   . _build/html

will use 4 processors in parallel to create all images before calling
``sphinx-build`` to build the document.

.. _cgatreport-clean:

cgatreport-clean
------------------

The :ref:`cgatreport-clean` utility removes files from a previous build. It is called as::

   cgatreport-clean [target [[tracker] ...]

Where *target* can be one of 

**clean**
   Remove the latest rendered documents, but leaves cached data.

**distclean**
   Remove all build information including cached data.

**<tracker>**
   The name of a :class:`Tracker`. All images, cached data and text elements based
   on this tracker are removed so that they will be re-build during the 
   next build. Multiple trackers can be named on the command line.

.. _cgatreport-test:

cgatreport-test
-----------------

The :ref:`cgatreport-test` utility presents previews of graphs and tables. It
can also generate template restructured text for cutting and pasting into a 
document. It is very useful for debugging trackers and tweaking parameters in order
to build the desired plot.

:ref:`cgatreport-test` is called as::

   cgatreport-test [options] [tracker] [renderer]

The following example shows how an interactive session
develops. First, we start by printing debugging summary for the
:class:`Tracker` ``SingleColumnDataExample``, to see if all is as
expected::

   cgatreport-test -t SingleColumnDataExample -r debug

The :ref:`debug` Renderer displays the data as it is returned from the
:term:`Tracker` as a nested dictionary. To see the :term:`dataframe`
that is built, use::

   cgatreport-test -t SingleColumnDataExample -r dataframe

The following command will compute stats and output a table::

   cgatreport-test -t SingleColumnDataExample -r table -m stats

The following command will group the tables by track and not by slice::

   cgatreport-test -t SingleColumnDataExample -r table -m stats -o groupby="track"

In the end, we decide to rather plot the data. The following command will compute 
a histogram and plot as a line-plot::

   cgatreport-test -t SingleColumnDataExample -r line-plot -m histogram

However, we prefer a cumulative histogram and rendering without bullets::

   cgatreport-test -t SingleColumnDataExample -r line-plot -m histogram -o tf-aggregate=cumulative -o as-lines

Interactive data exploration
++++++++++++++++++++++++++++

In interactive data exploration, data is only collected but not
rendered. Using the ``--start-interpreter`` or ``-start-iptyhon`` option, 
:ref:`cgatreport-test` will exit and automatically start up the
interpreter. For example::

   cgatreport-test -t SingleColumnDataExample -r line-plot -m histogram -i

will bring up the python interpreter. The data is available in the
``result`` object::
    
   >>>> print result
   OrderedDict([('track1', OrderedDict([('slice1', OrderedDict([('data',
   OrderedDict([('data', array([  0. ,   0.2,   0.4,   0.6,   0.8,   1. ,
   1.2,   1.4,   1.6,
   1.8,   2. ,   2.2,   2.4,   2.6,   2.8,   3. ,   3.2,   3.4,
   3.6,   3.8,   4. ,   4.2,   4.4,   4.6,   4.8,   5. ,   5.2,
   ...

:ref:`cgatreport-test` will also load any dataframes into the R
environment, load rpy2 and provide a short-cut to the R
interpreter. For example::

   cgatreport-test -r line-plot -t ExpressionLevels --ii

will provide the ``all`` object inside R within an ipython_ shell. For
example, to plot the data with ggplot, type::

   R('''x=ggplot( all, aes(x=experiment1, y=experiment2, color=factor(gene_function))) + geom_point()''')
   R('''plot(x)''')

After optimizing the plot, the resultant ggplot command can be used
with the :ref:`r-ggplot` renderer.

To do the same using the `rmagic
<http://ipython.org/ipython-doc/dev/config/extensions/rmagic.html>`_,
extension to ipython, type::

   %load_ext rmagic
   %R y=ggplot( all, aes(x=experiment1, y=experiment2, color=factor(gene_function))) + geom_point()
   R('''plot(y)''')

Please note that the last command to plot the graph should use the rpy2 interface
directly, as the notebook plots with to a png device by default and
thus the plot will not be visible.

:ref:`cgatreport-test` will also interact within an ipython_
notebook. To use this feature, use the ``--language`` option::

   cgatreport-test -r line-plot -t ExpressionLevels --language=notebook

The command will provide the following snippet to paste into an ipython
notebook::

   import os
   os.chdir('/ifs/devel/sphinx-report/doc')
   import CGATReport.test
   args = "-r none -t ExpressionLevels ".split(" ")
   result = CGATReport.test.main( args )
   %load_ext rmagic

The data are now available in the python variable ``result`` or in the
R variable ``all``. For example, to plot with ggplot, type the
following into the next workbook cell::

   %R y=ggplot( all, aes(x=experiment1, y=experiment2, color=factor(gene_function))) + geom_point()
   %R plot(y)

The benefit of this approach is that the data source is available
as a tracker for automated report generation, while a plot can
be developed interactively and later incorporated with the
:ref:`r-ggplot` renderer.

Note that this requires that the notebook is running on the same
server on which :ref:`cgatreport-test` was executed.

.. _Debugging:

Debugging
=========

Information and debugging messages from to the ``report`` directive are
written to the file :file:`cgatreport.log` in the current directory.

To examine data that a tracker has stored in a cache you can use
the :ref:`cgatreport-get` command. It is called as::

   cgatreport-get [options] tracker

For example, to output the data in the cache hold for the tracker
``Tracker.LabeledDataExample`` as comma separated values, type::

   cgatreport-get --format=csv Trackers-LabeledDataExample

.. _Caching:

Caching
=======

Extracting data from a database potentially takes much time if a lot
of processing is involved or the data set is large. To speed up the
writing process cgatreport is able to cache function calls to a
:term:`Tracker` if the configuration variable ``cgatreport_cachedir``
is set, for example to::

   cgatreport_cachedir=os.path.abspath("_cache")

Enabling caching will speed up the build process considerably, in
particular as :ref:`cgatreport-build` can make use of parallel data
gathering and plotting.  Unfortunately currently there is no
:ref:`Dependency` checking for cached data.  Thus, changes in the code
of a :term:`Tracker` or changes in the data will not result in an
automatic update of the cache. The best solution is to manually delete
the cached data using the command :ref:`cgatreport-clean`.

.. _Dependency:

Dependency checking
===================

cgatreport`Sphinx` implements dependency checking such that existing
documents are only rebuilt if the underlying sources have changed. The
same dependency checking is still available in cgatreport, however
currently there is no dependency checking between the data source and
an existing image. As long as an image or table is present on the file
system, it will not be re-rendered even if the document or the
underlying data has changed. To force re-rendering, use the command
:ref:`cgatreport-clean`.

.. _BuildDirecotry:

Using a build directory
=======================

It is good practice to keep the development of the report from the
actual report itself. CGATReport and Sphinx do support building using
a build directory.

For example, assume your code is in directory :file:`./code` and you
want to build in the directory :file:`./build`. In the :file:`build`
directory create a :file:`conf.py` and :ref:`Makefile`.

Apply the following modifications to point them to the source
directory:

1. Update the relative path to the Trackers to *sys.path*. For example, add::

      sys.path.append( "../code" )

2. Point the *templates_path* variable in the html section to the :file:`code` directory::

      templates_path = ['../code/_templates']

3. Update :file:`Makefile` and add ``-c . ../source`` to the command line.

