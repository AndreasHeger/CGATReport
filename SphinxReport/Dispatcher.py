import os, sys, re, shelve, traceback, cPickle, types, itertools

from SphinxReport.ResultBlock import ResultBlock, ResultBlocks
from SphinxReport import DataTree
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
        # add reference to self for access to tracks
        self.tracker.dispatcher = self
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

        self.groupby = kwargs.get("groupby", "slice")
        self.nocache = "nocache" in kwargs

        try: self.mInputTracks = [ x.strip() for x in kwargs["tracks"].split(",")]
        except KeyError: self.mInputTracks = None

        try: self.mInputSlices = [ x.strip() for x in kwargs["slices"].split(",")]
        except KeyError: self.mInputSlices = None
        
        try: self.mColumns = [ x.strip() for x in kwargs["columns"].split(",")]
        except KeyError: self.mColumns = None

    def getData( self, path ):
        """get data for track and slice. Save data in persistent cache for further use."""

        key = DataTree.path2str(path)

        result, fromcache = None, False
        if not self.nocache:
            try:
                result = self.cache[ key ]
                fromcache = True
            except KeyError:
                pass

        #kwargs = {}
        #if track != None: kwargs['track'] = track
        #if slice != None: kwargs['slice'] = slice
        
        if result == None:
            try:
                result = self.tracker( *path )
            except Exception, msg:
                self.warn( "exception for tracker '%s', path '%s': msg=%s" % (str(self.tracker),
                                                                              DataTree.path2str(path), 
                                                                              msg) )
                if VERBOSE: self.warn( traceback.format_exc() )
                raise
        
        if not self.nocache and not fromcache:
            self.cache[key] = result

        return result

    def buildTracksOrSlices( self, obj, attr, fun, input_list = None ):
        '''determine tracks/slices from a tracker.

        All possible tracks/slices are collected from the tracker via
        the *attr* attribute or *fun* function.

        If input_list is given, they are then filtered by:

        * exact matches to entries in input_list
        * pattern matches to entries in input list that starting with "r("
        
        If there is no match, the entry in input_list is submitted to 
        tracker.fun as a ``subset`` parameter for custom processing.
        '''
        if not hasattr( obj, fun ) and not hasattr( obj, attr ):
            # not a tracker, hence no tracks/slices
            return True, []

        def filter( all_entries, input_list ):
            result = []
            if input_list:
                for s in input_list:
                    if s in all_entries:
                        # collect exact matches
                        result.append( s )
                    elif s.startswith("r(") and s.endswith(")"):
                        # collect pattern matches:
                        # remove r()
                        s = s[2:-1] 
                        # remove flanking quotation marks
                        if s[0] in ('"', "'") and s[-1] in ('"', "'"): s = s[1:-1]
                        rx = re.compile( s )
                        result.extend( [ x for x in all_entries if rx.search( str(x) ) ] )
            else:
                result = all_entries
            return result

        if hasattr( obj, attr ):
            # get tracks/slices via attribute
            all_entries = getattr( obj, attr )
            if all_entries:
                return False, filter( all_entries, input_list )

        # get tracks/slices via function call
        # function
        f = getattr(obj, fun )
        if input_list:
            all_entries = set(f( subset = None ))
            result = filter( all_entries, input_list )
        else:
            result = f( subset = None )
            
        if type(result) in types.StringTypes: result=[result,]

        return False, result

    def getDataPaths( self, obj ):
        '''determine data paths from a tracker.

        If obj is a function, returns True and an empty list.

        returns False and a list of lists.
        '''
        data_paths = []

        
        if hasattr( obj, 'paths' ):
            data_paths = getattr( obj, 'paths' )
        elif hasattr( obj, 'getPaths' ):
            data_paths = getattr( obj, 'getPaths' )

        if not data_paths:
            if hasattr( obj, 'tracks' ):
                data_paths = [ getattr( obj, 'tracks' ) ]
            elif hasattr( obj, 'getTracks' ):
                data_paths = [ getattr( obj, 'getTracks' ) ]
            else: 
                # is a function
                return True, []
            
            # get slices
            if hasattr( obj, 'slices' ):
                data_paths.append( getattr( obj, 'slices' ) )
            elif hasattr( obj, 'getSlices' ):
                data_paths.append( getattr( obj, 'getSlices' ) )
                
        # sanity check on data_paths. 
        # Replace strings with one-element tuples
        for x,y in enumerate(data_paths):
            if type(y) in types.StringTypes: data_paths[x]=[y,]
            
        return False, data_paths


    def filterDataPaths( self, datapaths ):
        '''filter *datapaths*.

        returns the filtered data paths.
        '''
        
        if not datapaths: return

        def _filter( all_entries, input_list ):
            result = []
            for s in input_list:
                if s in all_entries:
                    # collect exact matches
                    result.append( s )
                elif s.startswith("r(") and s.endswith(")"):
                    # collect pattern matches:
                    # remove r()
                    s = s[2:-1] 
                    # remove flanking quotation marks
                    if s[0] in ('"', "'") and s[-1] in ('"', "'"): s = s[1:-1]
                    rx = re.compile( s )
                    result.extend( [ x for x in all_entries if rx.search( str(x) ) ] )
            return result

        if self.mInputTracks:
            datapaths[0] = _filter( datapaths[0], self.mInputTracks )
        
        if self.mInputSlices:
            datapaths[1] = _filter( datapaths[1], self.mInputTracks )

        return datapaths

    def collect( self ):
        '''collect all data.

        Data is stored in a multi-level dictionary (DataTree)
        '''

        self.data = DataTree.DataTree()

        is_function, datapaths = self.getDataPaths(self.tracker)
        
        # if function, no datapaths
        if is_function:
            d = self.getData( None )
            self.data[ "all" ] = odict( (( "all", d),))
            self.debug( "%s: collecting data finished for function." % (self.tracker))
            return

        # if no tracks, error
        if len(datapaths) == 0 or len(datapaths[0]) == 0:
            self.warn( "%s: no tracks found - no output" % self.tracker )
            raise ValueError( "no tracks found from %s" % self.tracker )
        
        # filter data paths
        datapaths = self.filterDataPaths( datapaths )

        # if no tracks, error
        if len(datapaths) == 0 or len(datapaths[0]) == 0:
            self.warn( "%s: no tracks found - no output" % self.tracker )
            raise ValueError( "no tracks found from %s" % self.tracker )

        all_paths = list(itertools.product( *datapaths ))
        self.debug( "%s: collecting data started for %i data paths" % (self.tracker, 
                                                                       len( all_paths) ) )

        self.data = DataTree.DataTree()
        for path in all_paths:
            
            d = self.getData( path )

            # ignore empty data sets
            if d == None: continue

            # save in data tree as leaf
            self.data.setLeaf( path, d )

        self.debug( "%s: collecting data finished for %i data paths" % (self.tracker, 
                                                                       len( all_paths) ) )

    def transform(self): 
        '''call data transformers and group tree
        '''
        for transformer in self.transformers:
            self.debug( "%s: applying %s" % (self.renderer, transformer ))
            self.data = transformer( self.data )

    def group( self ):
        '''rearrange data tree for grouping.

        and set group level.
        '''

        data_paths = self.data.getPaths()
        nlevels = len(data_paths)

        # get number of levels required by renderer
        try:
            renderer_nlevels = self.renderer.nlevels
        except AttributeError:
            renderer_nlevels = 0
        
        if self.groupby == "none":
            self.group_level = renderer_nlevels
        
        elif self.groupby == "track":
            # track is first level
            self.group_level = 0
            
        elif self.groupby == "slice":
            # rearrange tracks and slices in data tree
            if nlevels <= 2 :
                raise ValueError( "grouping by slice, but only %i levels in data tree" % nlevels)

            self.data.swop( 0, 1)
            self.group_level = 0
            
        elif self.groupby == "all":
            # group everthing together
            self.group_level = -1
        else:
            # neither group by slice or track ("ungrouped")
            self.group_level = -1

    def render( self ):
        '''supply the :class:`Renderer.Renderer` with the data to render. 
        
        The data supplied will depend on the ``groupby`` option.

        return resultblocks
        '''
        self.debug( "%s: rendering data started for %i items" % (self,
                                                                 len(self.data)))
        
        results = ResultBlocks( title="main" )

        # get number of levels required by renderer
        try:
            renderer_nlevels = self.renderer.nlevels
        except AttributeError:
            renderer_nlevels = 0

        data_paths = self.data.getPaths()
        nlevels = len(data_paths)

        group_level = self.group_level

        self.debug( "%s: rendering data started. levels=%i, required levels>=%i, group_level=%i, data_paths=%s" %\
                        (self, nlevels, 
                         renderer_nlevels,
                         group_level,
                         str(data_paths)[:100]))

        if nlevels < renderer_nlevels:
            # add some dummy levels if levels is not enough
            d = self.data
            for x in range( renderer_nlevels - nlevels):
                d = odict( (("all", d ),))
            results.append( self.renderer( DataTree.DataTree(d), path = ("all",) ) )

        elif group_level < 0:
            # no grouping
            results.append( self.renderer( self.data, path = () ) )
        else:
            # group at level group_level
            paths = list(itertools.product( *data_paths[:group_level+1] ))
            for path in paths:
                work = self.data.getLeaf( path )
                if not work: continue
                results.append( self.renderer( work, path = path ))

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

        data_paths = self.data.getPaths()
        self.debug( "%s: after collection: %i data_paths: %s" % (self,len(data_paths), str(data_paths)))
        
        try: self.transform()
        except: return Utils.buildException( "transformation" )

        data_paths = self.data.getPaths()
        self.debug( "%s: after transformation: %i data_paths: %s" % (self,len(data_paths), str(data_paths)))

        try: self.group()
        except: return Utils.buildException( "grouping" )

        data_paths = self.data.getPaths()
        self.debug( "%s: after grouping: %i data_paths: %s" % (self,len(data_paths), str(data_paths)))

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
