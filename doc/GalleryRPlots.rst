.. _r-box-plot:

==========
r-box-plot
==========

The :class:`SphinxReportPlugins.RPlotter.BoxPlot` class presents
:term:`numerical arrays` as box plots:

.. report:: Trackers.SingleColumnDataExample
   :render: r-box-plot
   :width: 200
   :layout: row

   A box plot.

Options
=======

:class:`SphinxReportPlugins.RPlotter.BoxPlot` has no additional
options apart from :ref:`common plot options`. 

.. _r-smooth-scatter-plot:

=====================
r-smooth-scatter-plot
=====================

The :class:`SphinxReportPlugins.RPlotter.SmoothScatterPlot` class presents
:term:`numerical arrays` as smoothed scatter plots:

.. report:: Trackers.MultipleColumnDataExample
   :render: r-smooth-scatter-plot
   :width: 200
   :layout: row

   A scatter plot.

Options
=======

:class:`SphinxReportPlugins.RPlotter.SmoothScatterPlot` understands
the :ref:`common plot options` plus:

.. glossary::
   :sorted:

   bins
      int or int,int
      
      Number of equally spaced grid points for the density estimation.
      If one value is supplied, it is applied to both dimensions,
      otherwise it is x,y.



