import os, sys, re, shelve, traceback, cPickle, types, itertools

import bsddb.db
import sqlalchemy
import collections

from ResultBlock import ResultBlock, ResultBlocks
import DataTree
import Renderer
import report_directive
from Reporter import *

# Some renderers will build several objects.
# Use these two rst levels to separate individual
# entries. Set to None if not separation.
VERBOSE=True

# from logging import warn, log, debug, info
# import logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s %(levelname)s %(message)s',
#     stream = open( "sphinxreport.log", "a" ) )

# # for cachedir
# cachedir = None
# if not os.path.exists("conf.py"):
#     raise IOError( "could not find conf.py" )
# execfile( "conf.py" )

from odict import OrderedDict as odict

class Dispatcher(Reporter):
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
        Reporter.__init__(self)

        self.debug("starting dispatcher '%s': tracker='%s', renderer='%s', transformer:='%s'" % \
                  (str(self), str(tracker), str(renderer), str(transformers) ) )

        self.mTracker = tracker
        self.mRenderer = renderer
        self.mTransformers = transformers

        global cachedir
        self.mCacheFile = None
        self._cache = None

        if cachedir:

            try:
                if cachedir != None: 
                    os.mkdir(cachedir)
            except OSError, msg:
                pass
        
            if not os.path.exists(cachedir): 
                raise OSError( "could not create directory %s: %s" % (cachedir, msg ))

                
            modulename = os.path.split(tracker.__class__.__module__)[1]

            if hasattr( tracker, "func_name" ):
                name = tracker.func_name
            else:
                name = tracker.__class__.__name__

            self.mCacheFile = os.path.join( cachedir, 
                                            report_directive.quoted( ".".join((modulename,name))))
                                                                               
            # on Windows XP, the shelve does not work, work without cache
            try:
                self._cache = shelve.open(self.mCacheFile,"c", writeback = False)
                debug( "disp%s: using cache %s" % (id(self), self.mCacheFile ))
                debug( "disp%s: keys in cache: %s" % (id(self,), str(self._cache.keys() ) ))                
            except bsddb.db.DBFileExistsError, msg:    
                warn("disp%s: could not open cache %s - continuing without. Error = %s" %\
                     (id(self), self.mCacheFile, msg))
                self.mCacheFile = None
                self._cache = None

        else:
            debug( "disp%s: not using cache"% (id(self),) )

        self.mData = DataTree.DataTree()

    def __del__(self):
        
        if self._cache != None: 
            return
            self.debug( "closing cache %s" % self.mCacheFile )
            self.debug( "keys in cache %s" % (str(self._cache.keys() ) ))
            self._cache.close()
            self._cache = None

    def getCaption( self ):
        """return a caption string."""
        return self.__doc__

    def parseArguments(self, *args, **kwargs ): 
        '''argument parsing.'''

        try: self.mGroupBy = kwargs["groupby"]
        except KeyError: self.mGroupBy = "slice"

        try: self.mInputTracks = [ x.strip() for x in kwargs["tracks"].split(",")]
        except KeyError: self.mInputTracks = None

        try: self.mInputSlices = [ x.strip() for x in kwargs["slices"].split(",")]
        except KeyError: self.mInputSlices = None

        try: self.mColumns = [ x.strip() for x in kwargs["columns"].split(",")]
        except KeyError: self.mColumns = None

    def getDataFromCache( self, key ):

        result = None
        if self._cache != None:
            try:
                if key in self._cache: 
                    result = self._cache[key]
                    self.debug( "retrieved data for key '%s' from cache: %i" % (key, len(result)) )
                else:
                    result = None
                    self.debug( "key '%s' not found in cache" % key )

            except (bsddb.db.DBPageNotFoundError, bsddb.db.DBAccessError, cPickle.UnpicklingError, ValueError, EOFError), msg:
                self.warn( "could not get key '%s' or value for key in '%s': msg=%s" % (key,self.mCacheFile, msg) )
        return result

    def saveDataInCache( self, key, data ):

        if self._cache != None:
            try:
                self._cache[key] = data
                self.debug( "saved data for key '%s' in cache" % key )
            except (bsddb.db.DBPageNotFoundError,bsddb.db.DBAccessError), msg:
                self.warn( "could not save key '%s' from '%s': msg=%s" % (key,self.mCacheFile,msg) )
            # The following sync call is absolutely necessary when using 
            # the multiprocessing library (python 2.6.1). Otherwise the cache is emptied somewhere 
            # before the final call to close(). Even necessary, if writeback = False
            self._cache.sync()

    def getData( self, track, slice):
        """get data for track and slice. Save data in persistent cache for further use."""

        key = ":".join( (str(track), str(slice)) )
        result = self.getDataFromCache( key )

        kwargs = {}
        if track != None: kwargs['track'] = track
        if slice != None: kwargs['slice'] = slice
        
        if result == None:
            try:
                result = self.mTracker( **kwargs )
            except Exception, msg:
                self.warn( "exception for tracker '%s', track '%s' and slice '%s': msg=%s" % (str(self.mTracker), track, slice, msg) )
                if VERBOSE: self.warn( traceback.format_exc() )
                raise

            # try:
            #     # this messy code distinguishes between the result of functors
            #     # and true functions that have been wrapped with the DataTypes
            #     # decorators by checking if it has a __len__ method.
            #     if not hasattr( self.mTracker, "__len__"):
            #         result = self.mTracker( **kwargs )
            #     else:
            #         result = self.mTracker
            #     self.debug( "collected data for key '%s': %i" % (key, len(result)) )
            # except Exception, msg:
            #     self.warn( "exception for tracker '%s', track '%s' and slice '%s': msg=%s" % (str(self.mTracker), track, slice, msg) )
            #     if VERBOSE: self.warn( traceback.format_exc() )
            #     result = []
            
        self.saveDataInCache( key, result )

        return result

    def buildTracks( self ):
        '''decide which tracks to collect.'''

        if hasattr( self.mTracker, "getTracks" ):
            tracks = self.mTracker.getTracks( subset = None )
        else:
            # not a Tracker, hence no tracks
            self.mTracks = []
            return True

        # do we have a subset specified
        if self.mInputTracks != None:
            # if it starts with -, remove
            if self.mInputTracks[0].startswith("-"):
                f = set(self.mTracks)
                f.add( self.mTracks[0][1:] )
                tracks = [ t for t in tracks if t not in f ]
            else:
                # get tracks again, this time with subset
                tracks = self.mTracker.getTracks( subset = self.mInputTracks )
        
        self.mTracks = tracks
        return False

    def buildSlices( self ):
        '''determine the slices through the data'''

        # first get all slices without subsets and check if all
        # specified slices are available. 

        if not hasattr( self.mTracker, "getSlices" ):
            # not a tracker, hence no slices
            slices = []
        elif self.mInputSlices:
            all_slices = set(self.mTracker.getSlices( subset = None ))
            for s in self.mInputSlices:
                if s not in all_slices:
                    slices = self.mTracker.getSlices( subset = self.mInputSlices )
                    break
            else:
                slices = self.mInputSlices
        else:
            slices = self.mTracker.getSlices( subset = None )
        
        if type(slices) in types.StringTypes: slices=[slices,]
        # if len(slices) == 0: slices=[None,]
        
        self.mSlices = slices

    def collect( self ):
        '''collect all the data

        Data is stored in a two-level dictionary with track as
        the first level and slice as the second level.
        '''

        self.mData = DataTree.DataTree()
        self.mTracks = []
        self.mSlices = []

        is_function = self.buildTracks()

        if is_function:
            d = self.getData( None, None )
            self.mData[ "all" ] = odict( (( "all", d),))
            self.debug( "%s: collecting data finished for function." % (self.mTracker))
            return

        if len(self.mTracks) == 0: 
            self.warn( "%s: no tracks found - no output" % self.mTracker )
            raise ValueError( "no tracks found from %s" % (str(self.mTracker)))

        self.buildSlices()

        tracks, slices = self.mTracks, self.mSlices

        self.debug( "%s: collecting data started for %i pairs, %i tracks: %s, %i slices: %s" % (self.mTracker, 
                                                                                           len(tracks) * len(slices), 
                                                                                           len(tracks), str(tracks),
                                                                                           len(slices), str(slices) ) )
        self.mData = DataTree.DataTree()
        for track in tracks:
            self.mData[track] =  DataTree.DataTree()
            if slices:
                for slice in slices:
                    d = self.getData( track, slice )
                    if not d: continue
                    self.mData[track][slice] = DataTree.DataTree( d )
            else:
                d = self.getData( track, None )
                self.mData[track] = DataTree.DataTree( d )

        self.debug( "%s: collecting data finished for %i pairs, %i tracks: %s, %i slices: %s" % (self.mTracker, 
                                                                                            len(tracks) * len(slices), 
                                                                                            len(tracks), str(tracks),
                                                                                            len(slices), str(slices) ) )
        
    def transform(self): 
        '''call data transformers
        '''
        for transformer in self.mTransformers:
            self.debug( "%s: applying %s" % (self.mRenderer, transformer ))
            self.mData = transformer( self.mData )

    def render( self ):
        '''supply the :class:`Renderer.Renderer` with 
        data to render. The data supplied will depend on
        the ``group-by`` option.

        return resultblocks
        '''
        self.debug( "%s: rendering data started for %i items" % (self,len(self.mData)))

        results = ResultBlocks( title="main" )

        labels = self.mData.getPaths()
        nlevels = len(labels)
        self.debug( "%s: rendering data started: %s labels, %s minimum, %s" %\
                        (self, str(nlevels), str(self.mRenderer.nlevels), str(labels)))

        if nlevels >= 2:
            all_tracks, all_slices = labels[0], labels[1]
        elif nlevels == 1:
            all_tracks, all_slices = labels[0], []

        self.debug( "%s: rendering: groupby=%s, input: tracks=%s, slices=%s; output: tracks=%s, slices=%s" %\
                   (self, self.mGroupBy, self.mTracks, self.mSlices, all_tracks, all_slices))

        tracks, slices = self.mTracks, self.mSlices

        if nlevels < self.mRenderer.nlevels:
            # add some dummy levels if levels is not enough
            d = self.mData
            for x in range( self.mRenderer.nlevels - nlevels):
                d = odict( (("all", d ),))
            results.append( self.mRenderer( DataTree.DataTree(d), path = ("all",) ) )

        elif nlevels >= self.mRenderer.nlevels:
            if self.mGroupBy == "none":
                paths = list(itertools.product( *labels[:-self.mRenderer.nlevels] ))
                for path in paths:
                    subtitle = "/".join( path )
                    work = self.mData.getLeaf( path )
                    if not work: continue
                    for key,value in work.iteritems():
                        vals = DataTree.DataTree( odict( ((key,value),) ))
                        results.append( self.mRenderer( vals, path = path ))
            elif nlevels == self.mRenderer.nlevels and self.mGroupBy == "track":
                for track in all_tracks:
                    vals = DataTree.DataTree( odict( ((track, self.mData[track]),)))
                    results.append( self.mRenderer( vals, path = (track,) ) )
                
            elif nlevels > self.mRenderer.nlevels and self.mGroupBy == "track":
                for track in all_tracks:
                    # slices can be absent
                    d = [ (x,self.mData[track][x]) for x in all_slices if x in self.mData[track] ]
                    if len(d) == 0: continue
                    vals = DataTree.DataTree( odict( d ) )
                    results.append( self.mRenderer( vals, path = (track,) ) )

            elif nlevels > self.mRenderer.nlevels and self.mGroupBy == "slice" and len(self.mSlices) > 0:
                for slice in all_slices:
                    d = [ (x,self.mData[x][slice]) for x in all_tracks if slice in self.mData[x] ]
                    if len(d) == 0: continue
                    vals = DataTree.DataTree( odict( d ) )
                    results.append( self.mRenderer( vals, path = (slice,) ) )
            elif self.mGroupBy == "all":
                results.append( self.mRenderer( self.mData, path = () ) )
            else:
                results.append( self.mRenderer( self.mData, path = () ) )

        if len(results) == 0:
            self.warn("tracker returned no data.")
            raise ValueError( "tracker returned no data." )

        self.debug( "%s: rendering data finished with %i blocks" % (self.mTracker, len(results)))

        return results

    def __call__(self, *args, **kwargs ):

        try: self.parseArguments( *args, **kwargs )
        except: return Renderer.buildException( "parsing" )

        try: self.collect()
        except: return Renderer.buildException( "collection" )

        labels = self.mData.getPaths()
        self.debug( "%s: after collection: %i labels: %s" % (self,len(labels), str(labels)))
        
        try: self.transform()
        except: return Renderer.buildException( "transformation" )

        labels = self.mData.getPaths()
        self.debug( "%s: after transformation: %i labels: %s" % (self,len(labels), str(labels)))

        try: result = self.render()
        except: return Renderer.buildException( "rendering" )
        
        return result

        

