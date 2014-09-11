.. _Tutorial5:

======================
Tutorial 5: Using SQL
======================

Trackers allow you to use all the flexibility of python to generate
data sources. In the previous Tutorial :ref:`Tutorial4` the data was
computed directly by the Tracker. More often, the data is computed
elsewhere and stored in a database. cgatreport provides a tracker
:class:`Tracker.TrackerSQL` that facilitates obtaining data from an
SQL database.

The tutorial assumes that `sqlite <http://www.sqlite.org/>`_ has been
installed.

Setting up the database
=======================

Create a small python script :file:`fill.py` in the current directory:
     
.. literalinclude:: fill.py

Once executed::

    python fill.py

the script will have created two tables called ``experiment1_data``
and ``experiment2_data`` and filled them with random data. The data is
thought to have come from two experiments measuring expression level
in genes that are either thought to perform housekeeping functions or
regulatory functions.

Building a tracker
==================

Create the file :file:`Tutorial5.py` in the :file:`python`
subdirectory and add the following code:

.. literalinclude:: trackers/Tutorial5.py
   :lines: 1-19

In order to use data from a database, a connection needs to be
established. This is done by providing a value for the ``backend``
option to the constructor:

.. literalinclude:: trackers/Tutorial5.py
   :lines: 9-13

This will connect to an sqlite database called :file:`csvdb`
in the current directory.

Note that this tracker is derived from
:class:`Tracker.TrackerSQL`. The base class provides two options. It
implements a :meth:`tracks` property that automatically queries the
database for tables matching the pattern in ``pattern``. It also
defines convenience functions such as :meth:`getValues`.
:meth:`getValues` executes an SQL statement that returns rows of
single values and converts these to a python list. The outcome is
the following dataframe:

.. report:: Tutorial5.ExpressionLevel
   :render: dataframe
   :head: 10
   :tail: 10

   Dataframe returned from TrackerSQL

Testing this data source you should see one plot::

   cgatreport-test -t ExpressionLevel -m histogram -o range=0,100,4 -r line-plot

The plots show a bi-modal distribution in the two experiments.

Adding slices
=============

Adding slices is akin to adding ``WHERE`` clauses in SQL
statements. Add the following data source:

.. literalinclude:: trackers/Tutorial5.py
    :lines: 21-


Testing this data source you should now see two plots by function::

   cgatreport-test -t ExpressionLevelWithSlices -m histogram -o range=0,100,4 -r line-plot

The plot is concorporated into a restructured text document as usual:

.. literalinclude:: Tutorial5Demo.rst

See :ref:`Tutorial5Demo` to check how the result should look like.



