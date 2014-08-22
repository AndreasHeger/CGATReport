.. _venn-plot:

=========
venn-plot
=========

:class:`CGATReportPlugins.Renderer.Venn` plots a 2 or 3 circle
Venn diagramm:

.. report:: Trackers.VennTracker 
   :render: venn-plot
   :groupby: track
   :layout: columns-2
   :width: 300

   Two and three circle Venn diagrams.

A tracker for Venn diagrams needs to return a dictionary with the following elements:

    * ('10', '01', and '11') for a two-circle Venn diagram.
    * ('100', '010', '110', '001', '101', '011', '111') for a three-circle Venn diagram.

Optionally, the dictionary might also contain a list called ``labels``.

For example::

    class VennTracker( Tracker ):

	tracks = ('two-circle', 'three-circle' )

	def __call__( self, track ):

	    if track == 'two-circle':
		return {'01' : 10, '10': 20, '11' : 5, 
			'labels' : ("SetA", "SetB") }

	    elif track == 'three-circle':
		return {'001' : 10, '010': 20, '100' : 5,
			'011' : 10, '110': 20, '101' : 5,
			'111' : 10,
			'labels' : ("SetA", "SetB", "SetC") }

Options
-------

:class:`CGATReportPlugins.Renderer.Venn` has no additional
options.

