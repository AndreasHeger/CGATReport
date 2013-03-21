.. _Background:

==========
Background
==========

This section introduces the concepts of sphinxreport. This section is required reading in
order to be able to use sphinxreport effectively.

To create dynamic figures, sphinxreport requires two components, a :term:`tracker` and 
a :term:`renderer`. A :term:`tracker` provides data. Trackers are written by the user and are project specific. 

Renderers take data and render them within a report. A renderer might create one or several
plots, some text, a table or some combination of these. sphinxreport provides a collection of renderers 
for the most commont plotting needs (see :ref:`Renderers`). Additional renderers can be added
as plugins (see :ref:`Extending sphinxReport``).

There is an optional third component, a :term:`transformer`, that can be inserted between
a :term:`tracker` and a :term:`renderer`. A :term:`transformer` applies transformations
to data such as filtering, computing means, etc., before rendering. sphinxreport supplies a few transformers,
(see :ref:`Transformers`) and more can be added as plugins (see :ref:`Extending sphinxReport``).

This section discusses data representation within sphinxreport and Trackers.

Data representation
===================

Data in sphinxreport is represented by ordered python dictionaries. 

The key in the dictionary denotes a data label, while the associated value can be any of the python data types 
such as numbers, strings,  tuples, lists. Different renderes will require different data types. 
For example, a scatter-plot will require a dictionary with at least two items, each of which
should be a tuple or list of same length containing of numerical items, for example::

   data = { 'expected' : (1,2,3), 'observed' : (4,5,6) }

The scatter plot renderer will create a plot, labeling the x and y-axis ``expected`` and ``observed``, respectively.
Note that a different renderer will interprete the data
differently. Given the same data, a box-plot for example will create 
a single image with two box plots for ``expected`` and ``observed``.

Nesting data
------------

The data dictionaries can be nested. The nesting creates a hierarchy, a :term:`data tree` (see also :class:`DataTree`).
Data in a :term:`data tree` can be accessed via a :term:`data path`,
which is simply a tuple of dictionary keys.

The following example shows two data sets ``dataset1`` and ``dataset2``::

   data = { 'dataset1' : { 'expected' : (1,2,3), 'observed' : (4,5,6) },
            'dataset2' : { 'expected' : (10,20,30), 'observed' : (3,7,6) }, }

The data at :term:`data path` ``('dataset1', 'expected')`` is ``(1,2,3)``.

Given to a scatter plot, this data set will produce two scatter plots, one for 
``dataset1`` and one for ``dataset2``.

The nesting can be up to any level. The first two levels have particular names 
(:term:`track` and :term:`slice`). Renderers may require different levels. For
example, a scatter plot requires at least one, while a matrix plot requires at least 
two (one for row and one for the column).

Grouping data
-------------

By default, data is grouped by the lowest level that a renderer requires. Consider the
following nested data set::
 
   data = { 'experiment1' : {
      	    'condition1' : { 'expected' : (1,2,3), 'observed' : (4,5,6) },
	    'condition2' : { 'expected' : (1,2,3), 'observed' : (14,15,16) },
            'experiment2' : 
      	    'condition1' : { 'expected' : (10,20,30), 'observed' : (3,7,6) },
	    'condition2' : { 'expected' : (10,20,30), 'observed' : (14,15,16) },} }
	    
Give to a scatter plot, data will be grouped by the second level (:term:`slice`), which are ``condition1`` and ``condition2``.
The result will be two plots, one for each condition, with data points for ``experiment1`` and ``experiment2`` appearing
on each.

The grouping can be changed using the :term:`groupby` option. To group by ``experiment`` instead of ``condition``, group
by :term:`track`::

   :groupy: track

or level ``1``::

   :groupby: 1

Grouping can be turned off::

   :groupby: none

such that each measurement is on a separate plot. Grouping can also bee maximized::

   :groupby: all

such that all measurements appear on a single plot.

Trackers
========

Trackers are written by the user and return data.

A :term:`tracker` can be either a python function or a function class (:term:`functor`).
The former will simply return data (see :ref:`Tutorial1`). More flexibility can be gained
from a functor that is derived from :class:`SphinxReport.Tracker.Tracker`.

A :term:`tracker` needs to provide two things, a ``__call__`` method to obtain the data 
and the data hierarchy. The data hierarchy is obtained first while data is then collected
for each path independently. This two-step approach permits multi-processing and caching.

Data hierarchy
--------------

The data hierarchy can be defined in several ways:

