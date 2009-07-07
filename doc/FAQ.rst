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
These should be caught by the :mod:`SphinxReport.DataTypes`.

sphinxreport-build freezes keyboard and mouse when run with multiple processes
******************************************************************************

When running sphinxreport-build, the keyboard and mouse freezes. The only remedy
is to kill the processes remotely. Then, the following message appears::

   sphinxreport-build: Fatal IO error 0 (Success) on X server :0.0

This seems to be a problem with combining matplotlib and multiprocessing. Possibly, 
the first time a plot command is called that process receives the X connection and 
other processes will then hang. The solutions are to either

1. use a backend that does not require X. For example TkAgg backend works, while
   GTKAgg does not. To change the matplotlib backend, edit your :file:`matplotlibrc` file.
   Or, 

2. only run sphinxreport, not sphinxreport-build. Instead of
   ``sphinxreport-build --num-jobs=4 sphinx-build -b html -d _build/doctrees   . _build/html``
   run
   ``sphinx-build -b html -d _build/doctrees   . _build/html``




