import collections
import itertools
from collections import OrderedDict as odict
import pandas
from CGATReport import Utils
from CGATReport import Component

def unique(iterables):
    s = set()
    for x in iterables:
        if x not in s:
            yield x
            s.add(x)


def path2str(path):
    '''convert path to printable string.'''
    if path is None:
        return ""
    if Utils.isString(path):
        return path
    try:
        return "/".join(map(str, path))
    except:
        return str(path)


def str2path(s):
    '''convert printable string to path.'''
    if Utils.isString(s):
        return s.split("/")
    return [s]

# This module needs to be properly refactored to use
# proper tree traversal algorithms. It currently is
# a collection of not very efficient hacks.

# The DataTree data structure is discontinued
# - a nested dictionary was more general from a user
# point of view.
class DataTree(object):
    '''a DataTree.

    A data tree is a nested dictionary. A branch or
    leaf is identified by a:term:`path`, a tuple
    of dictionary keys. For example: the:term:path
    ("data1","slice1","distance") returns the
    data at dictionary["data1"]["slice1"]["distance"].

    Note that it will never return a KeyError, but
    will return an empty dictionary for a new tree.
    '''

    slots = "_data"

    def __init__(self, data=None):
        if not data:
            data = odict()
        object.__setattr__(self, "_data", data)

    def __iter__(self):
        return self._data.__iter__()

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __delitem__(self, key):
        return self._data.__delitem__(key)

    def __setitem__(self, key, value):
        return self._data.__setitem__(key, value)

    def __len__(self):
        return self._data.__len__()

    def getPaths(self):
        '''extract labels from data.

        returns a list of list with all labels within
        the nested dictionary of data.
        '''
        labels = []

        this_level = [self._data, ]

        while 1:
            l, next_level = [], []
            for x in [x for x in this_level if hasattr(x, "keys")]:
                l.extend(list(x.keys()))
                next_level.extend(list(x.values()))
            if not l:
                break
            labels.append(list(unique(l)))
            this_level = next_level

        return labels

    def getLeaf(self, path):
        '''get leaf/branch at *path*.'''
        work = self._data
        for x in path:
            try:
                work = work[x]
            except KeyError:
                work = None
                break
        return work

    def setLeaf(self, path, data):
        '''set leaf/branch at *path* to *data*.'''
        if len(path) == 0:
            object.__setattr__(self, "_data", data)
        else:
            work = self._data
            for x in path[:-1]:
                try:
                    work = work[x]
                except KeyError:
                    work[x] = DataTree()
                    work = work[x]

            work[path[-1]] = data

    def swop(self, level1, level2):
        '''swop two levels *level1* and *level2*.

        For example, swop(0,1) on paths (a/1/x, a/1/y, b/2/x, c/1/y)
        will result in 1/a/x, 1/a/y, 1/c/y, 2/b/x.

        Both levels must be smaller the len().
        '''
        nlevels = len(self.getPaths())
        if nlevels <= level1:
            raise IndexError("level out of range: %i >= %i" %
                             (level1, nlevels))
        if nlevels <= level2:
            raise IndexError("level out of range: %i >= %i" %
                             (level2, nlevels))
        if level1 == level2:
            return
        if level1 > level2:
            level1, level2 = level2, level1

        paths = self.getPaths()
        prefixes = paths[:level1]
        infixes = paths[level1 + 1:level2]
        suffixes = paths[level2 + 1:]

        if prefixes:
            prefixes = list(itertools.product(*prefixes))
        else:
            prefixes = [(None,)]

        if infixes:
            infixes = list(itertools.product(*infixes))
        else:
            infixes = [(None,)]

        if suffixes:
            suffixes = list(itertools.product(*suffixes))
        else:
            suffixes = [(None,)]

        # write to new tree in order to ensure that labels
        # that exist in both level1 and level2 are not
        # overwritten.
        newtree = DataTree()

        def _f(p):
            return tuple([x for x in p if x is not None])

        for p1, p2 in itertools.product(paths[level1], paths[level2]):
            for prefix, infix, suffix in itertools.product(prefixes,
                                                           infixes,
                                                           suffixes):
                oldpath = _f(prefix + (p1,) + infix + (p2,) + suffix)
                newpath = _f(prefix + (p2,) + infix + (p1,) + suffix)
                # note: getLeaf, setLeaf are inefficient in this
                # context as they traverse the tree again
                data = self.getLeaf(oldpath)
                if data is None:
                    continue
                newtree.setLeaf(newpath, data)

        object.__setattr__(self, "_data", newtree._data)

    def removeLeaf(self, path):
        '''remove leaf/branch at *path*.'''
        if len(path) == 0:
            object.__setattr__(self, "_data", odict)
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
        if len(paths) == 0:
            return "NA"
        else:
            return "< datatree: %s >" % str(paths)

    def __getattr__(self, name):
        return getattr(self._data, name)

    def __setattr__(self, name, value):
        setattr(self._data, name, value)


