==================
Complex documents
==================

Almost any analysis will grow and it might be useful to think about
code and document organization for complex reports.

Separation of data, report code and report document
===================================================

The data, the code for the report and the actual report document
itself can live in different directories. The respective directories
are called:

   1. ``datadir`` for the data
   2. ``sourcedir`` for the report code and restructured text
   3. ``builddir`` for the report document.

In fact, separation of the three is good practice:

   * the report code can be re-used on different data avoiding
      code duplication between the same reports
   * the report code can be version controlled and backed-up
     separately.
   * The report document can be easily exported as a whole directory
     without having to worry that unrelated data might be included.

Code organization
=================

CGATReport is a framework. Additional :term:`renderers` and :term:`transformers`
can be added as plugins, which is covered elsewhere.

:term:`trackers` are report specific. As the complexity of a report
increases so will the number of trackers. CGATReport does not impose
any restrictions on how trackers are organized as long as they can be
imported through python. Thus, :term:`trackers` can be a simple
collection of functions in a single file or a complex class hierarchy of functors
spread over several modules.

In fact, organizing :term:`trackers` in a class hierarchy and over
several modules has many advantages, for example, avoiding code duplication
and permitting code re-use across several reports. For example, in our reports
all our :term:`trackers` are derived from one class defined::

    class ProjectTracker( TrackerSQL ): pass

This arrangement permits to add additional initialization code that
will apply across the whole report, for example by adding a second
database::

    class ProjectTracker( TrackerSQL ): pass
        def __init__(self, *args, **kwargs ):
	    TrackerSQL.__init__(self, *args, **kwargs )

	    # issuing the ATTACH DATABASE into the sqlalchemy ORM (self.db.execute( ... ))
	    # does not work. The database is attached, but tables are not accessible in later
	    # SELECT statements.
	    if not self.db:
		def _create():
		    import sqlite3
		    conn = sqlite3.connect(re.sub( "sqlite:///", "", DATABASE) )
		    statement = "ATTACH DATABASE '/ifs/data/annotations/mm9_ensembl64/csvdb' AS annotations; "
		    conn.execute(statement)
		    return conn

		self.connect( creator = _create )

.. note::
   Instead of giving a database explicitely, add configuration parameter parsing to the
   tracker modules

Document organization
=====================

Our philosophy in data analysis is to plot everything - if you plot a certain
pie-chart for one data set, plot it for all data sets to make sure it
is typical or atypical. CGATReport's mechanism of tracks and slices
automates plotting everything. However, once too many plots are
created, pages become quickly hard too navigate and the interpretation
is lost among a forest of plots.

We found it good practice to separate the bulk plotting and the
analysis into separate sections of the report. 

The ``pipeline`` section plots everything and is there for reference. It contains 
generic text.

The ``analysis`` section takes individual plots from the ``pipeline``
section, fine-tunes them and selects only the tracks and slices
necessary to make a point.







