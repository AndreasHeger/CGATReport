***********
Transformer
***********

Inheritance diagram
===================

.. inheritance-diagram:: CGATReportPlugins.Transformer
   :parts: 1

.. inheritance-diagram:: CGATReportPlugins.TransformersGeneLists
   :parts: 1

Transformer
===========

.. automodule:: CGATReportPlugins.Transformer
   :members:
   :inherited-members:
   :show-inheritance:

.. automodule:: CGATReportPlugins.TransformersGeneLists
    :members:
    :undoc-members:
    :show-inheritance:

..
   Checks
   ======

   TransformerFilter
   ------------------

   Before transformation:

   .. report:: Transformers.TrackerFilter
      :render: debug

      TransformerFilter

   After transformation:

   .. report:: Transformers.TrackerFilter
      :render: debug
      :transform: filter
      :tf-fields: x

      TransformerFilter

   TransformerSelect
   ------------------

   Before transformation:

   .. report:: Transformers.TrackerSelect
      :render: debug

      TransformerSelect

   After transformation:

   .. report:: Transformers.TrackerSelect
      :render: debug
      :transform: select
      :tf-fields: x

      TransformerSelect

   TransformerToLabels
   --------------------

   Before transformation:

   .. report:: Transformers.TrackerToLabels
      :render: debug

      TransformerToLabels

   After transformation:

   .. report:: Transformers.TrackerToLabels
      :render: debug
      :transform: tolabels

      TransformerToLabels

   TransformerToList
   --------------------

   Before transformation:

   .. report:: Transformers.TrackerToList
      :render: debug

      TransformerToList

   After transformation:

   .. report:: Transformers.TrackerToList
      :render: debug
      :transform: tolist

      TransformerToList

   TransformerToDataFrame
   -----------------------

   Before transformation:

   .. report:: Transformers.TrackerToDataFrame
      :render: debug

      TransformerToFrame

   After transformation:

   .. report:: Transformers.TrackerToDataFrame
      :render: debug
      :transform: toframe

      TransformerToDataFrame

   TransformerCombinations
   -----------------------

   Before transformation:

   .. report:: Transformers.TrackerCombinations
      :render: debug

      TransformerCombinations

   After transformation:

   .. report:: Transformers.TrackerCombinations
      :render: debug
      :transform: combinations

      TransformerCombinations

.. TransformerIndicator
.. -----------------------

.. Before transformation:

.. .. report:: Transformers.TrackerIndicator
..    :render: debug
   
..    TransformerIndicator

.. After transformation:

.. .. report:: Transformers.TrackerIndicator
..    :render: debug
..    :transform: indicator
   
..    TransformerIndicator

..
   TransformerGroup
   -----------------------

   Before transformation:

   .. report:: Transformers.TrackerGroup
      :render: debug

      TransformerIndicator

   After transformation:

   .. report:: Transformers.TrackerGroup
      :render: debug
      :transform: group
      :tf-fields: x

      TransformerGroup

TransformerPandas
-----------------------

Before transformation:

.. report:: Trackers.MultipleColumnDataExample
   :render: debug

   TransformerPandas

After transformation:

.. report:: Trackers.MultipleColumnDataExample
   :render: debug
   :transform: pandas
   :tf-statement: reset_index().set_index('slice','track')

   TransformerPandas


TransformerStats
-----------------------

Before transformation:

.. report:: Transformers.TrackerStats
   :render: debug
   
   TransformerStats

After transformation:

.. report:: Transformers.TrackerStats
   :render: debug
   :transform: stats

   TransformerStats


TransformerPairwise
-------------------

Before transformation:

.. report:: Transformers.TrackerPairwise
   :render: debug
   
   TransformerPairwise

After transformation:

.. report:: Transformers.TrackerPairwise
   :render: debug
   :transform: correlation

   TransformerCorrelation

.. report:: Transformers.TrackerPairwise
   :render: debug
   :transform: pearson

   TransformerCorrelationPearson

.. report:: Transformers.TrackerPairwise
   :render: debug
   :transform: spearman

   TransformerCorrelationSpearman

.. report:: Transformers.TrackerPairwise
   :render: debug
   :transform: test-mwu

   TransformerCorrelationMannWhitneyU

.. report:: Transformers.TrackerPairwise
   :render: debug
   :transform: contingency

   TransformerContingency

TransformerAggregate
--------------------

Before transformation:

.. report:: Transformers.TrackerAggregate
   :render: debug
   
   TransformerAggregate

After transformation:

.. report:: Transformers.TrackerAggregate
   :render: debug
   :transform: aggregate

   TransformerAggregate

TransformerHistogram
--------------------

Before transformation:

.. report:: Transformers.TrackerHistogram
   :render: debug
   
   TransformerHistogram

After transformation:

.. report:: Transformers.TrackerHistogram
   :render: debug
   :transform: histogram
   :tf-bins: 10

   TransformerHistogram