def listAsDataFrame(data, index_title='names',
                    values_are_rows=False):
    '''convert a list of key, value pairs to a dataframe.

    The keys will be a one-level index called *index_title*
    and the values will contain one or more columns.

    If *values_are_rows* is set, keys will be column names
    and values will separate rows in the dataframe.

    '''
    if values_are_rows:
        df = pandas.DataFrame(
            odict(data))
    else:
        df = pandas.DataFrame(
            data=[x[1] for x in data],
            index=pandas.Index([x[0] for x in data],
                               name=index_title))
    return df


def concatDataFrames(dataframes, index_tuples):

    df = pandas.concat(dataframes, keys=index_tuples)

    # concat is akin to an SQL join operation and will
    # sort the columns lexicographically.
    # For matrices that could result in the columns not
    # being in the natural order any more unless the
    # column names have been set accordingly.
    # The following thus reorders the columns preserving
    # the order in the original dataframes.
    column_set = collections.OrderedDict()
    for d in dataframes:
        column_set.update(collections.OrderedDict(
            [(x, 0) for x in d.columns]))

    df = df.reindex_axis(list(column_set.keys()), axis=1)
    return df


def asDataFrame(data):
    '''convert data tree to pandas DataFrame.

    The data frame is multi-indexed according to the depth within the
    data tree.

    If the data-tree has only one level, the data will be
    single-indexed because pandas will not tolerate a single level
    MultiIndex.

    The code assumes that the data tree has a uniform
    depth and structure.

    The inner-most level in the *data* tree will be columns. However,
    if *data* is only a single-level dictionary, the keys in the
    dictionary will be row labels and the resultant dataframe will
    have only one column.

    Depending on the type of the leaf, the data frame is constructed
    as follows:

    Leaves are multiple arrays of the same size

        The data is assumed to be coordinate type data (x,y,z
        values). Leaves will be added to a dataframe as multiple
        columns.

    Leaves are a single array or arrays with dissimilar size

        A melted data frame will be constructed where
        the hierarchical index contains the path information
        and the data frame has a single column with the value.

    Leaf is a dataframe

        Dataframes will be concatenated. Existing indices
        of the dataframes will be preserved with the exception
        of the trivial index for the row numbers.

        Requires:
            All dataframes need to have the same columns.

    Leaf is a scalar
        Dataframes will be built from a nested dictionary

    Special cases for backwards compatibility:

    1. Lowest level dictionary contains the following arrays: rows,
        columns, matrix - numpy matrix, convert to dataframe and apply
        as above

    2. Lowest level dictionary contains the following keys:
        '01', '10', '11' - Venn 2-set data, convert columns
        '001', '010', ... - Venn 3-set data, convert columns

    Pandas attempts to find a column data type that will
    fit all values in a column. Thus, if a column is numeric,
    but contains values such as "inf", "Inf", as well, the
    column type might be set to object or char.

    '''
    if data is None or len(data) == 0:
        return None

    logger = Component.get_logger()

    levels = getDepths(data)
    if len(levels) == 0:
        return None

    mi, ma = min(levels), max(levels)
    if mi != ma:
        raise NotImplementedError(
            'data tree not of uniform depth, min=%i, max=%i' %
            (mi, ma))

    labels = getPaths(data)

    ######################################################
    ######################################################
    ######################################################
    # check special cases
    MATRIX = ('rows', 'columns', 'matrix')
    VENN2 = ('10', '01', '11')
    VENN3 = ('010', '001', '011')
    dataframe_prune_index = True
    branches = list(getNodes(data, len(labels) - 2))
    for path, branch in branches:
        # numpy matrix - dictionary with keys matrix, rows, columns
        if len(set(branch.keys()).intersection(MATRIX)) == len(MATRIX):
            df = pandas.DataFrame(branch['matrix'],
                                  columns=branch['columns'],
                                  index=branch['rows'])
            setLeaf(data, path, df)
            dataframe_prune_index = False

        elif len(set(branch.keys()).intersection(VENN2)) == len(VENN2) or \
                len(set(branch.keys()).intersection(VENN3)) == len(VENN3):
            # sort so that 'labels' is not the first item
            # specify data such that 'labels' will a single tuple entry
            values = sorted(branch.items())
            df = listAsDataFrame(values)
            dataframe_prune_index = False
            setLeaf(data, path, df)

    ######################################################
    ######################################################
    ######################################################
    labels = getPaths(data)
    # build multi-index
    leaves = list(getNodes(data, len(labels) - 1))

    # if set to a number, any superfluous levels in the
    # hierarchical index of the final dataframe will
    # be removed.
    expected_levels = None

    leaf = leaves[0][1]

    if Utils.isArray(leaf):

        # build dataframe from arrays
        dataframes = []
        index_tuples = []

        # not a nested dictionary
        if len(labels) == 1:
            branches = [(('all',), data)]
        else:
            branches = list(getNodes(data, max(0, len(labels) - 2)))

        # check if it is coordinate data
        # All arrays need to have the same length
        is_coordinate = True
        for path, subtree in branches:
            lengths = [len(x) for x in list(subtree.values())]
            if len(lengths) == 0:
                continue

            # all arrays have the same length - coordinate data
            if len(lengths) == 1 or min(lengths) != max(lengths):
                is_coordinate = False
                break

        if is_coordinate:
            logger.debug('dataframe conversion: from array - coordinates')
            for path, leaves in branches:
                # skip empty leaves
                if len(leaves) == 0:
                    continue
                dataframes.append(pandas.DataFrame(leaves))
                index_tuples.append(path)
        else:
            logger.debug('dataframe conversion: from array - series')
            # arrays of unequal length are measurements
            # build a melted data frame with a single column
            # given by the name of the path.
            for key, leave in leaves:
                # skip empty leaves
                if len(leave) == 0:
                    continue
                index_tuples.append(key)
                dataframes.append(pandas.DataFrame(leave,
                                                   columns=('value',)))

        expected_levels = len(index_tuples[0])
        df = concatDataFrames(dataframes, index_tuples)

    elif Utils.isDataFrame(leaf):
        logger.debug('dataframe conversion: from dataframe')

        # build dataframe from list of dataframes
        # by concatenation.
        # Existing indices of the dataframes will
        # be added as columns.
        dataframes = []
        index_tuples = []
        path_lengths = []
        levels = []
        for path, dataframe in leaves:
            if len(dataframe) == 0:
                continue
            path_lengths.append(len(path))
            if len(path) == 1:
                # if only one level, do not use tuple
                index_tuples.append(path[0])
            else:
                index_tuples.append(path)
            dataframes.append(dataframe)

            levels.append(Utils.getDataFrameLevels(
                dataframe,
                test_for_trivial=True))

        if len(path_lengths) == 0:
            return None

        assert min(path_lengths) == max(path_lengths)
        assert min(levels) == max(levels)

        # if only a single dataframe without given
        # tracks, return dataframe
        if index_tuples == ["all"]:
            df = dataframes[0]
            # if index is a simple numeric list, change to "all"
            if isinstance(df.index, pandas.Int64Index) and \
               df.index.name is None:
                df.index = ["all"] * len(df)
            return df

        expected_levels = min(path_lengths) + min(levels)
        df = concatDataFrames(dataframes, index_tuples)

    else:
        logger.debug('dataframe conversion: from values')
        if len(labels) == 1:
            # { 'x': 1, 'y': 2 } -> DF with one row and two columns (x, y)
            df = pandas.DataFrame(list(data.values()), index=list(data.keys()))
        elif len(labels) == 2:
            # { 'a': {'x':1, 'y':2}, 'b': {'y',2}
            # -> DF with two columns(x,y) and two rows(a,b)
            df = pandas.DataFrame.from_dict(data).transpose()
            # reorder so that order of columns corresponds to data
            df = df[labels[-1]]
        else:
            # We are dealing with a simple nested dictionary
            branches = list(getNodes(data, max(0, len(labels) - 3)))
            dataframes = []
            index_tuples = []
            for path, nested_dict in branches:
                # transpose to invert columns and rows
                # in cgatreport convention, the deeper
                # level in a dictionary in cgatreport are columns, while
                # in pandas they are rows.
                df = pandas.DataFrame(nested_dict).transpose()
                dataframes.append(df)
                index_tuples.extend([path])
            df = concatDataFrames(dataframes, index_tuples)

    # remove index with row numbers
    if expected_levels is not None and dataframe_prune_index:
        Utils.pruneDataFrameIndex(df, expected_levels)

    # rename levels in hierarchical index
    is_hierarchical = isinstance(df.index,
                                 pandas.core.index.MultiIndex)

    if is_hierarchical:
        n = list(df.index.names)
        l = ["track", "slice"] + ["level%i" % x for x in range(len(n))]

        for x, y in enumerate(n):
            if y is None:
                n[x] = l[x]
        df.index.names = n
    else:
        df.index.name = 'track'

    return df


