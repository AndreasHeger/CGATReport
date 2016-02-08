.. _Tutorial15:

============================
Configuring display elements
============================

In this tutorial we introduce the options that permit turning off
particular parts of a display item.  Display items or plots in
CGATReport have the following layout::

   Plot1      Plot2
   [link1]    [link2]
   Title1     Title2

   Caption for the plot

For example, see the layout of the plot below:
   
.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :groupby: track

   Default plot layout.

The flag :term:`no-caption` turns off the caption of a
plot.

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :groupby: track
   :no-caption:

   This is the caption, but it will not be shown.

The flag :term:`no-title` turns off the sub-titles for
individual plot elements.

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :groupby: track
   :no-title:

   Plots without title bars.

The flag :term:`no-links` turns off the links associated
with a particular plot.

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :groupby: track
   :no-links:

   Plots without link element.
