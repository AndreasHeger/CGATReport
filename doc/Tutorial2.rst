.. _Tutorial2:

==========================
 Tutorial 2: Using tracks
==========================

The previous tutorial created a simple bar-plot of a single data source. More useful plots
show several data sources, called ``tracks``, in a single plot. This tutorial will show how 
to do this.

**********************
Converting to functors
**********************

Instead of using a python function as in the first tutorial, we will use a functor,
a function object. The functor provides additional methods that allows the renderer 
to query for available :term:`tracks`.

Adding a data source
********************

Create the file :file:`Tutorial2.py` in the :file:`trackers` subdirectory and add 
the following code::

  from SphinxReport.Tracker import *

  class MyDataOneTrack(Tracker):
      """My one-tracked data."""

      tracks = ["all",]

      def __call__(self, track, slice = None ):
	  return dict( (("header1", 10), ("header2", 20)),)

The module sphinxreport`Trackers` is imported and the data source ``MyDataOneTrack`` is derived from it::
   
   class MyDataOneTrack(Tracker):

The docstring::

      """My one tracked data."""

will later reappear in the caption of the table or figure. The attribute :attr:`tracks` returns
the tracks provided by this tracker::

      tracks = ["all",]

In this example, there is only one track called ``all``. The argument *subset* can
be used to pass options from a restructured text directive to a tracker.

Finally, the method :meth:`__call__` provides the data::

      def __call__(self, track, slice = None ):
	  return dict( (("header1", 10), ("header2", 20)),)

Like the function :meth:`MyDataFunction`, the :class:`Tracker` MyDataOneTrack
returns a dictionary. 

Testing the data source
***********************

Testing the current implementation::

   sphinxreport-test -t MyDataOneTrack -r interleaved-bar-plot

will show a familiar plot - the functor returns the data as the funtion in :file:`Tutorial2.py`.

******************
Adding more tracks
******************

The functor now permits adding more flexibility to the data source, for 
example returning data for several tracks.

Adding a data source
********************

Add the following code to :file:`Tutorial2.py`::

    class MyDataTwoTracks(Tracker):
	"""My one-tracked data."""

	tracks = ["track1","track2"]

	def __call__(self, track, slice = None ):
	    if track == "track1":
		return dict( (("header1", 10), ("header2", 20)),)
	    elif track == "track2":
		return dict( (("header1", 20), ("header2", 10)),)

As before, the :class:`Tracker` MyDataTwoTracks returns a dictionary,
however these are different dictionaries depending on the :term:`track`.

Testing the data source
***********************

Testing the current implementation::

   sphinxreport-test -t MyDataTwoTracks -r interleaved-bar-plot

will now show two bars side-by-side. Try out::

   sphinxreport-test -t MyDataTwoTracks -r stacked-bar-plot

Creating a restructured text document
*************************************

To add the trackes to a restructured text document simply use the :term:`report`
directive as before. Create the following :file:`Tutorial2.rst` (and add it to 
:file:`index.rst`)::

    ==========
    Tutorial 2
    ==========

    My new bar plots:

    .. report:: Tutorial2.MyDataOneTrack
       :render: interleaved-bar-plot

       My first bar plot - this time as a functor

    .. report:: Tutorial2.MyDataTwoTracks
       :render: interleaved-bar-plot

       My new bar plot - two tracks

    .. report:: Tutorial2.MyDataTwoTracks
       :render: stacked-bar-plot

       My new bar plot - same data, different renderer

Note that the same data can appear several times in the same document
with different renderers. See :ref:`Tutorial2Demo` to check 
how the result should look like.
