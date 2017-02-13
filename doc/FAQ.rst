***
FAQ
***

=========
 Plotting
=========

I can not see the full plot when using ``arange``
*************************************************

Note that the module uses python ranges. Thus, plotting
a histogram with arange(0,100,1) will only bin the
values from 0 to 99 and ignore values greater or larger
that 100.

I get the error message ``TypeError: a class that defines __slots__ without defining __getstate__ cannot be pickled``
*********************************************************************************************************************

The pickling mechanism used in the persistent cache
does not deal well with objects of the type
<class 'sqlalchemy.engine.base.RowProxy'>. These
should be converted to tuples beforehand. 

I get the error message ``RuntimeError: maximum recursion depth exceeded while calling a Python object``
********************************************************************************************************

This is possibly a data type error. If the type of a database column is defined as text (for example
if there are so few values that the correct type can not be guessed), the Trackers might return a
string instead of a numeric value, for example ``(u'0.64425349087',)`` instead of ``(u'0.64425349087',)``.
These should be caught by the cgatreport`CGATReport.DataTypes`.

How do I insert a link into a document
**************************************

In order to add a link to a document, use the restructured text
linking mechanism. Note that path names should be absolute path names.
For example::

    class ReportsList( Tracker ):
	'''provide links to reports in subdirectories.'''

	tracks = glob.glob("subdir*")

	def __call__( self, track ):
	    datadir = os.path.abspath(os.curdir())
	    return "`medip_%(track)s <%(datadir)s/%(track)s/report/html/contents.html>`_" % locals()







