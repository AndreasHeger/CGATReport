.. _Tutorial8:

==================================
Extending CGATReport
==================================

The pre-built engines for plotting are not sufficient for all
purposes. Especially when it comes to building highly customized plots
you will need to write your own plugin code. Still, the cgatreport
build system can be used for this.

There are several options you might employ.

Writing a tracker that plots
============================

The basic solution is to write a :term:`Tracker` that plots
instead of returning data.

.. literalinclude:: trackers/UserTrackers.py
   :pyobject: MatplotlibData

The tracker creates a new figure, plots and returns a text element
that contains a place-holder for the figure plotted. The place-holder
is of the format ``#$mpl %i$#`` where ``%i`` is the figure number of
the current plot.

The plots are inserted within a document as::

    .. report:: UserTrackers.MatplotlibData
       :render: user

       Plot using matplotlib

Note the use of the :ref:`user` Renderer, which passes the output of
the :term:`Tracker` straight through to the report.
       
.. report:: UserTrackers.MatplotlibData
   :render: user
   :layout: column-3
   :nocache:

   Plot using matplotlib

See more information in the section about the :ref:`user` renderer.
   
Writing a renderer that plots
=============================

An alternative is to write a :term:`Renderer` that does not require
any data.

.. literalinclude:: trackers/MyPlots.py
   :pyobject: ExampleWithoutData
	      
This renderer does not require any input data, but simply goes
straight to plotting. Note how the :term:`Renderer` again returns
place-holder text for the matplotlib figure that has been generated.
In contrast to the previous solution, a :term:`Renderer` is required
to return a collection (:class:`CGATReport.ResultBlocks.ResultBlocks`) of plot items
(:class:`CGATReport.ResultBlocks.ResultBlock`).

The plots are inserted within a document as::
  
   .. report:: Tracker.Empty
      :render: MyPlots.ExampleWithoutData

      An example of a plot that does not require data

Here, cgatreport can not match ``MyPlots.ExampleWithoutData`` with any
of the known :term:`Renderers`. Instead, it will try to import the
function ``ExampleWithoutData`` from the module ``MyPlots``. The
latter should be somewhere within the :envvar:`PYTHONPATH`. The result
is below:

.. report:: Tracker.Empty
   :render: MyPlots.ExampleWithoutData

   An example of a plot that does not require data

To enable re-use, it is good practice to separate data acquisition and the
rendering process. See below the same plot as above split into a
separate :term:`Tracker` and :term:`Renderer`:

.. literalinclude:: trackers/MyPlots.py
   :pyobject: ExampleWithData

.. literalinclude:: trackers/MyPlots.py
   :pyobject: ExampleData1

The plots are inserted within a document as::

   .. report:: MyPlots.ExampleData1
      :render: MyPlots.ExampleWithData

      The same plot, but separated into a :term:`Tracker`
      and :term:`Renderer`.

and look like this:

.. report:: MyPlots.ExampleData1
   :render: MyPlots.ExampleWithData

   The same plot, but separated into a :term:`Tracker`
   and :term:`Renderer`.

As a benefit of this approach, the individual components can be re-used.
For example, a different dataset can be plotted in the same way::

   .. report:: MyPlots.ExampleData2
      :render: MyPlots.ExampleWithData

      The same plot, but separated into a :term:`Tracker`
      and :term:`Renderer`.

.. report:: MyPlots.ExampleData2
   :render: MyPlots.ExampleWithData

   The same plot, but separated into a :term:`Tracker`
   and :term:`Renderer`.

A :term:`renderer` returns a collection of
:class:`CGATReport.ResultBlocks`. A :term:`ResultBlock` contains the
restructured text that is inserted into the document at the point of
the ``report`` directive.

At the same time, a :term:`Renderer` can create plots on a variety of
devices. These plots will be collected by various agents of the
CGATReport framework and inserted into the document. In order to
associatde a plot with text, usually a place-holder is defined.

The following collectors are defined:

matplotlib plots
   ``#$mpl %i$#`` with ``%i`` being the current matplotlib figure id 

   Implemented in :class:`CGATReportPlugins.MatplotlibPlugin``

R plots
   ``#$rpl %i$#`` with ``%i`` being the current R device number

   Implemented in :class:`CGATReportPlugins.RPlotPlugin``

HTML text
   ``#$html %s$#`` with ``%s`` being the :attr:`title` of the 
   :class:`CGATReport.ResultBlock`.

   Requires the :attr:`html` attribute to be defined in
    :class:`CGATReport.ResultBlock`. The contents
   are saved and a link is inserted in the text.

RST text
    Requires the ``text`` attribute to be defined in
    :class:`CGATReport.ResultBlock`. The contents are
    inserted into the document directly.

R ggplot

   Plots created through R's ggplot2 library are saved in the
   `rggplot` attribute of a :class:`CGATReport.ResultBlock`.  The
   corresponding placeholder is called ``#$rggplot %s#`` with ``%s``
   being the ``figname`` attribute of a result block.

   Implemented in :class:`CGATReportPlugins.RPlotPlugin``
   
bokeh plot

   Plots created through the bokeh library are saved in the
   `bokeh` attribute of a :class:`CGATReport.ResultBlock`.  The
   corresponding placeholder is called ``#$bokeh %i#`` with ``%i``
   being the bokeh figure id (bokeh._id).

   Implemented in :class:`CGATReportPlugins.BokehPlugin``

