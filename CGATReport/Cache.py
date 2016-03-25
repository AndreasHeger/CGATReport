import os
import shelve
import pickle

from CGATReport.Component import Component
from CGATReport import Utils

# Python 3 - bsddb.db not available
# import bsddb.db


def tracker2key(tracker):
    '''derive cache filename from a tracker.'''

    modulename = tracker.__module__
    try:
        # works for functions (def)
        name = tracker.__name__
    except AttributeError:
        # works for functors (class)
        name = tracker.__class__.__name__

    return Utils.quote_filename(".".join((modulename, name)))


class Cache(Component):

    '''persistent storage for tracker results.'''

    def __init__(self, cache_name, mode="a"):

        Component.__init__(self)

        self.cache_filename = None
        self._cache = None
        self.cache_name = cache_name
        if "report_cachedir" in Utils.PARAMS:
            self.cache_dir = Utils.PARAMS["report_cachedir"]
        else:
            self.cache_dir = None

        if self.cache_dir:

            try:
                os.mkdir(self.cache_dir)
            except OSError as msg:
                pass

            if not os.path.exists(self.cache_dir):
                raise OSError("could not create directory %s: %s" %
                              (self.cache_dir, msg))

            self.cache_filename = os.path.join(self.cache_dir, cache_name)

            if mode == "r":
                if not os.path.exists(self.cache_filename):
                    raise ValueError("cache %s does not exist at %s" %
                                     (self.cache_name,
                                      self.cache_filename))

            # on Windows XP, the shelve does not work, work without cache
            try:
                self._cache = shelve.open(
                    self.cache_filename, "c", writeback=False)
                self.debug("disp%s: using cache %s" %
                           (id(self), self.cache_filename))
                self.debug("disp%s: keys in cache: %s" %
                           (id(self,), str(list(self._cache.keys()))))
            # except bsddb.db.DBFileExistsError as msg:
            except OSError as msg:
                self.warn(
                    "disp%s: could not open cache %s - continuing without. Error = %s" %
                    (id(self), self.cache_filename, msg))
                self.cache_filename = None
                self._cache = None
        else:
            self.debug("disp%s: not using cache" % (id(self),))

    def __del__(self):

        if self._cache is not None:
            return
        self.debug("closing cache %s" % self.cache_filename)
        self.debug("keys in cache %s" % (str(list(self._cache.keys()))))
        self._cache.close()
        self._cache = None

    def keys(self):
        '''return keys in cache.'''
        if self._cache is not None:
            return list(self._cache.keys())
        else:
            return []

    def __getitem__(self, key):
        '''return data in cache.
        '''

        if self._cache is None:
            raise KeyError("no cache - key `%s` does not exist" % str(key))

        try:
            if key in self._cache:
                result = self._cache[key]
                if result is not None:
                    self.debug(
                        "retrieved data for key '%s' from cache" % (key))
                else:
                    self.warn(
                        "retrieved None data for key '%s' from cache" % (key))
            else:
                self.debug("key '%s' not found in cache" % key)
                raise KeyError("cache does not contain %s" % str(key))

        # except (bsddb.db.DBPageNotFoundError, bsddb.db.DBAccessError,
        # pickle.UnpicklingError, ValueError, EOFError) as msg:
        except (pickle.UnpicklingError, ValueError, EOFError) as msg:
            self.warn("could not get key '%s' or value for key in '%s': msg=%s" %
                      (key,
                       self.cache_filename,
                       msg))
            raise KeyError("cache could not retrieve %s" % str(key))

        return result

    def __setitem__(self, key, data):
        '''save data in cache.
        '''

        if self._cache is not None:
            # do not store data frames in cache until
            # best method is clear
            try:
                self._cache[key] = data
                self.debug("saved data for key '%s' in cache" % key)
            # except (bsddb.db.DBPageNotFoundError,bsddb.db.DBAccessError) as
            # msg:
            except (OSError) as msg:
                self.warn("could not save key '%s' from '%s': msg=%s" %
                          (key,
                           self.cache_filename,
                           msg))
            # The following sync call is absolutely necessary when
            # using the multiprocessing library (python
            # 2.6.1). Otherwise the cache is emptied somewhere before
            # the final call to close(). Even necessary, if writeback
            # = False
            self._cache.sync()
