.. _Tutorial6Demo:

==========
Tutorial 6
==========

The simplest plot:

.. report:: Tutorial5.ExpressionLevelWithSlices
   :render: line-plot
   :transform: histogram
   :tf-range: 0,100,4

   Expression level in house-keeping and regulatory genes
   in two experiments.

A customized plot:

.. report:: Tutorial5.ExpressionLevelWithSlices
   :render: line-plot
   :transform: histogram
   :tf-range: 0,100,4
   :xtitle: expression level
   :groupby: all
   :as-lines:

   Expression level in house-keeping and regulatory genes
   in two experiments.

The same data in tabular form:

.. report:: Tutorial5.ExpressionLevelWithSlices
   :render: table
   :transform: stats

   Expression level in house-keeping and regulatory genes
   in two experiments.

as box plot:

.. report:: Tutorial5.ExpressionLevelWithSlices
   :render: box-plot
   :groupby: all
   :ytitle: expression level

   Expression level in house-keeping and regulatory genes
   in two experiments.

or as literal histogram:

.. report:: Tutorial5.ExpressionLevelWithSlices
   :render: line-plot
   :transform: histogram
   :tf-range: 0,100,4

   Expression level in house-keeping and regulatory genes
   in two experiments.
