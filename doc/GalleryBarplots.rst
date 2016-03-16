.. _bar-plot:

========
bar-plot
========

The :class:`CGATReportPlugins.Plotter.BarPlot` class presents
:term:`labeled values` as overlapping bars.

.. report:: Trackers.LabeledDataExample
   :render: bar-plot
   :layout: row
   :width: 200

   A bar plot with overlapping bars.

Options
=======

:class:`CGATReportPlugins.Plotter.BarPlot` understands the
:ref:`common plot options` and the following options:

.. glossary::
   :sorted:

   label
      string

      field to use for data labels. See :term:`labeled values with labels`
      
   error
      string

      field to use for error bars. See :term:`labeled values with
      errors`

   colour
      string
      
      field to use for colours.

   orientation
      string

      orientation of bars. Can be either ``vertical`` (default) or ``horizontal``

   switch
      flag
      
      switch rows/columns in plot.

.. _stacked-bar-plot:

================
stacked-bar-plot
================

The :class:`CGATReportPlugins.Plotter.StackedBarPlot` class presents :term:`labeled values`
as stacked bars.

.. report:: Trackers.LabeledDataExample
   :render: stacked-bar-plot
   :layout: row
   :width: 200

   A bar plot with stacked bars.

.. _interleaved-bar-plot:

====================
interleaved-bar-plot
====================

The :class:`CGATReportPlugins.Plotter.InterleavedBarPlot` class presents :term:`labeled values`
as interleaved bars. Both *interleaved-bars* and *bars* can be used.

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200

   A bar plot with interleaved bars.


Changing plot orientation
==========================

Horizontal bar charts can be created with the option :term:`orientation`.

.. report:: Trackers.LabeledDataExample
   :render: bar-plot
   :layout: row
   :width: 200
   :orientation: horizontal

   A horizontal bar plot with interleaved bars.

.. report:: Trackers.LabeledDataExample
   :render: stacked-bar-plot
   :layout: row
   :width: 200
   :orientation: horizontal

   A horizontal bar plot with interleaved bars.

.. report:: Trackers.LabeledDataExample
   :render: interleaved-bar-plot
   :layout: row
   :width: 200
   :orientation: horizontal

   A horizontal bar plot with interleaved bars.

The option :term:`first-is-offset` can be used to create Gantt-like charts:

.. report:: Trackers.LabeledDataExample
   :render: stacked-bar-plot
   :layout: row
   :width: 200
   :orientation: horizontal
   :first-is-offset:

   A horizontal bar plot with stacked bars. The first value is used
   as an offset.


Adding error bars and labels
============================

The :class:`CGATReportPlugins.Plotter.InterleavedBarPlot` class
presents :term:`labeled values` as interleaved bars. Both
*interleaved-bars* and *bars* can be used.

.. report:: Trackers.LabeledDataWithErrorsAndLabelsExample
   :render: bar-plot
   :error: error
   :layout: row
   :width: 200

   A bar plot with overlapping bars and errors

.. report:: Trackers.LabeledDataWithErrorsAndLabelsExample
   :render: interleaved-bar-plot
   :error: error
   :layout: row
   :width: 200

   A bar plot with interleaved bars and errors

.. report:: Trackers.LabeledDataWithErrorsAndLabelsExample
   :render: stacked-bar-plot
   :error: error
   :layout: row
   :width: 200
   
   A bar plot with interleaved bars and errors

.. report:: Trackers.LabeledDataWithErrorsAndLabelsExample
   :render: bar-plot
   :label: label
   :layout: row
   :width: 200

   A bar plot with overlapping bars and labels

.. report:: Trackers.LabeledDataWithErrorsAndLabelsExample
   :render: interleaved-bar-plot
   :label: label
   :layout: row
   :width: 200

   A bar plot with interleaved bars and labels

.. report:: Trackers.LabeledDataWithErrorsAndLabelsExample
   :render: stacked-bar-plot
   :label: label
   :layout: row
   :width: 200

   A bar plot with stacked bars and labels


