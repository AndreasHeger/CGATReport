.. _Reference:

*********
Reference
*********

Renderer Options
****************

The following table lists all available options to the ``:render:``
directive. Not all will be having an effect, for example :term:`xtitle`
is only applicable to plots, but not tables. Superfluous options are
ignored.

.. glossary::
   :sorted:

   tf-bins
      int or sequence of scalars, optional

      If `tf-bins` is an int, it defines the number of equal-width
      bins in the given range (10, by default). If `bins` is a sequence,
      it defines the bin edges, including the rightmost edge, allowing
      for non-uniform bin widths.
      (From the :mod:`numpy` documentation)
      If bins is of the format ''log-X'' with X an integer number, X 
      logarithmig bins will be used. 
      If bins is ''dict'', then the histogram will be computed using a
      dictionary. Use this for large data sets, but make sure to round
      values reasonably.

      Examples::

	 :tf-bins: 100
	 :tf-bins: arange(0,1,0.1)
	 :tf-bins: log-100

   tf-range
      float[,float[,float]], optional

      The minimum value, maximum value and the bin-size. Fields can the left empty.
      If no minimum is provided, the minimum value is min(data), the maxmimum
      value is max(data) and the bin-size depends on the :term:`tf-bins` parameter.
      Values outside the range are ignored. 

   tf-aggregate
      cumulative|reverse-cumulative|normalized-max|normalized-total

      normalize or cumulate values in a histogram

   groupby   
      choice of 'tracks', 'slices', 'all'

      defines the grouping order. If a tracker provides multiple slices
      and tracks, the grouping can be either tracks first ('tracks') or
      slices first ('slices'). If :term:`groupby` is 'all', all tracks
      and slices will be rendered together. The default is to group by
      'slices'.

   layout  
      not implemented yet.

   logscale  
      choice of 'x', 'y', 'xy'

      convert x-axis, y-axis or both axes to logarithmic coordinates.

   title  
      string

      add a title to the plot

   xtitle  
      string

      add an explicit label to the X-axis. The default is to use the
      one supplied by the :class:Tracker.

   ytitle  
      string

      add an explicit label to the Y-axis. The default is to use the
      one supplied by the :class:Renderer.

   add-title
      flag

      add title within in each plot

   add-total 
      flag

      add a total column to a table.

   colorbar-format
      string

      printf format for tick labels on the colorbar. The default is '%1.1f'.

   force
      flag

      force display of large tables and matrices. If given,
      the large table will be inserted. The default behaviour is to create
      a separate file for the table and link to it.

   palette  
      choice

      select color palette for plotting a matrix. See :mod:`matplotlib` for a list of 
      available color palettes.

   reverse-palette  
      flag

      reverse the color palette used for plotting matrices.

   transform-matrix  
      choice

      apply matrix transformations before rendering. See :class:`SphinxReport.RendererMatrix`
      for a list of options.

   plot-value  
      unchanged

   tracks 
      list separated by comma

      tracks to output. The tracks available depend on the
      tracker. The default is to output all tracks. In the following
      Example, only the tracks 'set1' and 'set2' are output::

         :slices: set1,set2

   slices 
      list separated by comma

      slices to output. The slices available depend on the
      tracker. The default is to output all slices. In the following
      Example, only the slices 'all' and 'novel' are output::
         
         :slices: all,novel

   as-lines 
      flag

      convert line graphics to lines, omitting any symbols.

   legend-location
      choice

      specify the location of the legend. See :mod:matplotlib for options. The default 
      option 'outer' displays the legend next to the plot.

   xrange
      a pair of comma separate values

      restrict plot to part of the x-axis

   yrange
      a pair of comma separate values

      restrict plot to part of the y-axis

   zrange
      a pair of comma separate values

      restrict plot to part of the z-axis

   mpl-figure
      ``;`` separated ``key=value`` pairs

      options for matplotlib ``figure`` calls().

   mpl-legend
      ``;`` separated ``key=value`` pairs   

      options for matplotlib ``legend`` calls().

   mpl-subplot
      ``;`` separated ``key=value`` pairs

      options for matplotlib ``subplots_adjust`` calls().

   mpl-rc
      ``;`` separated ``key=value`` pairs

      general environment settings for matplotlib.
      See the matplotlib documentation. Multiple options can be
      separated by ;, for example 
      ``:mpl-rc: figure.figsize=(20,10);legend.fontsize=4``