1. If the class contains a property ``tracks``, this is taken as the first level of the hierarchy. For example::

    class MyTracker( Tracker ):
        tracks = ("dataset1", "dataset2") 
   
2. If the class contains a property ``slices``, this is taken as the second level of the hierarchy. If ``slices`` exists,
   the class will also need to have a ``tracks`` property. For example::

    class MyTracker( Tracker ):
        tracks = ("experiment1", "experiment2") 
        slices = ("condition1", "condition2") 

3. The property ``paths`` is the most generic way to describe the data hierarchy. It lists all the components of a :term:`data path`::

    class MyTracker( Tracker ):
        paths = ( ("experiment1", "experiment2"),
                  ("condition1", "condition2") )

Each property can be replaced by a ``get`` method to permit more flexibility. For example,
if a method :meth:`getTracks` is present, this will be called instead of checking of the
presence of the ``tracks`` attribute. The method approach accommodates cases in which a 
one-line statement is not enough::

    class MyTracker( Tracker ):
       def getTracks( self ):
          paths = ResultOfSomeSeriousComputation
          return paths

:term:`tracks` and :term:`slices` are sphinxreport
terminology. An alternative labeling would be as ``track=dataset`` and
``slice=measurement``. For example, :term:`tracks` or data sets could be ``mouse``,
``human``, ``rabbit`` and :term:`slices` or measurements could be ``height`` and
``weight``. This nomenclature explains why default
grouping in plots is by :term:`slice` - the above :term:`tracks` and
:term:`slices` would be displayed as two plots for ``height`` and
``weight`` contrasting the various heights and weights for the three
species. 

The __call__ method
-------------------

The __call__ method of a tracker returns the data for a certain :term:`data path`. The :term:`data path`
is supplied as the arguments of the __call__ function call. The __call__ method can be defined generically::

   class MyTracker( TrackerSQL ):
       paths = ( ("experiment1", "experiment2"),
                 ("condition1", "condition2") )

       def __call__( self, *args ):
          data = self.getValues( "SELECT data FROM table WHERE experiment = '%s' AND condition = '%s'" % (args) ) 
          return data

The method :meth:`getValues` is one of the database access convenience functions described below. It returns the first
column of an SQL statement as a list.

A more expressive way will name the parameters::

   class MyTracker( TrackerSQL ):
       paths = ( ("experiment1", "experiment2"),
                 ("condition1", "condition2") )

       def __call__( self, experiment, condition ):
          data = self.getValues( """SELECT data FROM table 
                                    WHERE experiment = '%(experiment)s' AND 
				    	  condition = '%(condition)s'""" % locals() ) 
          return data

The above can be abbreviated and reformatted to improve readabability (using some of the functionality of :class:`TrackerSQL`)::

   class MyTracker( TrackerSQL ):
       paths = ( ("experiment1", "experiment2"),
                 ("condition1", "condition2") )

       def __call__( self, experiment, condition ):
          return self.getValues( """SELECT data FROM table 
                                    WHERE experiment = '%(experiment)s' AND
				          condition = '%(condition)s' """) 

The data return by a tracker is automatically inserted at the correct path.
A tracker itself can return a dictionary or a nested dictionary - this will increase
the depth of the :term:`data tree`.

As the ``__call__`` method is pure python, the user has ultimately full flexibility.

More information on Trackers is at the documentation of the :ref:`Tracker` base class.

Behind the scenes
=================

The :class:`SphinxReport.Dispatcher` is the central actor behind the scenes in sphinxreport.
To resolve a :term:`report` directive, it will first assemble all components
in place (a :term:`renderer`, a :term:`tracker` and optionally a :term:`transformer`).
Conceptually, it then proceeds as follows.

1. Collect every possible :term:`data path` from the :term:`tracker`.

2. Build the complete :term:`data tree`. For each :term:`data path`, call the ``__call__`` method of the :class:`Tracker`.
   If caching is enabled, the :class:`SphinxReport.Dispatcher` will first check if the data is already present in the cache.
   If it is, the data will be retrieved from the cache instead of calling the :class:`Tracker`.

3. Transfrom the :term:`data tree`. If given, apply every :term:`transformer` on the :term:`data tree`. 
   Modifications might re-arrange the hierarchy, prune the tree, substitute values, etc.

4. Collapse the :term:`data tree` according to the grouping level.

5. Call the :term:`renderer` for each grouped data.

6. Collect all images, text files, etc. and insert into these into the rst document.



