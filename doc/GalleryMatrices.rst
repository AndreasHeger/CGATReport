.. _matrix:

matrix
======

Matrices are tables that contain only numeric values. Because of this,
additional transformations are possible for matrices, for example, 
computing totals, row or column maxima, normalization.

The :class:`CGATReportPlugins.Renderer.Matrix` presents
:term:`labeled values` as a table.

.. report:: Trackers.LabeledDataExample
   :render: matrix

   A matrix.

Options
-------

:class:`CGATReportPlugins.Renderer.Matrix` understands the
following options:

.. glossary::
   :sorted:

   transform-matrix
      string

      apply a matrix transform. Possible choices are:

      * *correspondence-analysis*: use correspondence analysis to permute rows/columns 
      * *normalized-column-total*: normalize by column total
      * *normalized-column-max*: normalize by column maximum
      * *normalized-row-total*: normalize by row total
      * *normalized-row-max*: normalize by row maximum
      * *normalized-total*: normalize over whole matrix
      * *normalized-max*: normalize over whole matrix
      * *sort* : sort matrix rows and columns alphanumerically.
      * *filter-by-rows*: only keep columns that are also present in rows
      * *filter-by-cols*: only keep columns that are also present in cols
      * *square*: make matrix square, select only subset of shared rows/columns.
      * *add-row-total* : add the row total as as another column
      * *add-column-total* : add the row total as another row

   force
      flag

      show table, even if it is very large. By default, large
      tables are displayed in a separate page and only a link
      is inserted into the document.

   full-row-labels
      flag

      by default, row names are normalized to remove those levels
      that contain only a single value. Setting full-row-labels
      will retain these levels.

.. _matrix-plot:

matrix-plot
===========

The :class:`CGATReportPlugins.Plotter.MatrixPlot` class plots labeled data
in a matrix plot.

.. report:: Trackers.LabeledDataExample
   :render: matrix-plot
   :layout: row
   :width: 200

   A matrix.

Options
-------

:class:`CGATReportPlugins.Plotter.MatrixPlot` understands the
:ref:`common plot options` and the following options:

.. glossary::
   :sorted:

   colorbar-format
      string

      numerical format for the colorbar, for example ``%5.2f``

   palette  
      choice

      select color palette for plotting a matrix. See cgatreport`matplotlib` for a list of 
      available color palettes.

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

Normalization of row names
--------------------------

.. report:: Trackers.LabeledDataExample
   :render: matrix-plot
   :layout: row
   :width: 200
   :groupby: track
   :layout: column-3

   Split matrix by track. Note that row labels are shortened.


Plotting large matrices
-----------------------

Large matrices are difficult to plot. Labels might overlap or details
will be lost. 

.. report:: TestCases.LongLabelsSmall
   :render: matrix-plot
   :layout: column-2
   :width: 200
   :no-tight:

   Rendering small/large matrices with long/short labels

Maybe with some customizing:

.. report:: TestCases.LongLabelsSmall
   :render: matrix-plot
   :layout: column-2
   :slices: gigantic
   :mpl-rc: figure.figsize=(20,10);legend.fontsize=4

   Rendering small/large matrices with long/short labels

A large matrix in both rows and columns:

.. report:: TestCases.LargeMatrix
   :render: matrix-plot
   :layout: column-2
   :no-tight:

   Rendering small/large matrices with long/short labels

.. ========================
.. Rendering large matrices
.. ========================

.. .. report:: TestCases.VeryLargeMatrix
..    :render: matrix-plot

..    Plotting a very large matrix.

.. .. report:: TestCases.VeryLargeMatrix
..    :render: matrix

..    Plotting a very large matrix.

.. _hinton-plot:

hinton-plot
===========

The :class:`CGATReportPlugins.Plotter.HintonPlot` plots labeled data as a
weight matrix. The width and colour of each box shows the weight. 

.. report:: Trackers.LabeledDataExample
   :render: hinton-plot
   :layout: row
   :width: 200

   A matrix.

The width of each box shows the weight. Additional
labels can provide colours.

.. report:: Trackers.LabeledDataWithErrorsExample
   :render: hinton-plot
   :colours: error
   :layout: row
   :width: 200

   A matrix.

Options
-------

A hinton plot understands the same options as a :ref:`matrix plot`.

