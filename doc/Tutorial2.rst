.. _Tutorial2:

==========================
Using tracks
==========================

The previous tutorial created a simple bar-plot of a single data
source. More useful plots show several data sources, called
``tracks``, in a single plot. This tutorial will show how to do this.

**********************
Converting to functors
**********************

Instead of using a python function as in the first tutorial, we will
use a functor, a function object. The functor provides additional
methods that allows the renderer to query for available
:term:`tracks`.

Adding a data source
********************

Create the file :file:`Tutorial2.py` in the :file:`trackers`
subdirectory and add the following code:

.. literalinclude:: trackers/Tutorial2.py

.. literalinclude:: trackers/Tutorial2.py
   :lines: 1-13

The module cgatreport`Trackers` is imported and the data source
``MyDataOneTrack`` is derived from it::
   
   class MyDataOneTrack(Tracker):

The attribute :attr:`tracks` returns the tracks provided by this
tracker::

      tracks = ["all",]

In this example, there is only one track called ``all``. 

Finally, the method :meth:`__call__` provides the data:

.. literalinclude:: trackers/Tutorial2.py
   :pyobject: MyDataOneTrack.__call__

Like the function :meth:`MyDataFunction`, the :class:`Tracker`
MyDataOneTrack returns a dictionary.

Testing the data source
***********************

Testing the current implementation::

   cgatreport-test -t MyDataOneTrack -r interleaved-bar-plot

will show a familiar plot - the functor returns the data as the funtion in :file:`Tutorial2.py`.

******************
Adding more tracks
******************

The functor now permits adding more flexibility to the data source, for 
example returning data for several tracks.

Adding a data source
********************

Add the following code to :file:`Tutorial2.py`:

.. literalinclude:: trackers/Tutorial2.py
   :pyobject: MyDataTwoTracks

As before, the :class:`Tracker` MyDataTwoTracks returns a dictionary,
however these are different dictionaries depending on the :term:`track`.

Testing the data source
***********************

Testing the current implementation::

   cgatreport-test -t MyDataTwoTracks -r interleaved-bar-plot

will now show two bars side-by-side. Try out::

   cgatreport-test -t MyDataTwoTracks -r stacked-bar-plot

Creating a restructured text document
*************************************

To add the trackes to a restructured text document simply use the
:term:`report` directive as before. Create the following
:file:`Tutorial2.rst` (and add it to :file:`index.rst`):

.. literalinclude:: Tutorial2Demo.rst

Note that the same data can appear several times in the same document
with different renderers. See :ref:`Tutorial2Demo` to check how the
result should look like.
