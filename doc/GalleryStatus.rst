.. _status:

======
status
======

:class:`CGATReportPlugins.Renderer.Status` outputs a concise table
that aggregates various quality control indices and embellishes them
with icons:

.. report:: Trackers.StatusTracker 
   :render: status

   A simple status report

A tracker for status reports need to be derived from
:class:`CGATReport.Tracker.Status`. Each test is implemented as a
method in the tracker starting with the prefix ``test``. The test
method should return a tuple of ``status, information``. The example
below defines two tests::

  class StatusTracker( Status ):

      tracks = ("track1", "track2", "track3")

      def testTest1(self, track):
	  '''test1 passes'''
	  return "PASS", 0.5

      def testTest2(self, track):
	  '''test2 fails.'''
	  return "FAIL", 2

Possible values for ``status`` are:

PASS
   test passed

FAIL
   test failed

WARN
   potential problem

NA
   test not available/applicable

The results can also be grouped:

.. report:: Trackers.StatusTracker 
   :render: status
   :groupby: all

   A simple status report


Options
-------

:class:`CGATReportPlugins.Renderer.Status` understands the 
:ref:`common plot options` and the following options:

.. glossary::
   :sorted:

   :no-legend:
      flag

      If set to true, do not output the legend.

   :columns:
      columns

      comma-separated list of columns to output. The list
      also determines the order. Valid columns are
      "track", "test", "image", "status" and "info".


.. _status-matrix:

=============
status-matrix
=============

:class:`CGATReportPlugins.Renderer.StatusMatrix` outputs a condensed
version of the :term:`status` table.

.. report:: Trackers.StatusTracker 
   :render: status-matrix

   A simple status report.

The table can be compacted by grouping with ``:groupby: all``.

.. report:: Trackers.StatusTracker 
   :render: status-matrix
   :groupby: all

   The whole matrix grouped.

The table can be rotated using the :term:`transpose` option:

.. report:: Trackers.StatusTracker 
   :render: status-matrix
   :groupby: all
   :transpose:

   The table transposed.

Options
-------

:class:`CGATReportPlugins.Renderer.Status` understands the 
:ref:`common plot options` and the following options:

.. glossary::
   :sorted:

   :transpose:
      flag

      Transpose the matrix before outputting.