def getPaths(work):
    '''extract labels from data.

    returns a list of list with all labels within
    the nested dictionary of data.
    '''
    labels = []

    this_level = [work, ]

    while 1:
        l, next_level = [], []
        for x in [x for x in this_level if hasattr(x, "keys")]:
            # ignore data frame for path calculation
            if isinstance(x, pandas.DataFrame):
                break
            if isinstance(x, pandas.Series):
                break
            l.extend(list(x.keys()))
            next_level.extend(list(x.values()))
        if not l:
            break
        labels.append(list(unique(l)))
        this_level = next_level

    return labels


def getNodes(work, level=0):
    '''iterate over all nodes at a certain depth.
    in nested dictionary work.

    yields path, value items
    '''

    stack = collections.deque([((), 0, x) for x in list(work.items())])

    # BFS
    while stack:
        p, l, kv = stack.popleft()
        k, v = kv
        n = p + (k,)
        if l == level:
            yield (n, v)
        if isinstance(v, dict):
            stack.extend([(n, l + 1, x) for x in list(v.items())])


def getDepths(work):
    '''return a list of depth of leaves.'''
    stack = [(0, x) for x in list(work.values())]

    levels = []
    while stack:
        level, v = stack.pop()
        if isinstance(v, dict):
            stack.extend([(level + 1, x) for x in list(v.values())])
        else:
            levels.append(level)
    return levels


