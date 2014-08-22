****************
Renderer
****************

Inheritance diagram
===================

.. inheritance-diagram:: CGATReportPlugins.Renderer
   :parts: 1

Writing your own renderer
=========================

Objects of :class:`Renderer` convert data from 
a :class:`Tracker` to restructured text directives.

More precisely, a :class:`Renderer` implements a
:meth:`render` method that will take a :class:`DataTree` 
instance and return a :class:`ResultBlocks` instance.

The example below creates a simple renderer::

    class RendererDebug( Renderer ):
	'''a simple renderer, returning the type of data and the number of items at each path.'''

	# only look at leaves
	nlevels = 1

	def render( self, work, path ):

	    # initiate output structure
	    results = ResultBlocks( title = path )

	    # iterate over all items at leaf
	    for key in work:

		t = type(work[key])
		try:
		    l = "%i" % len(work[key])
		except AttributeError:
		    l = "na"

		# add a result block.
		results.append( ResultBlock( "debug: path=%s, key=%s, type=%s, len=%s" % \
						 ( path2str(path),
						   key,
						   t, l), title = "") )

	    return results

   
Renderer
========

.. automodule:: CGATReportPlugins.Renderer
   :members:
   :inherited-members:
   :show-inheritance:



