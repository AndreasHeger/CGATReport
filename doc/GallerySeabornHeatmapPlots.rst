.. _sb-heatmap-plot:

sb-heatmap-plot
===============

The :class:`CGATReportPlugins.Seaborn.HeatmapPlot` class plots labeled data
in a heat map or matrix plot.

.. report:: Trackers.MatrixTracker
   :render: sb-heatmap-plot
   :layout: row
   :width: 200

   A matrix.

Options
-------

:class:`CGATReportPlugins.Seaborn.HeatmapPlot` understands the
:ref:`common plot options`. For heatmap specific options, see
the seaborn `heatmap
<http://stanford.edu/~mwaskom/software/seaborn/generated/seaborn.heatmap.html#seaborn.heatmap>`_ documentation.

.. glossary::
   :sorted:

   colorbar-format
      string

      numerical format for the colorbar, for example ``%5.2f``

   palette  
      choice

      select color palette for plotting a matrix. See
      cgatreport`matplotlib` for a list of available color palettes.

   reverse-palette
      invert the colour palette

   max-rows
      int

      maximum number of rows per plot, If the matrix contains more
      rows, the plot is split into multiple plots.

   max-cols
      int

      maximum number of columns per plot. If the matrix contains
      more columns, the plot is split into multiple plots.

   nolabel-rows, nolabel-col
      flag

      produce plot without annotating the row or column axes.


.. _sb-clustermap-plot:

sb-clustermap-plot
===============

The :class:`CGATReportPlugins.Seaborn.ClustermapPlot` class plots labeled data
in a heat map or matrix plot.

.. report:: Trackers.MatrixTracker
   :render: sb-clustermap-plot
   :layout: row
   :width: 200

   A matrix.

Options
-------

:class:`CGATReportPlugins.Seaborn.ClustermapPlot` understands the
:ref:`common plot options` and the following options:

.. glossary::
   :sorted:

   colorbar-format
      string

      numerical format for the colorbar, for example ``%5.2f``

   palette  
      choice

      select color palette for plotting a matrix. See
      cgatreport`matplotlib` for a list of available color palettes.

   reverse-palette
      invert the colour palette

   max-rows
      int

      maximum number of rows per plot, If the matrix contains more
      rows, the plot is split into multiple plots.

   max-cols
      int

      maximum number of columns per plot. If the matrix contains
      more columns, the plot is split into multiple plots.

   nolabel-rows, nolabel-col
      flag

      produce plot without annotting the row or column axes.

   kwargs
      string

      Keyword arguments that will be passed to the seaborn 
      `clustermap
      <http://stanford.edu/~mwaskom/software/seaborn/generated/seaborn.clustermap.html#seaborn.clustermap>`_
      command.
      

