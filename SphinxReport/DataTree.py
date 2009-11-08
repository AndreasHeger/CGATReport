from odict import OrderedDict as odict
import collections
from logging import warn, log, debug, info

def unique( iterables ):
    s = set()
    for x in iterables:
        if x not in s:
            yield x
            s.add(x)

class DataTree( object ):
    slots = "_data"

    def __init__(self, data = None ):
        # do not put this in argument list, as
        # it will always refer to the same object.
        if not data: data = collections.defaultdict( odict )
        object.__setattr__( self, "_data", data)

    def __iter__(self):
        return self._data.__iter__()
    def __getitem__(self, key):
        return self._data.__getitem__(key)
    def __delitem__(self, key):
        return self._data.__delitem__(key)
    def __setitem__(self, key,value):
        return self._data.__setitem__(key,value)
    def __len__(self):
        return self._data.__len__()
    def getPaths( self ):
        '''extract labels from data.

        returns a list of list with all labels within
        the nested dictionary of data.
        '''
        labels = []
        
        this_level = [self._data,]

        while 1:
            l, next_level = [], []
            for x in [ x for x in this_level if hasattr( x, "keys")]:
                l.extend( x.keys() )
                next_level.extend( x.values() )
            if not l: break
            labels.append( list(unique(l)) )
            this_level = next_level

        debug( "%s: found the following labels: %s" % (str(self),labels))
        return labels

    def getLeaf( self, path ):
        '''get leaf in hierarchy at path.'''
        work = self._data
        for x in path:
            try:
                work = work[x]
            except KeyError:
                work = None
                break
        return work

    def setLeaf( self, path, data ):
        '''set leaf.'''
        work = self._data
        for x in path[:-1]:
            try:
                work = work[x]
            except KeyError:
                work = None
                break
        work[path[-1]] = data
    def __str__(self):
        return "< datatree: _data=%s>" % str(self._data)

    def __getattr__(self, name):
        return getattr(self._data, name)
    def __setattr__(self, name, value):
        setattr(self._data, name, value) 

