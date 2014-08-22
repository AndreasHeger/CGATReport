.. _user:

====
user
====

The :class:`CGATReportPlugins.Renderer.User` does not render.
This renderer can be used to do some plotting within a
:term:`tracker`.

The examples below illustrate how different types of content can
be rendered.

Plotting with matplotlib
========================

The following :term:`tracker` plots using matplotlib::

    class MatplotlibData( Tracker ):
	'''create plot using matplotlib.'''
	slices = ("slice1", "slice2")
	tracks = ("track1", "track2", "track3")
	def __call__(self, track, slice = None):
	    s = [random.randint(0,20) for x in range(40)]
	    random.shuffle( s )

	    # do the plotting
	    fig = plt.figure()
	    plt.plot( s )
	    return odict( (("text", "#$mpl %i$#" % fig.number),) )

The tracker creates a new figure, plots and returns a text element that contains a
place-holder for the figure plotted. The place-holder is of
the format ``#$mpl %i$#`` where ``%i`` is the figure number
of the current plot.

The plots are inserted  within a document as::

    .. report:: UserTrackers.MatplotlibData
       :render: user

       Plot using matplotlib

.. report:: UserTrackers.MatplotlibData
   :render: user

   Plot using matplotlib

Plotting with R
===============

The following :term:`tracker` plots using R::

    def getCurrentRDevice():
        '''return the numerical device id of the current device.'''
        return R["dev.cur"]()[0]

    class RPlotData( Tracker ):
	'''create plot using R.'''
	slices = ("slice1", "slice2")
	tracks = ("track1", "track2", "track3")
	def __call__(self, track, slice = None):
	    s = [random.randint(0,20) for x in range(40)]
	    random.shuffle( s )
	    # do the plotting
	    R.x11()
	    R.plot( s, s )
	    return odict( (("text", "#$rpl %i$#" % getCurrentRDevice()),) )

The tracker creates a new device, plots and returns a text element that contains a
place-holder for the figure plotted. The place-holder is of
the format ``#$rpl %i$#`` where ``%i`` is the device number
of the current plot. Note the use of the convenience function 
``getCurrentDevice`` to obtain the device number.

.. report:: UserTrackers.RPlotData
   :render: user

   Plot using R

Adding pre-built images
=======================

Pre-built images can be added, including flanking text.

.. report:: UserTrackers.Images
   :render: user

   Plot pre-built images

They can also appear in a table:

.. report:: UserTrackers.Images2
   :render: user

   Plot pre-built images