def getLeaf(work, path):
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


def setLeaf(work, path, data):
    '''set leaf/branch at *path* to *data*.'''
    for x in path[:-1]:
        try:
            work = work[x]
        except KeyError:
            work[x] = odict()
            work = work[x]
    work[path[-1]] = data


def getPrefixes(work, level):
    '''get all possible paths up to *level*.'''
    paths = getPaths(work)
    return list(itertools.product(*paths[:level]))


def removeLevel(work, level):
    '''remove *level* in *work*.'''
    prefixes = getPrefixes(work, level)
    for path in prefixes:
        leaf = getLeaf(work, path)
        # skip truncated branches
        if leaf == None:
            continue

        # delete all in leaf
        keys = list(leaf.keys())
        for key in keys:
            # there might be a subkey the same as key
            d = leaf[key]
            del leaf[key]
            try:
                for subkey, item in list(d.items()):
                    leaf[subkey] = item
            except AttributeError:
                # for items that are not dict
                setLeaf(work, path, d)


def swop(work, level1, level2):
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
    if level1 == level2:
        return
    if level1 > level2:
        level1, level2 = level2, level1

    prefixes = paths[:level1]
    infixes = paths[level1 + 1:level2]
    suffixes = paths[level2 + 1:]

    if prefixes:
        prefixes = list(itertools.product(*prefixes))
    else:
        prefixes = [(None,)]

    if infixes:
        infixes = list(itertools.product(*infixes))
    else:
        infixes = [(None,)]

    if suffixes:
        suffixes = list(itertools.product(*suffixes))
    else:
        suffixes = [(None,)]

    # write to new tree in order to ensure that labels
    # that exist in both level1 and level2 are not
    # overwritten.
    newtree = odict()

    def _f(p):
        return tuple([x for x in p if x is not None])

    for p1, p2 in itertools.product(paths[level1], paths[level2]):

        for prefix, infix in itertools.product(prefixes, infixes):

            w = getLeaf(work, _f(prefix + (p1,) + infix + (p2,)))
            subpaths = getPaths(w)
            if subpaths:
                suffixes = list(itertools.product(subpaths[0]))
            else:
                suffixes = [(None,)]

            for suffix in suffixes:
                oldpath = _f(prefix + (p1,) + infix + (p2,) + suffix)
                newpath = _f(prefix + (p2,) + infix + (p1,) + suffix)

                # note: getLeaf, setLeaf are inefficient in this
                # context as they traverse the tree again
                data = getLeaf(work, oldpath)
                if data is None:
                    continue
                setLeaf(newtree, newpath, data)

    return newtree


