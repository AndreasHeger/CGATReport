.. _Tutorial:

********
Tutorial
********

The :mod:`SphinxReport` module is an extension for sphinx
that provides facilities for data retrieval and data rendering
within reStructured text. For example, the reST snippet::

   .. report:: Trackers.Lengths
      :render: histogram

will insert a table with transcript length information at the current location.
It will do so by instantiating a :class:`Renderer` of the type *histogram* and fill it 
with data from the Tracker :class:`Lengths`.

Simple example
==============

To do this, the extension will require a module called :mod:`Trackers` in its PYTHONPATH and 
a class called :class:`Lengths` which defines a :meth:`__call__` method.

The file Trackers.py could look like this::

   from SphinxReport.Tracker import *
   from SphinxReport.DataTypes import *
   class Lengths(Tracker):
      """Lengths of whatever."""

      def getTracks( self ):
      	  return ["all",]

      @returnSingleColumnData
      def __call__(self, track, slice = None ):
      	  return [ 121,221,213,421 ]

Line-by-line, this definition does the following. Firstly, the class
is derived from Tracker::
   
   class Lengths(Tracker):

The docstring::

      """Lengths of whatever."""

will later reappear in the caption of the table or figure. The method :meth:`getTracks` returns
the tracks provided by this tracker::

      def getTracks( self ):
      	  return ["all",]

A table or figure is organized into tracks. These would correspond to lines in a plot or columns in a table.
In the example above, there is only one track called "all". Finally, the method :meth:`__call__` provides the 
data to the :class:`Renderer`::

      @returnSingleColumnData
      def __call__(self, track, slice = None ):
      	  return [ 121,221,213,421 ]

The type of data returned requires on the renderer. For example, a histogram simply requires a list or tuple of 
values. The *table* renderer on the other hand asks for a list of (column,value) tuples.
The decorator :meth:`returnSingleColumnData` enforces type checking. 

SQL example
===========

The previous example returned a set of fixed values. Of course, the data could be obtained from
any number of sources. In the following example, the data is returned from SQL::

   from SphinxReport.Tracker import *
   class Lengths(TrackerSQL):
      """Lengths of transcript models."""
      mPattern = "_length$"

      @returnSingleColumnData
      def __call__(self, track, slice = None ):
      	  return self.getValues( "SELECT length FROM %s_length" % (track) )

The are a few differences in this definition. Firstly, the class
is derived from :class `TrackerSQL`::
   
   class Lengths(TrackerSQL):

The base class takes care of finding tracks. Hence, the method :meth:`getTracks` can be omitted. 
Instead, the attribute :attr:`mPattern` collects all tables in the current database that match the
pattern and designa.tes them as tracks. Thus, if there are the tables "experiment1_length",
"experiment2_length" and "experiment3_length" in the database, the histogram would have three columns 
labelled "experiment1", "experiment2" and "experiment3".

The method :meth:`__call__` collects the data from the database using an SQL select statement::

      @returnSingleColumnData
      def __call__(self, track, slice = None ):
      	  return self.getValues( "SELECT length FROM %s_length" % (track) )

Example with slices
===================

Slices define cross-sections across the data. Imagine we have stored the lengths of
pencils in our database and pencils can be either H or 2B. To render data according
to pencil type, we can define slices::

   from SphinxReport.Tracker import *
   class Lengths(TrackerSQL):
      """Lengths of transcript models."""
      mPattern = "_length$"

      def getSlices( self ): 
      	  return ("all", "H", "2B", "4B")

      @returnSingleColumnData
      def __call__(self, track, slice = None ):
          if slice == "None" or slice == "all":
	     return self.getValues( "SELECT length FROM %s_length" % (track) )
	  else:
	     return self.getValues( "SELECT length FROM %s_length WHERE type = '%s'" % (track,slice) )

The following has changed. There is an additional method :meth:`getSlices` enumerating the available slices::

      def getSlices( self ): 
      	  return ("all", "H", "2B" )

The :meth:`__call__` method has been expanded to allow selection of a subset of data::

      @returnSingleColumnData
      def __call__(self, track, slice = None ):
          if slice == "None" or slice == "all":
	     return self.getValues( "SELECT length FROM %s_length" % (track) )
	  else:
	     return self.getValues( "SELECT length FROM %s_length WHERE type = '%s'" % (track,slice) )


Note that the reST snippet has not changed, but instead of inserting a single histogram, the snippet
will now insert three histograms for the slices "all", "H" and "2B", each plot containing tracks 
"experiment1", "experiment2" and "experiment3".

The default is to group tracks by slice, but if you would want to group slices by track, you could give the option
``:groupby:`` to the reST snippet::

   .. report:: Trackers.Lengths
      :render: histogram
      :groupby: track

The renderer now returns three histograms "experiment1", "experiment2" and "experiment3", each containing
columns "all", "H" and "2B".

Options to the render directive
===============================

The render directive accepts two kinds of options. The first class is applicable to
all renderes and include the options

   * groupby
   * tracks
   * slices

The second class of options are render specific. Examples are:

   * legend-location
   * bins
   * ...













