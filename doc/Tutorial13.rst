.. _Tutorial13:

==========================
Grouping data
==========================

A general problem in automated report generation is that 
the underlying data will have very different size. A table
that is perfectly readable with 10 data sets, will become
unwieldy with 100. A bar-plot with 10 data sets renders fine,
but a bar-plot with 100 bars is difficult to interprete.

Sphinx-report provides several mechanisms to deal with data sets
of varying sizes.

1. Some :term:`Renderers` such as :ref:`table` have built-in
   thresholds that will change the how the data is displayed dependend
   on the size of the data set. For example, a small table will be
   inserted inside the document, while a large table will be displayed
   in a separate page.

   The thresholds can usually be changed through options. For example,
   the option :term:`force` will force a renderer to ignore such
   internal thresholds and use the default display mode.

2. All :term:`Renderers` accept a :term:`split-at` option to limit the
   number of data points within a graph. For example, if you have 20
   bars to plot and :term:`split-at` is set to 5, four bar plots will
   be generated with 5 bars each. The default split level varies
   between :term:`Renderers`.

3. Data is grouped before being provided to a :term:`Renderer`. The
   level at which data is grouped is determined by a particular
   :term:`Renderer`. For example, a :term:`Renderer` with a level of 1
   expects only a flat list of data labels (``track1``, ``track2``,
   ...), while a :term:`Renderer` with a level of 2 expects two levels
   (``track1/slice1``, ``track1/slice2``, ``track2/slice1``.  If the
   data frame to be rendered has a higher number of levels than the
   :term:`Renderer` expects, the data will be grouped by the lowest
   level accepted by the :term:`Renderer` and the :term:`Renderer`
   will be called with each group separately.  A :term:`Renderer`
   without a group-level can display a data frame with any level of
   its index.

   To enforce grouping with these kind, the group-level can be
   specified explicitely using the :term:`groupby` option. If there
   are not enough levels present, additional levels will be added to
   the data in order to allow grouping.
  
4. Some :term:`Renderers` such as :ref:`ggplot` have additional
   abilities to create trellis plots, plots subdivided into separated
   panels according to some criterion. In :ref:`ggplot` this is is
   called ``faceting``.


Using the GroupBy option
========================

The following section displays the effect on choosing
different values for the :term:`groupby` option.

Table
-------------------

.. report:: Trackers.LabeledDataExample
   :render: table
   :layout: row
   :width: 200

   Default grouping

.. report:: Trackers.LabeledDataExample
   :render: table
   :layout: row
   :width: 200
   :groupby: slice

   Group by slice (default)

.. report:: Trackers.LabeledDataExample
   :render: table
   :layout: row
   :width: 200
   :groupby: track

   Group by track

.. report:: Trackers.LabeledDataExample
   :render: table
   :layout: row
   :width: 200
   :groupby: all

   Group everything ``:groupby: all``

.. report:: Trackers.LabeledDataExample
   :render: table
   :layout: row
   :width: 200
   :groupby: none

   No grouping: ``:groupby: none``

Bar-Plot
--------

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200

   Default grouping

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :groupby: slice

   Group by track

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :groupby: track

   Group by slice

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :groupby: all

   Group everything ``:groupby: all``
   Because the Renderer can at most deal with one
   level, the data is still grouped at this level.

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :groupby: none

   No grouping: ``:groupby: none``

Deep data tree
--------------

The following section examines the output from a deep nested
data tree.

.. report:: TestCases.DeepTree
   :render: table
   :layout: row
   :width: 200

   Default grouping

.. report:: TestCases.DeepTree
   :render: table
   :layout: row
   :width: 200
   :groupby: slice

   Group by slice (default)

.. report:: TestCases.DeepTree
   :render: table
   :layout: row
   :width: 200
   :groupby: track

   Group by track

.. report:: TestCases.DeepTree
   :render: table
   :layout: row
   :width: 200
   :groupby: all

   Group everything ``:groupby: all``

.. report:: TestCases.DeepTree
   :render: table
   :layout: row
   :width: 200
   :groupby: none

   No grouping: ``:groupby: none``

Grouping options
----------------

.. report:: Trackers.DeepLevelNestedIndexExample
   :render: dataframe
   :groupby: track
   :layout: row

   Group by track

.. report:: Trackers.DeepLevelNestedIndexExample
   :render: dataframe
   :groupby: slice
   :layout: row

   Group by slice

Using numbers to the group-by option groups by the first
number of levels.

.. report:: Trackers.DeepLevelNestedIndexExample
   :render: dataframe
   :groupby: 0
   :layout: row

   Group by first level

.. report:: Trackers.DeepLevelNestedIndexExample
   :render: dataframe
   :groupby: 1
   :layout: row

   Group by first two levels

.. report:: Trackers.DeepLevelNestedIndexExample
   :render: dataframe
   :groupby: 2
   :layout: row

   Group by first three levels

Grouping by named levels
------------------------

If the index has names, grouping can be done by names of the 
indices.

.. report:: Trackers.DeepLevelNamedNestedIndexExample
   :render: dataframe
   :groupby: level0
   :layout: row

   Group by first level

.. report:: Trackers.DeepLevelNamedNestedIndexExample
   :render: dataframe
   :groupby: level1
   :layout: row

   Group by first two levels

.. report:: Trackers.DeepLevelNamedNestedIndexExample
   :render: dataframe
   :groupby: level2
   :layout: row

   Group by first three levels
