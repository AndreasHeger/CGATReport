import os, sys, re, shelve, traceback, cPickle, types, itertools
import bsddb.db
import sqlalchemy

from SphinxReport.Component import *
from SphinxReport import Utils

def tracker2key( tracker ):
    '''derive cache filename from a tracker.'''

    modulename = os.path.split(tracker.__class__.__module__)[1]

    if hasattr( tracker, "func_name" ):
        name = tracker.func_name
    else:
        name = tracker.__class__.__name__

    return Utils.quote_filename( ".".join((modulename,name)))

class Cache( Component ):
    '''persistent storage for tracker results.'''

    def __init__(self, cache_name, mode = "a" ):

        global sphinxreport_cachedir
        self.cache_filename = None
        self._cache = None
        self.cache_name = cache_name 

        if sphinxreport_cachedir:
            
            try:
                if sphinxreport_cachedir != None: 
                    os.mkdir(sphinxreport_cachedir)
            except OSError, msg:
                pass
        
            if not os.path.exists(sphinxreport_cachedir): 
                raise OSError( "could not create directory %s: %s" % (sphinxreport_cachedir, msg ))

            self.cache_filename = os.path.join( sphinxreport_cachedir, cache_name )
            if mode == "r":
                if not os.path.exists( self.cache_filename ):
                    raise ValueError( "cache %s does not exist at %s" % \
                                          (self.cache_name,
                                           self.cache_filename))
                
            # on Windows XP, the shelve does not work, work without cache
            try:
                self._cache = shelve.open(self.cache_filename,"c", writeback = False)
                debug( "disp%s: using cache %s" % (id(self), self.cache_filename ))
                debug( "disp%s: keys in cache: %s" % (id(self,), str(self._cache.keys() ) ))                
            except bsddb.db.DBFileExistsError, msg:    
                warn("disp%s: could not open cache %s - continuing without. Error = %s" %\
                     (id(self), self.cache_filename, msg))
                self.cache_filename = None
                self._cache = None
        else:
            debug( "disp%s: not using cache"% (id(self),) )
            
    def __del__(self):

        if self._cache != None: 
            return
        self.debug( "closing cache %s" % self.cache_filename )
        self.debug( "keys in cache %s" % (str(self._cache.keys() ) ))
        self._cache.close()
        self._cache = None

    def keys( self):
        '''return keys in cache.'''
        if self._cache != None:
            return self._cache.keys()
        else:
            return []

    def __getitem__(self, key ):
        '''return data in cache.
        '''

        if self._cache == None:
            raise KeyError("no cache - key `%s` does not exist" % str(key))

        try:
            if key in self._cache: 
                result = self._cache[key]
                if result != None:
                    self.debug( "retrieved data for key '%s' from cache: %i" % (key, len(result)) )
                else:
                    self.warn( "retrieved None data for key '%s' from cache" % (key ))
            else:
                self.debug( "key '%s' not found in cache" % key )
                raise KeyError("cache does not contain %s" % str(key))

        except (bsddb.db.DBPageNotFoundError, bsddb.db.DBAccessError, cPickle.UnpicklingError, ValueError, EOFError), msg:
            self.warn( "could not get key '%s' or value for key in '%s': msg=%s" % (key,
                                                                                    self.cache_filename, 
                                                                                    msg) )
            raise KeyError("cache could not retrieve %s" % str(key))

        return result

    def __setitem__( self, key, data ):
        '''save data in cache.
        '''

        if self._cache != None:
            try:
                self._cache[key] = data
                self.debug( "saved data for key '%s' in cache" % key )
            except (bsddb.db.DBPageNotFoundError,bsddb.db.DBAccessError), msg:
                self.warn( "could not save key '%s' from '%s': msg=%s" % (key,
                                                                          self.cache_filename,
                                                                          msg) )
            # The following sync call is absolutely necessary when using 
            # the multiprocessing library (python 2.6.1). Otherwise the cache is emptied somewhere 
            # before the final call to close(). Even necessary, if writeback = False
            self._cache.sync()

        
