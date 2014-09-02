Multiple lines per track
========================

.. report:: Trackers.MultipleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)

   A histogram plot.

Selection
---------

.. report:: Trackers.MultipleColumnDataExample
   :render: line-plot
   :transform: histogram,filter
   :tf-bins: arange(0,10)
   :tf-fields: bin,col1

   A histogram plot, but only with *col1* selected
