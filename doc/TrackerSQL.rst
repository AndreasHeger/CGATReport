.. _sqltrackers:

====================
Accessing SQL tables
====================

Very often, cgatreport is used to display data from an SQL database.
This section describes a set of utility trackers that permit easy
retrieval from SQL databases.

The basic tracker is called :class:`~.TrackerSQL`. See
:ref:`Tutorial5` for an example using it. Following here is a more 
general description.

:class:`~.TrackerSQL` is usually used by subclassing. It 
provides tracks that correspond to tables in the database matching a
certain pattern. For example, assume we have the tables
``experiment1_results``, ``experiment1_data``,
``experiment2_results``, ``experiment2_data`` in our database. The
following tracker will then provide data on the ``_results`` tables::

   class Results( TrackerSQL ):
       pattern = "(.*)_results"

       def __call__( self, track ):
          '''return some data'''

:class:`~.TrackerSQL` will automatically connect to a database
given by the option::

   [report] 
   sql_backend=...

in :file:`cgatreport.ini`. It will query the database for tables
matching the pattern and define these as :term:`tracks`. CGATReport
will then call the tracker with each track to extract the relevant
data from the database.

:class:`~TrackerSQL` is a very generic way to get data from SQL tables.
Some additional utility trackers are part of CGATReport that cover
some common use cases:

:class:`~.SingleTableTrackerRows`
    Obtain data from a single table in which :term:`tracks` are
    organized in rows. The columns in the
    table will be :term:`slices`. 
    Returns :term:`labeled values`.
    

:class:`~.SingleTableTrackerColumns`
    Obtain data from a single table in which :term:`Tracks` are 
    organized in columns. The rows in the table
    will be :term:`slices`. Returns :term:`labeled values`.

:class:`~.SingleTableTrackerHistogram`
    Obtain data from a single table containing multiple histograms.
    The :term:`tracks` are in columns while one column denotes the
    bin locations. Returns :term:`numerical arrays`.

:class:`~.SingleTableTrackerEdgeList`
    Obtain data from a single table where :term:`tracks` are in rows
    and :term:`slices` are in columns. Similar
    to :class:`~SingleTableTrackerRows` and
    :class:`~.SingleTableTrackerColumns`, 
    but while the former pre-load the table and thus pay a penalty
    once, 
    :class:`~.SingleTableTrackerEdgeList` does not
    and is thus suited when only few values need to be extracted from
    a large table.
    Returns :term:`labeled values`.

:class:`~.MultipleTableTrackerHistogram`
    Obtain data from multiple tables containing the same type of
    histogram. The :term:`tracks` will be the individual tables, while
    each individual table should contain the same two columns with
    bins and histogram values.
    Returns :term:`numerical arrays`.

:class:`~.MeltedTableTracker`
    Obtain data from multiple tables matching pattern. The :term:`track`
    will be added as a new column. Returns :term:`labeled values`.
	
:class:`~.MeltedTableTrackerDataframe`
    As :class:`~.MeltedTableTracker`, but returns a :term:`data frame`.
    Suited for analysis with ggplot as data is collected within R directly.




