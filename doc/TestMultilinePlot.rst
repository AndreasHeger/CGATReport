Multiple lines per track
========================

.. report:: Trackers.MultipleColumnDataExample
   :render: line-plot
   :transform: histogram
   :bins: arange(0,10)

   A histogram plot.

Selection
---------

.. report:: Trackers.MultipleColumnDataExample
   :render: line-plot
   :transform: histogram,filter
   :bins: arange(0,10)
   :tf-fields: col1
   :tf-level: 2

   A histogram plot, but only with *col1* selected
