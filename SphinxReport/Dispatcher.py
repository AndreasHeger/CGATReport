import os
import sys
import re
import shelve
import traceback
import pickle
import types
import itertools

from SphinxReport.ResultBlock import ResultBlock, ResultBlocks
from SphinxReport import DataTree
from SphinxReport.Component import *
from SphinxReport import Utils
from SphinxReport import Cache
from SphinxReport import Tracker

# move User renderer to SphinxReport main distribution
from SphinxReportPlugins import Renderer
import numpy

VERBOSE = True
# maximimum number of levels in data tree
MAX_PATH_NESTING = 5

import pandas

from collections import OrderedDict as odict

# heap memory debugging, search for 'heap' in this code
# from guppy import hpy; HP=hpy()


class Dispatcher(Component):

    """Dispatch the directives in the ``:report:`` directive
    to a:class:`Tracker`, class:`Transformer` and:class:`Renderer`.

    The dispatcher has three passes:

    1. Collect data from a:class:`Tracker`

    2. Transform data from a:class:`Transformer`

    3. Render data with a:class:`Renderer`

    This class adds the following options to the:term:`render` directive.

:term:`groupby`: group data by:term:`track` or:term:`slice`.

    """

    def __init__(self, tracker, renderer,
                 transformers=None):
        '''render images using an instance of a:class:`Tracker.Tracker`
        to obtain data, an optional:class:`Transformer` to transform
        the data and a:class:`Renderer.Renderer` to render the output.
        '''
        Component.__init__(self)

        self.debug("starting dispatcher '%s': tracker='%s', renderer='%s', transformer:='%s'" %
                   (str(self), str(tracker), str(renderer), str(transformers)))

        self.tracker = tracker
        # add reference to self for access to tracks
        self.tracker.dispatcher = self
        self.renderer = renderer
        self.transformers = transformers

        try:
            if tracker.cache:
                self.cache = Cache.Cache(Cache.tracker2key(tracker))
            else:
                self.cache = {}
        except AttributeError:
            self.cache = Cache.Cache(Cache.tracker2key(tracker))

        self.data = DataTree.DataTree()

        # Level at which to group the results of Renderers
        # None is no grouping
        # 0: group on first level ('groupby=track')
        # 1: group on second level ('groupby=slice')
        # n: group on n-th level
        self.group_level = 1

    def __del__(self):
        pass

    def getCaption(self):
        """return a caption string."""
        return self.__doc__

    def parseArguments(self, *args, **kwargs):
        '''argument parsing.'''

        self.groupby = kwargs.get("groupby", "slice")
        self.nocache = "nocache" in kwargs

        try:
            self.mInputTracks = [x.strip()
                                 for x in kwargs["tracks"].split(",")]
        except KeyError:
            self.mInputTracks = None

        try:
            self.mInputSlices = [x.strip()
                                 for x in kwargs["slices"].split(",")]
        except KeyError:
            self.mInputSlices = None

        try:
            self.restrict_paths = [x.strip()
                                   for x in kwargs["restrict"].split(",")]
        except KeyError:
            self.restrict_paths = None

        try:
            self.exclude_paths = [x.strip()
                                  for x in kwargs["exclude"].split(",")]
        except KeyError:
            self.exclude_paths = None

        try:
            self.mColumns = [x.strip() for x in kwargs["columns"].split(",")]
        except KeyError:
            self.mColumns = None

        self.tracker_options = kwargs.get("tracker", None)

    def getData(self, path):
        """get data for track and slice. Save data in persistent cache for further use.

        For functions, path should be an empty tuple.
        """

        if path:
            key = DataTree.path2str(path)
        else:
            key = "all"

        result, fromcache = None, False
        # trackers with options are not cached
        if not self.nocache and not self.tracker_options:
            try:
                result = self.cache[key]
                fromcache = True
            except KeyError:
                pass
            except RuntimeError as msg:
                raise RuntimeError(
                    "error when accessing key %s from cache: %s - potential problem with unpickable object?" % (key, msg))

        kwargs = {}
        if self.tracker_options:
            kwargs['options'] = self.tracker_options

        if result is None:
            try:
                result = self.tracker(*path, **kwargs)
            except Exception as msg:
                self.warn("exception for tracker '%s', path '%s': msg=%s" % (str(self.tracker),
                                                                             DataTree.path2str(
                                                                                 path),
                                                                             msg))
                if VERBOSE:
                    self.warn(traceback.format_exc())
                raise

        # store in cache
        if not self.nocache and not fromcache:
            # exception - do not store data frames
            # test with None fails for some reason
            self.cache[key] = result

        return result

    def getDataPaths(self, obj):
        '''determine data paths from a tracker.

        If obj is a function, returns True and an empty list.

        returns False and a list of lists.
        '''
        data_paths = []

        if hasattr(obj, 'paths'):
            data_paths = getattr(obj, 'paths')
        elif hasattr(obj, 'getPaths'):
            data_paths = obj.getPaths()

        if not data_paths:
            if hasattr(obj, 'tracks'):
                tracks = getattr(obj, 'tracks')
            elif hasattr(obj, 'getTracks'):
                tracks = obj.getTracks()
            else:
                # is a function
                return True, []

            # if tracks specified and no tracks found - return
            # no data paths.
            if tracks is None or len(tracks) == 0:
                return False, []

            data_paths = [tracks]

            # get slices
            if hasattr(obj, 'slices'):
                data_paths.append(getattr(obj, 'slices'))
            elif hasattr(obj, 'getSlices'):
                data_paths.append(obj.getSlices())

        # sanity check on data_paths.
        # 1. Replace strings with one-element tuples
        # 2. Remove empty levels in the paths
        # 3. Replace sets and other non-containers with lists
        to_remove = []
        for x, y in enumerate(data_paths):
            if y is None or len(y) == 0:
                to_remove.append(x)
                continue
            if isinstance(y, str):
                data_paths[x] = [y, ]
            elif type(y) not in Utils.ContainerTypes:
                data_paths[x] = list(y)

        for x in to_remove[::-1]:
            del data_paths[x]

        return False, data_paths

    def filterDataPaths(self, datapaths):
        '''filter *datapaths*.

        returns the filtered data paths.
        '''

        if not datapaths:
            return

        def _filter(all_entries, input_list):
            # need to preserve type of all_entries
            result = []
            search_entries = list(map(str, all_entries))
            m = dict(list(zip(search_entries, all_entries)))
            for s in input_list:
                if s in search_entries:
                    # collect exact matches
                    result.append(all_entries[search_entries.index(s)])
                elif s.startswith("r(") and s.endswith(")"):
                    # collect pattern matches:
                    # remove r()
                    s = s[2:-1]
                    # remove flanking quotation marks
                    if s[0] in ('"', "'") and s[-1] in ('"', "'"):
                        s = s[1:-1]
                    rx = re.compile(s)
                    result.extend(
                        [all_entries[y] for y, x in enumerate(search_entries) if rx.search(str(x))])
            return result

        if self.mInputTracks:
            datapaths[0] = _filter(datapaths[0], self.mInputTracks)

        if self.mInputSlices:
            if len(datapaths) >= 2:
                datapaths[1] = _filter(datapaths[1], self.mInputSlices)

        return datapaths

    def collect(self):
        '''collect all data.

        Data is stored in a multi-level dictionary (DataTree)
        '''

        self.data = odict()

        self.debug("%s: collecting data paths." % (self.tracker))
        is_function, datapaths = self.getDataPaths(self.tracker)
        self.debug("%s: collected data paths." % (self.tracker))

        # if function, no datapaths
        if is_function:
            d = self.getData(())

            # save in data tree as leaf
            DataTree.setLeaf(self.data, ("all",), d)

            self.debug("%s: collecting data finished for function." %
                       (self.tracker))
            return

        # if no tracks, error
        if len(datapaths) == 0 or len(datapaths[0]) == 0:
            self.warn("%s: no tracks found - no output" % self.tracker)
            return

        self.debug("%s: filtering data paths." % (self.tracker))
        # filter data paths
        datapaths = self.filterDataPaths(datapaths)
        self.debug("%s: filtered data paths." % (self.tracker))

        # if no tracks, error
        if len(datapaths) == 0 or len(datapaths[0]) == 0:
            self.warn(
                "%s: no tracks remain after filtering - no output" % self.tracker)
            return

        self.debug("%s: building all_paths" % (self.tracker))
        if len(datapaths) > MAX_PATH_NESTING:
            self.warn("%s: number of nesting in data paths too large: %i" % (
                self.tracker, len(all_paths)))
            raise ValueError("%s: number of nesting in data paths too large: %i" % (
                self.tracker, len(all_paths)))

        all_paths = list(itertools.product(*datapaths))
        self.debug("%s: collecting data started for %i data paths" % (self.tracker,
                                                                      len(all_paths)))

        self.data = odict()
        for path in all_paths:

            d = self.getData(path)

            # ignore empty data sets
            if d is None:
                continue

            # save in data tree as leaf
            DataTree.setLeaf(self.data, path, d)

        self.debug("%s: collecting data finished for %i data paths" % (self.tracker,
                                                                       len(all_paths)))
        return self.data

    def restrict(self):
        '''restrict data paths.

        Only those data paths matching the restrict term are accepted.
        '''
        if not self.restrict_paths:
            return

        data_paths = DataTree.getPaths(self.data)

        # currently enumerates - bfs more efficient

        all_paths = list(itertools.product(*data_paths))

        for path in all_paths:
            for s in self.restrict_paths:
                if s in path:
                    break
                elif s.startswith("r(") and s.endswith(")"):
                    # collect pattern matches:
                    # remove r()
                    s = s[2:-1]
                    # remove flanking quotation marks
                    if s[0] in ('"', "'") and s[-1] in ('"', "'"):
                        s = s[1:-1]
                    rx = re.compile(s)
                    if any((rx.search(p) for p in path)):
                        break
            else:
                self.debug(
                    "%s: ignoring path %s because of:restrict=%s" % (self.tracker, path, s))
                try:
                    DataTree.removeLeaf(self.data, path)
                except KeyError:
                    pass

    def exclude(self):
        '''exclude data paths.

        Only those data paths not matching the exclude term are accepted.
        '''
        if not self.exclude_paths:
            return

        data_paths = DataTree.getPaths(self.data)

        # currently enumerates - bfs more efficient
        all_paths = list(itertools.product(*data_paths))

        for path in all_paths:
            for s in self.exclude_paths:
                if s in path:
                    self.debug(
                        "%s: ignoring path %s because of:exclude:=%s" % (self.tracker, path, s))
                    try:
                        DataTree.removeLeaf(self.data, path)
                    except KeyError:
                        pass
                elif s.startswith("r(") and s.endswith(")"):
                    # collect pattern matches:
                    # remove r()
                    s = s[2:-1]
                    # remove flanking quotation marks
                    if s[0] in ('"', "'") and s[-1] in ('"', "'"):
                        s = s[1:-1]
                    rx = re.compile(s)
                    if any((rx.search(p) for p in path)):
                        self.debug(
                            "%s: ignoring path %s because of:exclude:=%s" % (self.tracker, path, s))
                        try:
                            DataTree.removeLeaf(self.data, path)
                        except KeyError:
                            pass

    def transform(self):
        '''call data transformers and group tree
        '''
        for transformer in self.transformers:
            self.debug("profile: started: transformer: %s" % (transformer))
            self.debug("%s: applying %s" % (self.renderer, transformer))

            try:
                self.data = transformer(self.data)
            finally:
                self.debug("profile: finished: transformer: %s" %
                           (transformer))

        return self.data

    def group(self):
        '''rearrange data tree for grouping
        and set group level.

        Through grouping the data tree is rearranged such
        that the level at which data will be grouped will
        be the top (0th) level in the nested dictionary.
        '''

        data_paths = DataTree.getPaths(self.data)
        nlevels = len(data_paths)

        # get number of levels required by renderer
        try:
            renderer_nlevels = self.renderer.nlevels
        except AttributeError:
            renderer_nlevels = 0

        if self.groupby == "none":
            self.group_level = nlevels - 1

        elif self.groupby == "track":
            # track is first level
            self.group_level = 1
            # add pseudo levels, if there are not enough levels
            # to group by track
            if nlevels == renderer_nlevels:
                d = odict()
                for x in data_paths[0]:
                    d[x] = odict(((x, self.data[x]),))
                self.data = d

        elif self.groupby == "slice":
            # rearrange tracks and slices in data tree
            if nlevels <= 2:
                self.warn(
                    "grouping by slice, but only %i levels in data tree - all are grouped" % nlevels)
                self.group_level = 0
            else:
                self.data = DataTree.swop(self.data, 0, 1)
                self.group_level = 1

        elif self.groupby == "all":
            # group everything together
            self.group_level = 0

        else:
            # neither group by slice or track ("ungrouped")
            self.group_level = 0

        return self.data

    def prune(self):
        '''prune data tree.

        Remove all empty leaves.

        Remove all levels from the data tree that are
        superfluous, i.e. levels that contain only a single label
        and all labels in the hierarchy below are the same.

        This method ignores some labels with reserved key-words
        such as ``text``, ``rst``, ``xls``

        Ignore both the first and last level for this analyis.
        '''

        # set method to outwards - only prune leaves if they
        # are superfluous.
        pruned = DataTree.prune(self.data,
                                ignore=Utils.TrackerKeywords,
                                method='bottom-up')

        for level, label in pruned:
            self.debug("pruned level %i from data tree: label='%s'" %
                       (level, label))

        # save for conversion
        self.pruned = pruned

    def render(self):
        '''supply the:class:`Renderer.Renderer` with the data to render.

        The data supplied will depend on the ``groupby`` option.

        returns a ResultBlocks data structure.
        '''
        self.debug("%s: rendering data started for %i items" % (self,
                                                                len(self.data)))

        # get number of levels required by renderer
        try:
            renderer_nlevels = self.renderer.nlevels
        except AttributeError:
            # set to -1 to avoid any grouping
            # important for user renderers that are functions
            # and have no level attribute.
            renderer_nlevels = -1

        # initiate output structure
        results = ResultBlocks(title="")

        # convert to data series
        # The data is melted, i.e,
        # BMW    price    10000
        # BMW    speed    100
        # Golf   price    5000
        # Golf   speed    50
        dataframe = DataTree.asDataFrame(self.data)
        # dataframe.write_csv("test.csv")

        if dataframe is None:
            self.warn("%s: no data after conversion" % self)
            raise ValueError("no data for renderer")

        # special patch: set column names to pruned levels
        # if there are no column names
        if len(dataframe.columns) == len(self.pruned):
            if list(dataframe.columns) == list(range(len(dataframe.columns))):
                dataframe.columns = [x[1] for x in self.pruned]

        index = dataframe.index

        def getIndexLevels(index):
            try:
                # hierarchical index
                nlevels = len(index.levels)
            except AttributeError:
                nlevels = 1
                index = [(x,) for x in index]
            #raise ValueError('data frame without MultiIndex')
            return nlevels

        nlevels = getIndexLevels(index)

        self.debug("%s: rendering data started. levels=%i, required levels>=%i, group_level=%s" %
                   (self, nlevels,
                    renderer_nlevels,
                    str(self.group_level)))

        if renderer_nlevels < 0 and self.group_level <= 0:
            # no grouping for renderers that will accept
            # a dataframe with any level of indices and no explicit
            # grouping has been asked for.
            results.append(self.renderer(dataframe, path=()))
        else:
            # user specified group level by default
            group_level = self.group_level

            # set group level to maximum allowed by renderer
            if renderer_nlevels >= 0:
                group_level = max(nlevels - renderer_nlevels, group_level)

            # add additional level if necessary
            if nlevels < group_level:
                prefix = tuple(
                    ["level%i" % x for x in range(group_level - nlevels)])
                dataframe.index = pandas.MultiIndex.from_tuples(
                    [prefix + x for x in dataframe.index])

            # used to be: group_level + 1
            # hierarchical index
            # numpy.unique converts everything to a string
            # which is not consistent with selecting later
            paths = map(tuple, DataTree.unique(
                [x[:group_level] for x in dataframe.index.unique()]))

            pathlength = len(paths[0]) - 1

            is_hierarchical = isinstance(
                dataframe.index, pandas.core.index.MultiIndex)

            if is_hierarchical:
                # Note: can only sort hierarchical indices
                dataframe = dataframe.sortlevel()

                if dataframe.index.lexsort_depth < pathlength:
                    raise ValueError('could not sort data frame: sort depth=%i < pathlength=%i, dataframe=%s'
                                     % (dataframe.index.lexsort_depth,
                                        pathlength,
                                        dataframe))

            for path in paths:

                if path:
                    if len(path) == nlevels:
                        # extract with loc in order to obtain dataframe
                        work = dataframe.loc[[path]]
                    else:
                        # select data frame as cross-section
                        work = dataframe.xs(path, axis=0)
                else:
                    # empty tuple - use full data set
                    work = dataframe

                # remove columns and rows in work that are all Na
                work = work.dropna(axis=1, how='all').dropna(axis=0, how='all')

                if is_hierarchical and renderer_nlevels >= 0:
                    work_levels = getIndexLevels(work.index)
                    # reduce levels of indices required to that required
                    # for Renderer. This occurs if groupby=none.
                    if work_levels > renderer_nlevels:
                        sep = work_levels - (renderer_nlevels - 1)
                        tuples = [(DataTree.path2str(x[:sep]),) + x[sep:]
                                  for x in work.index]
                        work.index = pandas.MultiIndex.from_tuples(tuples)

                try:
                    results.append(self.renderer(work,
                                                 path=path))
                except:
                    self.error("%s: exception in rendering" % self)
                    results.append(
                        ResultBlocks(Utils.buildException("rendering")))

        if len(results) == 0:
            self.warn("renderer returned no data.")
            raise ValueError("renderer returned no data.")

        self.debug("%s: rendering data finished with %i blocks" %
                   (self.tracker, len(results)))

        return results

    def __call__(self, *args, **kwargs):

        #self.debug("%s: heap at start\n%s" % (self, str(HP.heap())))

        try:
            self.parseArguments(*args, **kwargs)
        except:
            self.error("%s: exception in parsing" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("parsing")))

        # collect no data if tracker is the empty tracker
        # and go straight to rendering
        try:
            if self.tracker.getTracks() == ["empty"]:
                # is instance does not work because of module mapping
                # type(Tracker.Empty) == SphinxReport.Tracker.Empty
                # type(self.tracker) == Tracker.Empty
                # if isinstance(self.tracker, Tracker.Empty):
                result = self.renderer()
                return ResultBlocks(result)
        except AttributeError:
            # for function trackers
            pass

        self.debug("profile: started: tracker: %s" % (self.tracker))

        # collecting data
        try:
            self.collect()
        except:
            self.error("%s: exception in collection" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("collection")))
        finally:
            self.debug("profile: finished: tracker: %s" % (self.tracker))

        if len(self.data) == 0:
            self.info("%s: no data - processing complete" % self.tracker)
            return None

        data_paths = DataTree.getPaths(self.data)
        self.debug("%s: after collection: %i data_paths: %s" %
                   (self, len(data_paths), str(data_paths)))

        # self.debug("%s: heap after collection\n%s" % (self, str(HP.heap())))

        # transform data
        try:
            self.transform()
        except:
            self.error("%s: exception in transformation" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("transformation")))

        data_paths = DataTree.getPaths(self.data)
        self.debug("%s: after transformation: %i data_paths: %s" %
                   (self, len(data_paths), str(data_paths)))

        # special Renderers - do not proceed
        # Special renderers
        if isinstance(self.renderer, Renderer.User):
            results = ResultBlocks(title="main")
            results.append(self.renderer(self.data, ('')))
            return results
        elif isinstance(self.renderer, Renderer.Debug):
            results = ResultBlocks(title="main")
            results.append(self.renderer(self.data, ('')))
            return results

        # self.debug("%s: heap after transformation\n%s" % (self, str(HP.heap())))
        # restrict
        try:
            self.restrict()
        except:
            self.error("%s: exception in restrict" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("restrict")))

        data_paths = DataTree.getPaths(self.data)
        self.debug("%s: after restrict: %i data_paths: %s" %
                   (self, len(data_paths), str(data_paths)))

        # exclude
        try:
            self.exclude()
        except:
            self.error("%s: exception in exclude" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("exclude")))

        data_paths = DataTree.getPaths(self.data)
        self.debug("%s: after exclude: %i data_paths: %s" %
                   (self, len(data_paths), str(data_paths)))

        # remove superfluous levels
        try:
            self.prune()
        except:
            self.error("%s: exception in pruning" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("pruning")))

        data_paths = DataTree.getPaths(self.data)
        self.debug("%s: after pruning: %i data_paths: %s" %
                   (self, len(data_paths), str(data_paths)))

        # remove group plots
        try:
            self.group()
        except:
            self.error("%s: exception in grouping" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("grouping")))

        data_paths = DataTree.getPaths(self.data)
        self.debug("%s: after grouping: %i data_paths: %s" %
                   (self, len(data_paths), str(data_paths)))

        self.debug("profile: started: renderer: %s" % (self.renderer))

        try:
            result = self.render()
        except:
            self.error("%s: exception in rendering" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("rendering")))
        finally:
            self.debug("profile: finished: renderer: %s" % (self.renderer))

        #self.debug("%s: heap at end\n%s" % (self, str(HP.heap())))

        return result

    def getTracks(self):
        '''return tracks used by the dispatcher.

        used for re-constructing call to cache.
        '''
        return self.tracks

    def getSlices(self):
        '''return slices used by the dispatcher.

        used for re-constructing call to cache.
        '''
        return self.slices