def removeLeaf(work, path):
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


def removeEmptyLeaves(work):
    '''traverse data tree in DFS order and remove empty
    leaves.
    '''

    to_delete = []
    try:
        for label, w in list(work.items()):
            keep = removeEmptyLeaves(w)
            if not keep:
                to_delete.append(label)

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
    if isinstance(work, pandas.DataFrame) or isinstance(work, pandas.Series):
        return len(work) > 0

    try:
        return work is not None or work != ""
    except ValueError:
        # for numpy arrays
        return len(work) > 0


def prettyprint(work):
    paths = work.getPaths()
    if len(paths) == 0:
        return "NA"
    else:
        return "< datatree: %s >" % str(paths)


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


def count_levels(labels):
    '''count number of levels for each level in labels'''
    counts = []
    for x in labels:
        if type(x[0]) in Utils.ContainerTypes:
            counts.append(len(x[0]))
        else:
            counts.append(1)
    return counts


def tree2table(data, transpose=False, head=None):
    """build table from data.

    The table will be multi-level (main-rows and sub-rows), if:

       1. there is more than one column
       2. each cell within a row is a list or tuple

    If any of the paths contain tuples/lists, these are
    expanded to extra columns as well.

    If head is given, only first head rows are output.

    returns matrix, row_headers, col_headers
    """
    logger = Component.get_logger()

    labels = getPaths(data)

    if len(labels) < 2:
        raise ValueError("expected at least two levels for building table, got %i: %s" %
                         (len(labels), str(labels)))

    effective_labels = count_levels(labels)
    # subtract last level (will be expanded) and 1 for row header
    effective_cols = sum(effective_labels[:-1]) - 1

    col_headers = [""] * effective_cols + labels[-1]
    ncols = len(col_headers)

    paths = list(itertools.product(*labels[1:-1]))
    header_offset = effective_cols
    matrix = []

    logger.debug(
        "Datatree.buildTable: creating table with %i columns" %
        (len(col_headers)))

    # the following can be made more efficient
    # by better use of indices
    row_offset = 0
    row_headers = []

    # iterate over main rows
    for x, row in enumerate(labels[0]):

        first = True
        for xx, path in enumerate(paths):

            # get data - skip if there is None
            work = getLeaf(data, (row,) + path)
            if isinstance(work, pandas.DataFrame):
                if work.empty:
                    continue
            else:
                if not work:
                    continue

            row_data = [""] * ncols

            # add row header only for first row (if there are sub-rows)
            if first:
                if type(row) in Utils.ContainerTypes:
                    row_headers.append(row[0])
                    for z, p in enumerate(row[1:]):
                        row_data[z] = p
                else:
                    row_headers.append(row)
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
                if column not in work:
                    continue
                if type(work[column]) not in Utils.ContainerTypes:
                    is_container = False
                    break
                if max_rows == None:
                    max_rows = len(work[column])
                elif max_rows != len(work[column]):
                    raise ValueError("multi-level rows - unequal lengths: %i != %i" %
                                     (max_rows, len(work[column])))

            # add sub-rows
            if is_container:
                # multi-level rows
                for z in range(max_rows):
                    for y, column in enumerate(labels[-1]):
                        try:
                            row_data[
                                y + header_offset] = Utils.quote_rst(work[column][z])
                        except KeyError:
                            pass

                    if z < max_rows - 1:
                        matrix.append(row_data)
                        row_headers.append("")
                        row_data = [""] * ncols
            else:
                # single level row
                for y, column in enumerate(labels[-1]):
                    try:
                        row_data[
                            y + header_offset] = Utils.quote_rst(work[column])
                    except KeyError:
                        pass

            matrix.append(row_data)

            if head and len(matrix) >= head:
                break

    if transpose:
        row_headers, col_headers = col_headers, row_headers
        matrix = list(zip(*matrix))

    # convert headers to string (might be None)
    row_headers = [str(x) for x in row_headers]
    col_headers = [str(x) for x in col_headers]

    return matrix, row_headers, col_headers


