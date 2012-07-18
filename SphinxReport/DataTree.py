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
    if path:
        return "/".join(map(str,path))
    else:
        return ""

## This module needs to be properly refactored to use
## proper tree traversal algorithms. It currently is
## a collection of not very efficient hacks.

## The DataTree data structure is discontinued
## - a nested dictionary was more general from a user
##   point of view.
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
    def __str__(self):
        return str(self._data)
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
                    work[x] = DataTree()
                    work = work[x]

            work[path[-1]] = data

    def swop( self, level1, level2 ):
        '''swop two levels *level1* and *level2*.

        For example, swop(0,1) on paths (a/1/x, a/1/y, b/2/x, c/1/y)
        will result in 1/a/x, 1/a/y, 1/c/y, 2/b/x.
        
        Both levels must be smaller the len().
        '''
        nlevels = len(self.getPaths())
        if nlevels <= level1:
            raise IndexError("level out of range: %i >= %i" % (level1, nlevels))
        if nlevels <= level2:
            raise IndexError("level out of range: %i >= %i" % (level2, nlevels))
        if level1 == level2: return
        if level1 > level2:
            level1, level2 = level2, level1
            
        paths = self.getPaths()
        prefixes = paths[:level1]
        infixes = paths[level1+1:level2]
        suffixes = paths[level2+1:]

        if prefixes: prefixes = list(itertools.product( *prefixes ))
        else: prefixes = [(None,)]

        if infixes: infixes = list(itertools.product( *infixes ))
        else: infixes = [(None,)]

        if suffixes: suffixes = list(itertools.product( *suffixes ))
        else: suffixes = [(None,)]

        # write to new tree in order to ensure that labels
        # that exist in both level1 and level2 are not 
        # overwritten.
        newtree = DataTree()

        def _f(p): return tuple( [x for x in p if x != None] )

        for p1, p2 in itertools.product( paths[level1], paths[level2] ):
            for prefix, infix, suffix in itertools.product( prefixes, infixes, suffixes ):
                oldpath = _f( prefix + (p1,) + infix + (p2,) + suffix )
                newpath = _f(prefix + (p2,) + infix + (p1,) + suffix )
                # note: getLeaf, setLeaf are inefficient in this 
                # context as they traverse the tree again
                data = self.getLeaf( oldpath )
                if data == None: continue
                newtree.setLeaf( newpath, data )

        object.__setattr__( self, "_data", newtree._data)

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
        paths = self.getPaths()
        if len(paths) == 0: return "NA"
        else: return "< datatree: %s >" % str(paths)

    def __getattr__(self, name):
        return getattr(self._data, name)
    def __setattr__(self, name, value):
        setattr(self._data, name, value) 


def getPaths( work ):
    '''extract labels from data.

    returns a list of list with all labels within
    the nested dictionary of data.
    '''
    labels = []

    this_level = [work,]

    while 1:
        l, next_level = [], []
        for x in [ x for x in this_level if hasattr( x, "keys")]:
            l.extend( x.keys() )
            next_level.extend( x.values() )
        if not l: break
        labels.append( list(unique(l)) )
        this_level = next_level

    return labels

def getLeaf( work, path ):
    '''get leaf/branch at *path*.'''
    for x in path:
        try:
            work = work[x]
        except KeyError:
            work = None
            break
        except TypeError:
            work = None
            break

    return work

def setLeaf( work, path, data ):
    '''set leaf/branch at *path* to *data*.'''
    for x in path[:-1]:
        try:
            work = work[x]
        except KeyError:
            work[x] = odict()
            work = work[x]
    work[path[-1]] = data

def getPrefixes( work, level ):
    '''get all possible paths up to *level*.'''
    paths = getPaths(work)
    return list(itertools.product( *paths[:level] ))

def removeLevel( work, level ):
    '''remove *level* in *work*.'''
    prefixes = getPrefixes( work, level )
    for path in prefixes:
        leaf = getLeaf(work, path )
        # skip truncated branches
        if leaf == None: continue
        
        # delete all in leaf
        keys = leaf.keys()
        for key in keys:
            # there might be a subkey the same as key
            d = leaf[key]
            del leaf[key]
            try:
                for subkey, item in d.iteritems():
                    leaf[subkey] = item
            except AttributeError:
                # for items that are not dict
                setLeaf( work, path, d )
                
