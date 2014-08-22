.. _Tutorial10:

==================================
Tutorial 10: Using dates
==================================

This tutorial demonstrates how to use date formatting in plots.

Internally, values within CGATReport are passed around as scalar
numbers. Thus, in order to plot dates, the :term:`Tracker` needs to 
return dates as numbers, for example by using the matpotlib's date2num 
function::

    from CGATReport.Tracker import *

    import matplotlib.dates
    import datetime

    class ProjectDatesExample( Tracker ):
	tracks = ("proj1", "proj2", "proj3")
	def __call__(self, track ):

	    # define a convenience function to convert
            # a three-number tuple to a scalar date float:

	    f = lambda year, month, day: matplotlib.dates.date2num( datetime.datetime( year, month, day ))
	    if track == "proj1":
		return odict( ( ( "start", f(2012,1,1) ),
			      ( "duration", 100 ) ) )
	    elif track == "proj2":
		return odict( ( ( "start", f(2012,6,1) ),
				( "duration", 200 ) ) )
	    elif track == "proj3":
		return odict( (  ( "start", f(2012,8,1) ),
				 ( "duration", 100 ) ) )


In order to display the numbers as dates, use the :term:`xformat` and
:term:`yformat` options to format respective ticks as dates. 

A little care needs to taken to avoid date values of less than 1. To avoid an error such as: 
``ValueError( "date value out of range - needs to larger than 1")``
you can either specify the y-range or in our case use the first value
as an offset. 

In the plot below, we rotate the plot in order to display the data
(start times and durations) as a Gantt chart::

    .. report:: Tutorial10.ProjectDatesExample
       :render: stacked-bar-plot
       :first-is-offset:
       :orientation: horizontal
       :xformat: date

       A Gantt chart

.. report:: Tutorial10.ProjectDatesExample
   :render: stacked-bar-plot
   :first-is-offset:
   :orientation: horizontal
   :xformat: date

   A Gantt chart

   