def fromCache(cache,
              tracks=None,
              slices=None,
              groupby="slice"):
    '''return a data tree from cache'''

    data = DataTree()
    keys = [x.split("/") for x in list(cache.keys())]

    if tracks == None:
        tracks = set([x[0] for x in keys])
    else:
        tracks = tracks.split(",")

    if slices == None:
        slices = set([x[1] for x in keys if len(x) > 1])
    else:
        slices = slices.split(",")

    def tokey(track, slice):
        return "/".join((track, slice))

    if not slices:
        for track in tracks:
            data[track] = cache[track]
    elif groupby == "slice" or groupby == "all":
        for slice in slices:
            data[slice] = odict()
            for track in tracks:
                data[slice][track] = cache[tokey(track, slice)]
    elif groupby == "track":
        for track in tracks:
            data[track] = odict()
            for slice in slices:
                data[track][slice] = cache[tokey(track, slice)]
    return data


def prune(data,
          ignore=[],
          method='bottom-up'):
    '''prune data tree.

    Remove all empty leaves.

    Remove all levels from the data tree that are
    superfluous, i.e. levels that contain only a single label
    and all labels in the hierarchy below are the same.

    Do not prune top-level, if it is the only level.

    Ignore certain labels given by ignore.

    Returns the levels and labels which have been pruned.
    '''

    # remove all empty leaves
    removeEmptyLeaves(data)

    # prune superfluous levels
    data_paths = getPaths(data)
    nlevels = len(data_paths)

    levels_to_prune = []

    # used to be: 1 (no pruning on first level)
    for level in range(0, nlevels):

        # check for single label in level
        if len(data_paths[level]) == 1:
            label = data_paths[level][0]
            if label in ignore:
                continue
            prefixes = getPrefixes(data, level)
            keep = False
            for prefix in prefixes:
                leaves = getLeaf(data, prefix)
                if leaves is None:
                    continue
                if len(leaves) > 1 or label not in leaves:
                    keep = True
                    break
            if not keep:
                levels_to_prune.append((level, label))

    levels_to_prune.reverse()

    pruned = []

    for level, label in levels_to_prune:
        # do not prune top-level, if it is the only level
        if level == 0 and nlevels == 1:
            continue
        if method == 'bottom-up':
            # stop pruning if not on deepest level
            if level != nlevels - 1:
                break

        pruned.append((level, label))
        removeLevel(data, level)
        nlevels -= 1

    return pruned
