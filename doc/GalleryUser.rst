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

The following :term:`tracker` plots using matplotlib:

.. literalinclude:: trackers/UserTrackers.py
   :lines: 26-39

The tracker creates a new figure, plots and returns a text element
that contains a place-holder for the figure plotted. The place-holder
is of the format ``#$mpl %i$#`` where ``%i`` is the figure number of
the current plot.

The plots are inserted  within a document as::

    .. report:: UserTrackers.MatplotlibData
       :render: user

       Plot using matplotlib

.. report:: UserTrackers.MatplotlibData
   :render: user
   :layout: column-3
   :nocache:

   Plot using matplotlib

Plotting with R
===============

The following :term:`tracker` plots using R:

.. literalinclude:: trackers/UserTrackers.py
   :lines: 37-54

The tracker creates a new device, plots and returns a text element
that contains a place-holder for the figure plotted. The place-holder
is of the format ``#$rpl %i$#`` where ``%i`` is the device number of
the current plot. Note the use of the convenience function
``getCurrentDevice`` to obtain the device number.

.. report:: UserTrackers.RPlotData
   :render: user
   :layout: column-3

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
