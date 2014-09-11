.. _Background:

=====================
Background
=====================

This section introduces the concepts of cgatreport. This section is
required reading in order to be able to use cgatreport effectively.

To create dynamic figures, cgatreport combines two components, a
:term:`tracker` and a :term:`renderer`. A :term:`tracker` provides
data. Trackers are written by the user and are project specific.

Renderers take data and present them within a report. A renderer might
create one or several plots, some text, a table or some combination of
these. cgatreport provides a collection of renderers for the most
commont plotting needs (see :ref:`Renderers`). Additional renderers
can be added as plugins (see :ref:`Extending CGATReport`).

The central data structure in cgatreport is a pandas_
:term:`dataframe`. After data collection through a :term:`Tracker`,
CGATReport assembles a :term:`dataframe` that is then passed to a
:term:`Renderer` for representation.

There is an optional third component, a :term:`transformer`, that can
be inserted between a :term:`tracker` and a :term:`renderer`. A
:term:`transformer` applies transformations to data such as filtering,
computing means, etc., before rendering. cgatreport supplies a few
transformers, (see :ref:`Transformers`) and more can be added as
plugins (see :ref:`Extending CGATReport`).

The remainder of this section elaborates on the roles of these
components of CGATReport.

The data frame
==============

The central data structure within CGATReport is a pandas_
:term:`DataFrame`. A :term:`DataFrame` is a table. Each
value in the table is identified by two labels, a row
label and a column label. Labels can have multiple
levels. For example::
                           
                       *Colour* *Number* <- Column labels
   *Vehicle*  *Item*  +----------------  <- Row label names
   Car        Door    |  Blue     4
   Car        Roof    |  Red      1
   Bycicle    Frame   |  Pink     1
   Bycicle    Wheel   |  Black    2 
     ^        ^
     |        |
     Row labels

The :term:`DataFrame` above has two columns (``Colour`` and
``Number``) and four rows. Each row is identified by two labels.
These labels can be given names, here ``Vehicle`` and ``Item``.
In pandas_ terminology, this is a :term:`hierarchical index`
or multi-index index.

Building the data frame
=======================

Data collection in CGATReport is through a :term:`Tracker`.  Trackers
are written by the user and return data. A :term:`Tracker` is
basically a data collector or producer and in its simplest instance it
is a function returning some data::

   def getData():
       return [1,2,3,4,5]

More complex trackers are classes that are derived from 
:class:`CGATReport.Tracker.Tracker`. Using these trackers
allows CGATReport to control data collection more flexibly
and to parameterize data collection.

Conceptually, the :term:`Tracker` provides a view onto a complex
dataset which can be sliced in many different ways. For example,
imagine a set of gene expression level measurements in different
tissues and time points. Interesting subsets could thus be tissue
and time point. In practice, this would look like this::

   def GeneExpressionValues(Tracker):
       tracks = ('heart', 'kidney')
       slices = ('0h', '2h', '4h')
       def __call__(self, track, slice):
           # dependent on track and slice
           return {'apoe': 1.2, 'dhfr': 2.4}

Slices through data are called :term:`tracks` and :term:`slices`.
CGATReport will query the :term:`Tracker` for permissable values and
then call the :term:`Tracker` for each combination of :term:`track`
and :term:`slice`.

The returned data is then assembled into a dataframe.

                       *gene_id*  *fpkm*  
   *Track*  *Slice*  +--------------------
   heart    0h       |  apoe       1.2
   heart    0h       |  dhfr       2.4       
   heart    2h       |  apoe       1.4
   heart    2h       |  dhfr       1.1       
   heart    4h       |  apoe       1.2
   heart    4h       |  dhfr       3.4       
   kidney    0h      |  apoe       1.2
   kidney    0h      |  dhfr       2.4       
   kidney    2h      |  apoe       5.2
   kidney    2h      |  dhfr       2.4       
   kidney    4h      |  apoe       1.2
   kidney    4h      |  dhfr       3.1       

The :term:`tracks` and :term:`slices` constitute the
:term:`hierarchical index` of the data frame.

The type of data returned by a :term:`tracker` is flexible, it can be
a number, text, dictionary or array-like structure. The only
requirement is that the data returned needs to be consistent.  The
section on :ref:`Data mapping` explains the various conversions.

.. note::

   Note that the data returned from a :term:`tracker` needs to
   be consistent - a mixture will break the transformation into
   a data frame.

Grouping data
-------------

By default, data is grouped by the lowest level that a renderer
requires. Consider the following nested data set::
 
   data = { 'experiment1' : {
      	    'condition1' : { 'expected' : (1,2,3), 'observed' : (4,5,6) },
	    'condition2' : { 'expected' : (1,2,3), 'observed' : (14,15,16) },
            'experiment2' : 
      	    'condition1' : { 'expected' : (10,20,30), 'observed' : (3,7,6) },
	    'condition2' : { 'expected' : (10,20,30), 'observed' : (14,15,16) },} }
	    
Give to a scatter plot, data will be grouped by the second level
(:term:`slice`), which are ``condition1`` and ``condition2``.  The
result will be two plots, one for each condition, with data points for
``experiment1`` and ``experiment2`` appearing on each.

