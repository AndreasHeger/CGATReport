=======
Layouts
=======

Testing the :term:`layout` option
=================================

.. report:: TestCases.LayoutTest
   :render: line-plot
   :transform: histogram
   :layout: row
   :mpl-rc: figure.figsize=(3,3)
   :as-lines:

   Row layout

.. report:: TestCases.LayoutTest
   :render: line-plot
   :transform: histogram
   :layout: column
   :mpl-rc: figure.figsize=(3,3)
   :as-lines:

   Column layout

.. report:: TestCases.LayoutTest
   :render: line-plot
   :transform: histogram
   :layout: column-2
   :mpl-rc: figure.figsize=(3,3)
   :as-lines:

   Column layout with two columns

.. report:: TestCases.LayoutTest
   :render: line-plot
   :transform: histogram
   :layout: grid
   :mpl-rc: figure.figsize=(3,3)
   :as-lines:

   Grid layout

Testing the :term:`split-at` option
===================================

.. report:: TestCases.SplittingTest
   :render: line-plot
   :split-at: 4
   :layout: column-4
   :width: 200

   Splitting to show 4 tracks per plot

.. report:: TestCases.SplittingTest
   :render: line-plot
   :split-at: 4
   :split-always: slice0
   :layout: column-4
   :width: 200

   Splitting to show 4 tracks per plot
   including track0

