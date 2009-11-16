Histograms
==========

Cumulative
----------

.. report:: Trackers.SingleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)
   :tf-aggregate: cumulative
   :layout: row

   A histogram plot.

Reverse cumulative
------------------

.. report:: Trackers.SingleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)
   :tf-aggregate: reverse-cumulative
   :layout: row

   A histogram plot.

Normalized total
----------------

.. report:: Trackers.SingleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)
   :tf-aggregate: normalized-total
   :layout: row

   A histogram plot.

Normalized max
----------------

.. report:: Trackers.SingleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)
   :tf-aggregate: normalized-max
   :layout: row

   A histogram plot.

Normalized total and cumulative
-----------------------------

.. report:: Trackers.SingleColumnDataExample
   :render: line-plot
   :transform: histogram
   :tf-bins: arange(0,10)
   :tf-aggregate: normalized-total,cumulative
   :layout: row

   A histogram plot.