The grouping can be changed using the :term:`groupby` option. To group
by ``experiment`` instead of ``condition``, group by :term:`track`::

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

A :term:`tracker` can be either a python function or a function class
(:term:`functor`).  The former will simply return data (see
:ref:`Tutorial1`). More flexibility can be gained from a functor that
is derived from :class:`CGATReport.Tracker.Tracker`.

A :term:`tracker` needs to provide two things, a ``__call__`` method
to obtain the data and the data hierarchy. The data hierarchy is
obtained first while data is then collected for each path
independently. This two-step approach permits multi-processing and
caching.

Data hierarchy
--------------

The data hierarchy can be defined in several ways:

1. If the class contains a property ``tracks``, this is taken as the
   first level of the hierarchy. For example::

    class MyTracker( Tracker ):
        tracks = ("dataset1", "dataset2") 
   
2. If the class contains a property ``slices``, this is taken as the
   second level of the hierarchy. If ``slices`` exists, the class will
   also need to have a ``tracks`` property. For example::

    class MyTracker( Tracker ):
        tracks = ("experiment1", "experiment2") 
        slices = ("condition1", "condition2") 

3. The property ``paths`` is the most generic way to describe the data
   hierarchy. It lists all the components of a :term:`data path`::

    class MyTracker( Tracker ):
        paths = ( ("experiment1", "experiment2"),
                  ("condition1", "condition2") )

Each property can be replaced by a ``get`` method to permit more
flexibility. For example, if a method :meth:`getTracks` is present,
this will be called instead of checking of the presence of the
``tracks`` attribute. The method approach accommodates cases in which
a one-line statement is not enough::

    class MyTracker( Tracker ):
       def getTracks( self ):
          paths = ResultOfSomeSeriousComputation
          return paths

:term:`tracks` and :term:`slices` are cgatreport terminology. An
alternative labeling would be as ``track=dataset`` and
``slice=measurement``. For example, :term:`tracks` or data sets could
be ``mouse``, ``human``, ``rabbit`` and :term:`slices` or measurements
could be ``height`` and ``weight``. This nomenclature explains why
default grouping in plots is by :term:`slice` - the above
:term:`tracks` and :term:`slices` would be displayed as two plots for
``height`` and ``weight`` contrasting the various heights and weights
for the three species.

The __call__ method
-------------------

The __call__ method of a tracker returns the data for a certain
:term:`data path`. The :term:`data path` is supplied as the arguments
of the __call__ function call. The __call__ method can be defined
generically::

   class MyTracker( TrackerSQL ):
       paths = ( ("experiment1", "experiment2"),
                 ("condition1", "condition2") )

       def __call__( self, *args ):
          data = self.getValues( "SELECT data FROM table WHERE experiment = '%s' AND condition = '%s'" % (args) ) 
          return data

The method :meth:`getValues` is one of the database access convenience
functions described below. It returns the first column of an SQL
statement as a list.

A more expressive way will name the parameters::

   class MyTracker( TrackerSQL ):
       paths = ( ("experiment1", "experiment2"),
                 ("condition1", "condition2") )

       def __call__( self, experiment, condition ):
          data = self.getValues( """SELECT data FROM table 
                                    WHERE experiment = '%(experiment)s' AND 
				    	  condition = '%(condition)s'""" % locals() ) 
          return data

The above can be abbreviated and reformatted to improve readabability
(using some of the functionality of :class:`TrackerSQL`)::

   class MyTracker( TrackerSQL ):
       paths = ( ("experiment1", "experiment2"),
                 ("condition1", "condition2") )

       def __call__( self, experiment, condition ):
          return self.getValues( """SELECT data FROM table 
                                    WHERE experiment = '%(experiment)s' AND
				          condition = '%(condition)s' """) 

The data return by a tracker is automatically inserted at the correct
path.  A tracker itself can return a dictionary or a nested
dictionary - this will increase the depth of the :term:`data tree`.

As the ``__call__`` method is pure python, the user has ultimately
full flexibility.

More information on Trackers is at the documentation of the
:ref:`Tracker` base class.

Behind the scenes
=================

The :class:`CGATReport.Dispatcher` is the central actor behind the
scenes in cgatreport.  To resolve a :term:`report` directive, it
will first assemble all components in place (a :term:`renderer`, a
:term:`tracker` and optionally a :term:`transformer`).  Conceptually,
it then proceeds as follows.

1. Collect every possible :term:`data path` from the :term:`tracker`.

2. Build the complete :term:`data tree`. For each :term:`data path`,
   call the ``__call__`` method of the :class:`Tracker`.  If caching
   is enabled, the :class:`CGATReport.Dispatcher` will first check
   if the data is already present in the cache.  If it is, the data
   will be retrieved from the cache instead of calling the
   :class:`Tracker`.

3. Transfrom the :term:`data tree`. If given, apply every
   :term:`transformer` on the :term:`data tree`.  Modifications might
   re-arrange the hierarchy, prune the tree, substitute values, etc.

4. Collapse the :term:`data tree` according to the grouping level.

5. Call the :term:`renderer` for each grouped data.

6. Collect all images, text files, etc. and insert into these into the
   rst document.