def swop( work, level1, level2 ):
    '''swop two levels *level1* and *level2*.

    For example, swop(0,1) on paths (a/1/x, a/1/y, b/2/y, b/2/x, c/1/y)
    will result in 1/a/x, 1/a/y, 1/c/y, 2/b/a, 2/b/x.

    Both levels must be smaller the len().

    The sort order in lower levels is preserved, i.e. 
    it will be 2/b/y, 2/b/x.
    '''
    paths = getPaths(work)
    nlevels = len(paths)
    if nlevels <= level1:
        raise IndexError("level out of range: %i >= %i" % (level1, nlevels))
    if nlevels <= level2:
        raise IndexError("level out of range: %i >= %i" % (level2, nlevels))
    if level1 == level2: return
    if level1 > level2:
        level1, level2 = level2, level1

    prefixes = paths[:level1]
    infixes = paths[level1+1:level2]
    suffixes = paths[level2+1:]

    if prefixes: prefixes = list(itertools.product( *prefixes ))
    else: prefixes = [(None,)]

    if infixes: infixes = list(itertools.product( *infixes ))
    else: infixes = [(None,)]

    if suffixes: suffixes = list(itertools.product( *suffixes ))
    else: suffixes = [(None,)]

    # write to new tree in order to ensure that labels
    # that exist in both level1 and level2 are not 
    # overwritten.
    newtree = odict()

    def _f(p): return tuple( [x for x in p if x != None] )

    for p1, p2 in itertools.product( paths[level1], paths[level2] ):

        for prefix, infix in itertools.product( prefixes, infixes ):

            w = getLeaf( work, _f( prefix + (p1,) + infix + (p2,) ) )
            subpaths = getPaths(w)
            if subpaths:
                suffixes = list( itertools.product( subpaths[0] ) )
            else:
                suffixes = [(None,)]

            for suffix in suffixes:
                oldpath = _f( prefix + (p1,) + infix + (p2,) + suffix )
                newpath = _f(prefix + (p2,) + infix + (p1,) + suffix )

                # note: getLeaf, setLeaf are inefficient in this 
                # context as they traverse the tree again
                data = getLeaf( work, oldpath )
                if data == None: continue
                setLeaf( newtree, newpath, data )
            
    return newtree

def removeLeaf( work, path ):
    '''remove leaf/branch at *path*.

    raises KeyError if path is not found.
    '''
    
    if len(path) == 0:
        work.clear()
    else:
        for x in path[:-1]:
            work = work[x]
        del work[path[-1]]
    return work

def removeEmptyLeaves( work ):
    '''traverse data tree in DFS order and remove empty 
    leaves.
    '''

    to_delete = []
    try:
        for label, w in work.iteritems():
            keep = removeEmptyLeaves( w )
            if not keep: to_delete.append(label)

        for label in to_delete:
            del work[label]

        if len(work) == 0:
            return False
        else:
            return True
    except AttributeError:
        pass

    # return True if not empty
    # numpy arrays do not test True if they contain
    # elements.
    try:
        return work != "" or work != None
    except ValueError:
        # for numpy arrays
        return len(work) > 0

def prettyprint(work):
    paths = work.getPaths()
    if len(paths) == 0: return "NA"
    else: return "< datatree: %s >" % str(paths)

def flatten(l, ltypes=(list, tuple)):
    '''flatten a nested list/tuple.'''

    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

def count_levels( labels ):
    '''count number of levels for each level in labels'''
    counts = []
    for x in labels:
        if type( x[0] ) in Utils.ContainerTypes:
            counts.append( len(x[0]) )
        else:
            counts.append( 1 )
    return counts

def tree2table( data, transpose = False ):
    """build table from data.

    The table will be multi-level (main-rows and sub-rows), if:

       1. there is more than one column
       2. each cell within a row is a list or tuple

    If any of the paths contain tuples/lists, these are
    expanded to extra columns as well.

    returns matrix, row_headers, col_headers
    """

    labels = getPaths( data )
    
    if len(labels) < 2:
        raise ValueError( "expected at least two levels for building table, got %i: %s" %\
                              (len(labels), str(labels)))

    effective_labels = count_levels( labels ) 
    # subtract last level (will be expanded) and 1 for row header
    effective_cols = sum( effective_labels[:-1] ) - 1

    col_headers = [""] * effective_cols + labels[-1]
    ncols = len(col_headers)

    paths = list(itertools.product( *labels[1:-1] ))                
    header_offset = effective_cols
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
            work = getLeaf( data, (row,) + path )
            if not work: continue

            row_data = [""] * ncols

            # add row header only for first row (if there are sub-rows)
            if first: 
                if type(row) in Utils.ContainerTypes:
                    row_headers.append( row[0] )
                    for z, p in enumerate( row[1:] ):
                        row_data[z] = p
                else:
                    row_headers.append( row )
                first = False
            else:
                row_headers.append("")

            # enter data for the first row
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

    if slices == None: slices = set([ x[1] for x in keys if len(x) > 1]  )
    else: slices = slices.split(",")
    
    def tokey( track, slice ):
        return "/".join( (track,slice))

    if not slices:
        for track in tracks:
            data[track] = cache[track]
    elif groupby == "slice" or groupby == "all":
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
    
