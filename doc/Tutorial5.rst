.. _Tutorial5:

======================
Tutorial 5: Using SQL
======================

Trackers allow you to use all the flexibility of python to generate
data sources. In the previous Tutorial :ref:`Tutorial4` the data
was computed directly by the Tracker. More often, the data is computed
elsewhere and stored in a database. :mod:`SphinxReport` provides a
tracker :class:`Tracker.TrackerSQL` that facilitates obtaining data
from an SQL database.

Configuration
=============

In order to use SQL connectivity, the option ``sql_backend`` needs to be set.
in the file :file:`conf.py`. ``sql_backend`` is passed ot the 
:mod:`sql_alchemy` :meth:`create_engine` method to connect to an SQL database. 
For more information see the `sqlalchemy documentation <http://www.sqlalchemy.org/docs/04/dbengine.html>`_.

The tutorial assumes that `sqlite <http://www.sqlite.org/>`_ has been installed. 
First, set ``sql_backend`` in :file:`conf.py` to ::

   sql_backend="sqlite:///%s/csvdb" % os.path.abspath(".")

This will tell the Trackers to look for a sqlite database called ``csvdb`` in
the root installation directory.

Let us add some data to the database. Create a small python script :file:`fill.py`
in the current directory::

    import random, os
    from subprocess import Popen

    cmd = 'sqlite3 csvdb "%s" '

    def e( stmt ):
	p = Popen( cmd % stmt, shell=True )
	sts = os.waitpid(p.pid, 0)

    e("CREATE TABLE experiment1_data (gene_id TEXT, function TEXT, expression INT)")

    for x in range(0,200,2):
	e( "INSERT INTO %s VALUES ('gene%2i', '%s', %f)" % ("experiment1_data", x, "housekeeping", random.gauss( 40, 5)) )
	e( "INSERT INTO %s VALUES ('gene%2i', '%s', %f)" % ("experiment1_data", x+1, "regulation", random.gauss( 10, 5)) )

    e("CREATE TABLE experiment2_data (gene_id TEXT, function TEXT, expression INT)")

    for x in range(0,200,2):
	e( "INSERT INTO %s VALUES ('gene%2i', '%s', %f)" % ("experiment2_data", x, "housekeeping", random.gauss( 50, 5)) )
	e( "INSERT INTO %s VALUES ('gene%2i', '%s', %f)" % ("experiment2_data", x+1, "regulation", random.gauss( 20, 5)) )

The script will create two tables called ``experiment1_data`` and
``experiment2_data`` and fill them with random data. The data is thought
to have come from two experiments measuring expression level in genes
that are either thought to encode housekeeping functions are regulatory
functions.

Building a tracker
==================

Create the file :file:`Tutorial5.py` in the :file:`python` subdirectory and add 
the following code::

    from SphinxReport.Tracker import *

    class ExpressionLevel(TrackerSQL):
	"""Expression level measurements."""
	mPattern = "_data$"

	def __call__(self, track, slice = None ):
	    statement = "SELECT expression FROM %s_data" % track
	    data = self.getValues( statement )
	    return { "expression" : data }

Note that this tracker is derived from :class:`Tracker.TrackerSQL`. The base
class provides two options. It implements a :meth:`getTracks` method that
automatically queries the database for tables matching the pattern 
in ``mPattern``. It also defines convenience functions such as :meth:`getValues`.
:meth:`getValues` executes an SQL statement that returns rows of single
values and converts these to a python list.

Testing this data source you should see one plot::

   sphinxreport-test -t ExpressionLevel -m histogram -o range=0,100,4 -r line-plot

The plots show a bi-modal distribution in the two experiments.

Adding slices
=============

Adding slices is akin to adding ``WHERE`` clauses in SQL statements. Add the 
following data source::

    class ExpressionLevelWithSlices(ExpressionLevel):
	"""Expression level measurements."""

	def getSlices( self, subset = None ):
	    return ( "housekeeping", "regulation" )

	def __call__(self, track, slice = None ):
	    if not slice: where = ""
	    else: where = "WHERE function = '%s'" % slice
	    statement = "SELECT expression FROM %s_data %s" % (track,where)
	    data = self.getValues( statement )
	    return { "expression" : data }

Testing this data source you should now see two plots by function::

   sphinxreport-test -t ExpressionLevelWithSlices -m histogram -o range=0,100,4 -r line-plot

The plot is concorporated into a restructured text document as usual::

   ==========
   Tutorial 5
   ==========

   Connecting to SQL:

   .. report:: Tutorial4.ExpressionLevelWithSlices
      :render: histogram-plot
      :tf-range: 0,100,4

      Expression level in house-keeping and regulatory genes
      in two experiments.

See :ref:`Tutorial5Demo` to check how the result should look like.



