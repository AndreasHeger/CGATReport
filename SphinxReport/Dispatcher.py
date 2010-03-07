import os, sys, re, shelve, traceback, cPickle, types, itertools

from SphinxReport.ResultBlock import ResultBlock, ResultBlocks
from SphinxReport import DataTree
# from SphinxReport import Renderer
from SphinxReport.Component import *
from SphinxReport import Utils
from SphinxReport import Cache

VERBOSE=True

from odict import OrderedDict as odict

class Dispatcher(Component):
    """Dispatch the directives in the ``:report:`` directive
    to a :class:`Tracker`, class:`Transformer` and :class:`Renderer`.
    
    The dispatcher has three passes:

    1. Collect data from a :class:`Tracker`

    2. Transform data from a :class:`Transformer`

    3. Render data with a :class:`Renderer`

    This class adds the following options to the :term:`render` directive.

       :term:`groupby`: group data by :term:`track` or :term:`slice`.

    """

    def __init__(self, tracker, renderer, transformers = None ):
        '''render images using an instance of a :class:`Tracker.Tracker`
        to obtain data, an optional :class:`Transformer` to transform
        the data and a :class:`Renderer.Renderer` to render the output.
        '''
        Component.__init__(self)

        self.debug("starting dispatcher '%s': tracker='%s', renderer='%s', transformer:='%s'" % \
                  (str(self), str(tracker), str(renderer), str(transformers) ) )

        self.tracker = tracker
        self.renderer = renderer
        self.transformers = transformers

        try:
            if tracker.cache:
                self.cache = Cache.Cache( Cache.tracker2key(tracker) )
            else:
                self.cache = {}
        except AttributeError:
            self.cache = Cache.Cache( Cache.tracker2key(tracker) )

        self.data = DataTree.DataTree()

    def __del__(self):
        pass

    def getCaption( self ):
        """return a caption string."""
        return self.__doc__

    def parseArguments(self, *args, **kwargs ): 
        '''argument parsing.'''

        try: self.groupby = kwargs["groupby"]
        except KeyError: self.groupby = "slice"

        try: self.mInputTracks = [ x.strip() for x in kwargs["tracks"].split(",")]
        except KeyError: self.mInputTracks = None

        try: self.mInputSlices = [ x.strip() for x in kwargs["slices"].split(",")]
        except KeyError: self.mInputSlices = None

        try: self.mColumns = [ x.strip() for x in kwargs["columns"].split(",")]
        except KeyError: self.mColumns = None

    def getData( self, track, slice ):
        """get data for track and slice. Save data in persistent cache for further use."""

        key = "/".join( (str(track), str(slice)) )

        try:
            result = self.cache[ key ]
        except KeyError:
            result = None

        kwargs = {}
        if track != None: kwargs['track'] = track
        if slice != None: kwargs['slice'] = slice
        
        if result == None:
            try:
                result = self.tracker( **kwargs )
            except Exception, msg:
                self.warn( "exception for tracker '%s', track '%s' and slice '%s': msg=%s" % (str(self.tracker), track, slice, msg) )
                if VERBOSE: self.warn( traceback.format_exc() )
                raise

        self.cache[key] = result

        return result

    def buildTracksOrSlices( self, obj, fun, input_list = None ):
        '''determine tracks/slices from a tracker.'''
        result = []

        if not hasattr( obj, fun ):
            # not a tracker, hence no tracks/slices
            return True, result
        
        f = getattr(obj, fun )
        if input_list:
            all_entries = set(f( subset = None ))

            for s in input_list:
                if s in all_entries:
                    result.append( s )
                else:
                    result.extend( f( subset = [s,] ) )
