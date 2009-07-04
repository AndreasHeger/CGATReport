Test cases
==========

Here are various examples to test pathological plots.

Matrix plot
-----------

.. report:: TestCases.LongLabelsSmall
   :render: matrix-plot
   :layout: column-2

   Rendering small/large matrices with long/short labels

Maybe with some customizing:

.. report:: TestCases.LongLabelsSmall
   :render: matrix-plot
   :layout: column-2
   :slices: gigantic
   :mpl-rc: figure.figsize=(20,10);legend.fontsize=4

   Rendering small/large matrices with long/short labels


