import collections
from logging import warn, log, debug, info

from SphinxReport.odict import OrderedDict as odict

def unique( iterables ):
    s = set()
    for x in iterables:
        if x not in s:
            yield x
            s.add(x)

def path2str( path ):
    '''convert path to printable string.'''
    return "/".join(path)

class DataTree( object ):
    '''a DataTree.

    A data tree is a nested dictionary. A branch or
    leaf is identified by a :term:`path`, a tuple
    of dictionary keys. For example: the :term:path 
    ("data1","slice1","distance") returns the
    data at dictionary["data1"]["slice1"]["distance"].

    Note that it will never return a KeyError, but
    will return an empty dictionary for a new tree.
    '''
    
    slots = "_data"

    def __init__(self, data = None ):
        # do not put this in argument list, as
        # it will always refer to the same object.
        # if not data: data = collections.defaultdict( odict )
        if not data: data = odict()
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

        return labels

    def getLeaf( self, path ):
        '''get leaf/branch at *path*.'''
        work = self._data
        for x in path:
            try:
                work = work[x]
            except KeyError:
                work = None
                break
        return work

    def setLeaf( self, path, data ):
        '''set leaf/branch at *path* to *data*.'''
        if len(path) == 0:
            object.__setattr__( self, "_data", data)
        else:
            work = self._data
            for x in path[:-1]:
                try:
                    work = work[x]
                except KeyError:
                    work = None
                    break
            work[path[-1]] = data

    def removeLeaf( self, path ):
        '''remove leaf/branch at *path*.'''
        if len(path) == 0:
            object.__setattr__( self, "_data", odict)
        else:
            work = self._data
            for x in path[:-1]:
                try:
                    work = work[x]
                except KeyError:
                    work = None
                    break
            del work[path[-1]]
        
    def __str__(self):
        return "< datatree: %s >" % str(self.getPaths() )

    def __getattr__(self, name):
        return getattr(self._data, name)
    def __setattr__(self, name, value):
        setattr(self._data, name, value) 