#            else:
#                result = input_list
        else:
            result = f( subset = None )
        
        if type(result) in types.StringTypes: result=[result,]
        return False, result

    def buildTracks( self ):
        '''determine the tracks'''
        is_function, self.tracks = self.buildTracksOrSlices( self.tracker, 
                                                              "getTracks", 
                                                              self.mInputTracks )
        return is_function

    def buildSlices( self ):
        '''determine the slices'''
        is_function, self.slices = self.buildTracksOrSlices( self.tracker, 
                                                              "getSlices", 
                                                              self.mInputSlices )
        return is_function

    def collect( self ):
        '''collect all the data

        Data is stored in a two-level dictionary with track as
        the first level and slice as the second level.
        '''

        self.data = DataTree.DataTree()
        self.tracks = []
        self.slices = []

        is_function = self.buildTracks()

        if is_function:
            d = self.getData( None, None )
            self.data[ "all" ] = odict( (( "all", d),))
            self.debug( "%s: collecting data finished for function." % (self.tracker))
            return

        if len(self.tracks) == 0: 
            self.warn( "%s: no tracks found - no output" % self.tracker )
            raise ValueError( "no tracks found from %s" % (str(self.tracker)))

        self.buildSlices()

        tracks, slices = self.tracks, self.slices

        self.debug( "%s: collecting data started for %i pairs, %i tracks: %s, %i slices: %s" % (self.tracker, 
                                                                                           len(tracks) * len(slices), 
                                                                                           len(tracks), str(tracks),
                                                                                           len(slices), str(slices) ) )
        self.data = DataTree.DataTree()
        for track in tracks:
            self.data[track] =  DataTree.DataTree()
            if slices:
                for slice in slices:
                    d = self.getData( track, slice )
                    if not d: continue
                    self.data[track][slice] = DataTree.DataTree( d )
            else:
                d = self.getData( track, None )
                self.data[track] = DataTree.DataTree( d )

        self.debug( "%s: collecting data finished for %i pairs, %i tracks: %s, %i slices: %s" % (self.tracker, 
                                                                                            len(tracks) * len(slices), 
                                                                                            len(tracks), str(tracks),
                                                                                            len(slices), str(slices) ) )
        
    def transform(self): 
        '''call data transformers
        '''
        for transformer in self.transformers:
            self.debug( "%s: applying %s" % (self.renderer, transformer ))
            self.data = transformer( self.data )

    def render( self ):
        '''supply the :class:`Renderer.Renderer` with 
        data to render. The data supplied will depend on
        the ``group-by`` option.

        return resultblocks
        '''
        self.debug( "%s: rendering data started for %i items" % (self,
                                                                 len(self.data)))
        
        results = ResultBlocks( title="main" )

        try:
            renderer_nlevels = self.renderer.nlevels
        except AttributeError:
            renderer_nlevels = 0

        labels = self.data.getPaths()
        nlevels = len(labels)
        self.debug( "%s: rendering data started: %s labels, %s minimum, %s" %\
                        (self, str(nlevels), 
                         str(renderer_nlevels),
                         str(labels)[:100]))

        if nlevels >= 2:
            all_tracks, all_slices = labels[0], labels[1]
        elif nlevels == 1:
            all_tracks, all_slices = labels[0], []

        self.debug( "%s: rendering: groupby=%s, input: tracks=%s, slices=%s; output: tracks=%s, slices=%s" %\
                        (self, self.groupby, 
                         self.tracks[:20], 
                         self.slices[:20], 
                         all_tracks[:20], 
                         all_slices[:20])[:200])

        tracks, slices = self.tracks, self.slices

        if nlevels < renderer_nlevels:
            # add some dummy levels if levels is not enough
            d = self.data
            for x in range( renderer_nlevels - nlevels):
                d = odict( (("all", d ),))
            results.append( self.renderer( DataTree.DataTree(d), path = ("all",) ) )

        elif nlevels >= renderer_nlevels:
            if self.groupby == "none":
                paths = list(itertools.product( *labels[:-renderer_nlevels] ))
                for path in paths:
                    subtitle = "/".join( path )
                    work = self.data.getLeaf( path )
                    if not work: continue
                    for key,value in work.iteritems():
                        vals = DataTree.DataTree( odict( ((key,value),) ))
                        results.append( self.renderer( vals, path = path ))
            elif nlevels == renderer_nlevels and self.groupby == "track":
                for track in all_tracks:
                    vals = DataTree.DataTree( odict( ((track, self.data[track]),)))
                    results.append( self.renderer( vals, path = (track,) ) )
                
            elif nlevels > renderer_nlevels and self.groupby == "track":
                for track in all_tracks:
                    # slices can be absent
                    d = [ (x,self.data[track][x]) for x in all_slices if x in self.data[track] ]
                    if len(d) == 0: continue
                    vals = DataTree.DataTree( odict( d ) )
                    results.append( self.renderer( vals, path = (track,) ) )

            elif nlevels > renderer_nlevels and self.groupby == "slice" and len(self.slices) > 0:
                for slice in all_slices:
                    d = [ (x,self.data[x][slice]) for x in all_tracks if slice in self.data[x] ]
                    if len(d) == 0: continue
                    vals = DataTree.DataTree( odict( d ) )
                    results.append( self.renderer( vals, path = (slice,) ) )
            elif self.groupby == "all":
                results.append( self.renderer( self.data, path = () ) )
            else:
                results.append( self.renderer( self.data, path = () ) )

        if len(results) == 0:
            self.warn("tracker returned no data.")
            raise ValueError( "tracker returned no data." )

        self.debug( "%s: rendering data finished with %i blocks" % (self.tracker, len(results)))

        return results

    def __call__(self, *args, **kwargs ):

        try: self.parseArguments( *args, **kwargs )
        except: return Utils.buildException( "parsing" )

        self.debug( "profile: started: tracker: %s" % (self.tracker))

        try: self.collect()
        except: return Utils.buildException( "collection" )

        self.debug( "profile: finished: tracker: %s" % (self.tracker))

        labels = self.data.getPaths()
        self.debug( "%s: after collection: %i labels: %s" % (self,len(labels), str(labels)))
        
        try: self.transform()
        except: return Utils.buildException( "transformation" )

        labels = self.data.getPaths()
        self.debug( "%s: after transformation: %i labels: %s" % (self,len(labels), str(labels)))

        self.debug( "profile: started: renderer: %s" % (self.renderer))

        try: result = self.render()
        except: return Utils.buildException( "rendering" )

        self.debug( "profile: finished: renderer: %s" % (self.renderer))

        return result

        
    def getTracks( self ):
        '''return tracks used by the dispatcher.
        
        used for re-constructing call to cache.
        '''
        return self.tracks

    def getSlices( self ):
        '''return slices used by the dispatcher.
        
        used for re-constructing call to cache.
        '''
        return self.slices
