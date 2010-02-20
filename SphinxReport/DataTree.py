import collections, itertools
from logging import warn, log, debug, info

from SphinxReport.odict import OrderedDict as odict
from SphinxReport import Utils

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

def tree2table( data, transpose = False ):
    """build table from data.

    The table will be multi-level (main-rows and sub-rows), if:

       1. there is more than one column
       2. each cell within a row is a list or tuple

    returns matrix, row_headers, col_headers
    """

    labels = data.getPaths()
    if len(labels) < 2:
        raise ValueError( "expected at least two levels for building table, got %i: %s" %\
                              (len(labels), str(labels)))

    col_headers = [""] * (len(labels)-2) + labels[-1]
    ncols = len(col_headers)

    paths = list(itertools.product( *labels[1:-1] ))                
    header_offset = len(labels)-2
    matrix = []

    debug( "Datatree.buildTable: creating table with %i columns" % (len(col_headers)))

    ## the following can be made more efficient
    ## by better use of indices
    row_offset = 0
    row_headers = []

    # iterate over main rows
    for x, row in enumerate(labels[0]):

        first = True
        for xx, path in enumerate(paths):

            # get data - skip if there is None
            work = data.getLeaf( (row,) + path )
            if not work: continue

            # add row header only for first row (if there are sub-rows)
            if first: 
                row_headers.append( row )
                first = False
            else:
                row_headers.append("")

            # enter data for the first row
            row_data = [""] * ncols 
            for z, p in enumerate(path): 
                row_data[z] = p

            # check for multi-level rows
            is_container = True
            max_rows = None
            for y, column in enumerate(labels[-1]):
                if column not in work: continue
                if type(work[column]) not in Utils.ContainerTypes:
                    is_container = False
                    break
                if max_rows == None:
                    max_rows = len( work[column])
                elif max_rows != len( work[column]):
                    raise ValueError("multi-level rows - unequal lengths: %i != %i" % \
                                         (max_rows, len(work[column])))

            # add sub-rows
            if is_container:
                # multi-level rows
                for z in range( max_rows ):
                    for y, column in enumerate(labels[-1]):
                        try:
                            row_data[y+header_offset] = Utils.quote_rst(work[column][z])
                        except KeyError:
                            pass

                    if z < max_rows-1:
                        matrix.append( row_data )
                        row_headers.append( "" )
                        row_data = [""] * ncols 
            else:
                # single level row
                for y, column in enumerate(labels[-1]):
                    try:
                        row_data[y+header_offset] = Utils.quote_rst(work[column])
                    except KeyError:
                        pass

            matrix.append( row_data )

    if transpose:
        row_headers, col_headers = col_headers, row_headers
        matrix = zip( *matrix )

    # convert headers to string (might be None)
    row_headers = [str(x) for x in row_headers]
    col_headers = [str(x) for x in col_headers]

    return matrix, row_headers, col_headers

def fromCache( cache, 
               tracks = None, 
               slices = None,
               groupby = "slice" ):
    '''return a data tree from cache'''

    data = DataTree()
    keys = [ x.split("/") for x in cache.keys()]

    if tracks == None: tracks = set([ x[0] for x in keys] )
    else: tracks = tracks.split(",")

    if slices == None: slices = set([ x[1] for x in keys] )
    else: slices = slices.split(",")
    
    def tokey( track, slice ):
        return "/".join( (track,slice))

    if groupby == "slice" or groupby == "all":
        for slice in slices:
            data[slice]=odict()
            for track in tracks:
                data[slice][track] = cache[tokey(track,slice)]
    elif groupby == "track":
        for track in tracks:
            data[track]=odict()
            for slice in slices:
                data[track][slice] = cache[tokey(track,slice)]
    return data
    
