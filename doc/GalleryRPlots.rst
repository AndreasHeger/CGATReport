.. _r-box-plot:

==========
r-box-plot
==========

The :class:`CGATReportPlugins.RPlotter.BoxPlot` class presents
:term:`numerical arrays` as box plots:

.. report:: Trackers.SingleColumnDataExample
   :render: r-box-plot
   :width: 200
   :layout: row

   A box plot.

Options
=======

:class:`CGATReportPlugins.RPlotter.BoxPlot` has no additional
options apart from :ref:`common plot options`. 

.. _r-smooth-scatter-plot:

=====================
r-smooth-scatter-plot
=====================

The :class:`CGATReportPlugins.RPlotter.SmoothScatterPlot` class presents
:term:`numerical arrays` as smoothed scatter plots:

.. report:: Trackers.MultipleColumnDataExample
   :render: r-smooth-scatter-plot
   :width: 200
   :layout: row

   A scatter plot.

Options
=======

:class:`CGATReportPlugins.RPlotter.SmoothScatterPlot` understands
the :ref:`common plot options` plus:

.. glossary::
   :sorted:

   bins
      int or int,int
      
      Number of equally spaced grid points for the density estimation.
      If one value is supplied, it is applied to both dimensions,
      otherwise it is x,y.

==============
r-heatmap-plot
==============

The :class:`CGATReportPlugins.RPlotter.HeatmapPlot` class presents
:term:`matrices` as box plots:

.. report:: Trackers.MatrixTracker
   :render: r-heatmap-plot
   :width: 200
   :layout: row

   Heatmap plots

Options
=======

:class:`CGATReportPlugins.RPlotter.HeatmapPlot` has no additional
options apart from :ref:`common plot options`. 

.. _r-ggplot:

=====================================
r-ggplot
=====================================

The :class:`CGATReportPlugins.GGPlot.` class permits plotting 
:term:`data frames` using the ggplot2_ library:

.. report:: Tutorial9.ExpressionLevels
    :render: r-ggplot
    :statement: aes(experiment1, experiment2, color=factor(gene_function)) + geom_point()

    Correlation with expression values coloured by factor gene_function

Options
=======

:class:`CGATReportPlugins.RPlotter.GGPlot` has the following options
in addition to :ref:`common plot options`. 

.. glossary::
   :sorted:

   statement
      string
      
      A ggplot2_ statement describing the plots construction. Names
      within the statement should correspond to column names in the
      data frame.

.. _ggplot2: http://ggplot2.org/

