.. _histogram-plot:

==============
histogram-plot
==============

The :class:`CGATReportPlugins.Plotter.HistogramPlot` class presents
:term:`numerical arrays` as histograms.

.. report:: Trackers.ArrayDataExample
   :render: histogram-plot
   :layout: row
   :width: 200

   A histogram plot

Options
=======

:class:`CGATReportPlugins.Plotter.HistogramPlot` understands the
:ref:`common plot options` and the following options:

   error
      field to use for error bars. See :term:`labeled values with errors`

.. _histogram-gradient-plot:

..
   =======================
   histogram-gradient-plot
   =======================

   The :class:`CGATReportPlugins.Plotter.HistogramGradientPlot` class presents
   :term:`numerical arrays` as gradients.

   .. report:: Trackers.ArrayDataExample
      :render: histogram-gradient-plot
      :layout: row
      :width: 200

      A histogram plot

Options
=======

:class:`CGATReportPlugins.Plotter.HistogramGradientPlot` understands the
:ref:`common plot options` and the following options:

.. glossary::
   :sorted:

   colorbar-format
      numerical format for the colorbar, for example ``%5.2f``

   palette
      colour palette to use for matrix. See matplotlib for a list
      of available colour schemes

   reverse-palette
      invert the colour palette
   
