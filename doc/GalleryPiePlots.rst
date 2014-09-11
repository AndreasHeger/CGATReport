pie-plot
========

The :class:`CGATReportPlugins.Plotter.PiePlot` class presents :term:`labeled values`
as pie charts. For example:

.. report:: Trackers.LabeledDataExample
   :render: pie-plot
   :layout: row
   :width: 200

   A pie plot

Options
-------

:class:`CGATReportPlugins.Plotter.PiePlot` understands the
:ref:`common plot options` and the following options:

.. glossary::
   :sorted:

   pie-min-percentage
      minimum percentage to display. Percentages smaller than the
      minimum are summed and added as "other".

   pie-first-is-total <label>
      the first value in the date is the total. All other entries will be
      subtracted from the total and a new slice will be added as
      label.
      

      

      


