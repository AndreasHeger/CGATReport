import re
import traceback
import itertools
import pandas

from CGATReport.ResultBlock import ResultBlocks
from CGATReport import DataTree
from CGATReport import Component
from CGATReport import Utils
from CGATReport import Cache

# move User renderer to CGATReport main distribution
from CGATReportPlugins import Renderer

VERBOSE = True
# maximimum number of levels in data tree
MAX_PATH_NESTING = 5

from collections import OrderedDict as odict

# heap memory debugging, search for 'heap' in this code
# from guppy import hpy; HP=hpy()


class Dispatcher(Component.Component):

    """Dispatch the directives in the ``:report:`` directive
    to a:class:`Tracker`, class:`Transformer` and:class:`Renderer`.

    The dispatcher has three passes:

    1. Collect data from a:class:`Tracker`

    2. Transform data from a:class:`Transformer`

    3. Render data with a:class:`Renderer`

    This class adds the following options to the:term:`render` directive.

    :term:`groupby`: group data by:term:`track` or:term:`slice`.

    """

    def __init__(self,
                 tracker,
                 renderer,
                 transformers=None):
        '''render images using an instance of a:class:`Tracker.Tracker` to
        obtain data, an optional:class:`Transformer` to transform the
        data and a:class:`Renderer.Renderer` to render the output.

        '''
        Component.Component.__init__(self)

        self.debug("starting dispatcher '%s': tracker='%s', renderer='%s', "
                   "transformer:='%s'" %
                   (str(self), str(tracker), str(renderer), str(transformers)))

        self.tracker = tracker
        # add reference to self for access to tracks
        self.tracker.dispatcher = self
        self.renderer = renderer
        self.transformers = transformers

        # set to true if index will be later set by tracker
        self.indexFromTracker = False

        try:
            self.debug("cache of tracker: %s: %s" % (self.tracker,
                                                     str(tracker.cache)))

            if tracker.cache:
                self.cache = Cache.Cache(Cache.tracker2key(tracker))
            else:
                self.cache = {}
                self.nocache = True
        except AttributeError:
            self.cache = Cache.Cache(Cache.tracker2key(tracker))

        self.tree = None
        self.data = None

        # Level at which to group the results of Renderers
        # None is no grouping
        # 0: group on first level ('groupby=track')
        # 1: group on second level ('groupby=slice')
        # n: group on n-th level
        self.group_level = 0

        # no caching for user renderers, figure needs
        # to be created for collection.
        if isinstance(renderer, Renderer.User):
            self.nocache = True

    def __del__(self):
        pass

    def getCaption(self):
        """return a caption string."""
        return self.__doc__

    def parseArguments(self, *args, **kwargs):
        '''argument parsing.'''

        def as_list(arg):
            if arg is None:
                return arg

            return [x.strip() for x in arg.split(",")]

        def as_set(arg):
            if arg is None:
                return arg
            else:
                return set([x.strip() for x in arg.split(",")])

        self.groupby = kwargs.get("groupby", "default")
        try:
            self.groupby = int(self.groupby)
        except ValueError:
            pass

        self.nocache = "nocache" in kwargs

        self.mInputTracks = as_list(kwargs.get("tracks", None))
        self.mInputSlices = as_list(kwargs.get("slices", None))
        self.restrict_paths = as_list(kwargs.get("restrict", None))
        self.exclude_paths = as_list(kwargs.get("exclude", None))
        self.mColumns = as_list(kwargs.get("columns", None))
        self.exclude_columns = as_set(kwargs.get("exclude-columns", None))
        self.include_columns = as_list(kwargs.get("include-columns", None))
        self.set_index = as_list(kwargs.get("set-index", None))

        self.tracker_options = kwargs.get("tracker", None)

    def getData(self, path):
        """get data for track and slice. Save data in persistent cache for
        further use.

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
                    "error when accessing key %s from cache: %s "
                    "- potential problem with unpickable object?" % (key, msg))

        kwargs = {}
        if self.tracker_options:
            kwargs['options'] = self.tracker_options

        if result is None:
            try:
                result = self.tracker(*path, **kwargs)
            except Exception as msg:
                self.warn("exception for tracker '%s', path '%s': msg=%s" %
                          (str(self.tracker),
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
        '''determine if obj is a function and return
        data paths from a tracker.

        If obj is a function, returns True and an empty list.
        If obj is an object, returns False and a list datapaths.
        '''
        data_paths = []

        if hasattr(obj, 'paths'):
            data_paths = getattr(obj, 'paths')
        elif hasattr(obj, 'getPaths'):
            data_paths = obj.getPaths()

        if not data_paths:
            if hasattr(obj, 'setIndex'):
                self.indexFromTracker = True
                return True, []
            elif hasattr(obj, 'tracks'):
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
                        [all_entries[y] for y, x in
                         enumerate(search_entries) if rx.search(str(x))])
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

        self.tree = odict()

        self.debug("%s: collecting data paths." % (self.tracker))
        is_function, datapaths = self.getDataPaths(self.tracker)
        self.debug("%s: collected data paths." % (self.tracker))

        # if function, no datapaths
        if is_function:
            d = self.getData(())

            # save in data tree as leaf
            DataTree.setLeaf(self.tree, ("all",), d)

            self.debug("%s: collecting data finished for function." %
                       (self.tracker))
            return

        # if no tracks, error
        if len(datapaths) == 0 or len(datapaths[0]) == 0:
            self.warn("%s: no tracks found - no output" % self.tracker)
            return

        # filter data paths
        self.debug("%s: filtering data paths: %s" %
                   (self.tracker, datapaths))
        datapaths = self.filterDataPaths(datapaths)
        self.debug("%s: filtered data paths: %s" %
                   (self.tracker, datapaths))

        # if no tracks, error
        if len(datapaths) == 0 or len(datapaths[0]) == 0:
            self.warn(
                "%s: no tracks remain after filtering "
                "- no output" % self.tracker)
            return

        self.debug("%s: building all_paths" % (self.tracker))
        if len(datapaths) > MAX_PATH_NESTING:
            self.warn("%s: number of nesting in data paths too large: %i" % (
                self.tracker, len(datapaths)))
            raise ValueError(
                "%s: number of nesting in data paths too large: %i" % (
                    self.tracker, len(datapaths)))

        all_paths = list(itertools.product(*datapaths))
        self.debug(
            "%s: collecting data started for %i data paths" % (
                self.tracker,
                len(all_paths)))

        self.tree = odict()
        for path in all_paths:

            d = self.getData(path)

            # ignore empty data sets
            if d is None:
                continue

            # save in data tree as leaf
            DataTree.setLeaf(self.tree, path, d)

        self.debug(
            "%s: collecting data finished for %i data paths" % (
                self.tracker,
                len(all_paths)))
        return self.tree

    def _match(self, label, paths):
        '''return True if any of paths match to label.'''

        for s in paths:
            if label == s:
                return True
            elif s.startswith("r(") and s.endswith(")"):
                    # collect pattern matches:
                    # remove r()
                    s = s[2:-1]
                    # remove flanking quotation marks
                    if s[0] in ('"', "'") and s[-1] in ('"', "'"):
                        s = s[1:-1]
                    rx = re.compile(s)
                    if not Utils.isString(label):
                        continue
                    if rx.search(label):
                        return True
        return False

    def filterPaths(self, path_patterns, mode="restrict"):
        '''restrict or exclude data paths.

        Only those data paths and columns matching the restrict term
        are accepted.

        Columns are not removed.
        '''
        if not path_patterns:
            return

        # rows first

        # select rows to keep (matching any of the patterns in any
        # of the levels of the hierarchical index)
        is_hierarchical = isinstance(self.data.index,
                                     pandas.core.index.MultiIndex)
        if is_hierarchical:
            keep = [any([self._match(x, path_patterns) for x in labels])
                    for labels in self.data.index]
        else:
            keep = [self._match(x, path_patterns) for x in self.data.index]

        if mode == "exclude":
            keep = [not x for x in keep]

        self.data = self.data[keep]

        # Selecting columns does not work together with row restrict
        # needs a separate option.
        # keep = [x for x in self.data.columns if _match(x)]
        # self.data = self.data[keep]

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
        '''rearrange dataframe for desired grouping.

        Through grouping the dataframe is rearranged such that the
        level at which data will be grouped will be the first level in
        hierarchical index.

        If grouping by "track" is set, additional level will be added
        to ensure that grouping will happen.

        If grouping by "slice" is set, the first two levels will be
        swopped.

        The group level indicates at which level in the nested
        dictionary the data will be grouped with 0 indicating that
        everything will grouped together.

        '''

        nlevels = Utils.getDataFrameLevels(self.data)
        try:
            default_level = self.renderer.group_level
        except AttributeError:
            # User rendere that is pure functions does not
            # have a group_level attribute
            default_level = 0

        groupby = self.groupby

        if str(default_level).startswith("force"):
            groupby = default_level[len("force-"):]
        elif groupby == "default":
            groupby = default_level

        if groupby == "none":
            self.group_level = nlevels - 1

        elif groupby == "track":
            self.group_level = 0

        elif groupby == "slice":
            # rearrange first two levels in data tree
            if nlevels > 1:
                self.data = self.data.reorder_levels(
                    [1, 0] + list(range(2, nlevels)))
            self.group_level = 0

        elif groupby == "all":
            # group everything together
            self.group_level = -1

        elif isinstance(groupby, int):
            # get group level from Renderer
            if groupby < 0:
                # negative levels - subtract from lowest
                # level
                g = nlevels + groupby - 1
            else:
                g = groupby
            self.group_level = g
        else:
            self.group_level = 0

        self.debug(
            "grouping: nlevel=%i, groupby=%s, default=%s, group=%i" %
            (nlevels, groupby, str(default_level), self.group_level))

        return self.data

    def prune(self):
        '''prune data frame.

        Remove levels from the data tree that are
        superfluous, i.e. levels that contain only a single label.

        This method ignores some labels with reserved key-words
        such as ``text``, ``rst``, ``xls``

        '''

        dataframe = self.data
        self.pruned = []

        if isinstance(dataframe.index,
                      pandas.core.index.MultiIndex):
            todrop = []
            for x, level in enumerate(dataframe.index.levels):

                if len(level) == 1 and level[0] not in Utils.TrackerKeywords:
                    todrop.append(x)

            names = dataframe.index.names
            pruned = [(x, names[x]) for x in todrop]

            dataframe.reset_index(
                todrop,
                drop=True,
                inplace=True)

            for level, label in pruned:
                self.debug(
                    "pruned level %i from data tree: label='%s'" %
                    (level, label))

            # save for conversion
            self.pruned = pruned

    def reframe(self):
        """set index and drop columns of dataframe"""
        dataframe = self.data

        if not (self.set_index or self.include_columns or self.exclude_columns):
            return

        if self.set_index is None:
            try:
                index_columns = dataframe.index.levels
            except AttributeError:
                index_columns = [dataframe.index.name]
        else:
            index_columns = self.set_index

        dataframe.reset_index(inplace=True)
        if self.include_columns:
            new_columns = self.include_columns
        else:
            new_columns = [x for x in dataframe.columns if x not in index_columns]

        if self.exclude_columns:
            new_columns = [x for x in new_columns if x not in self.exclude_columns]

        dataframe.set_index(index_columns, inplace=True)
        self.data = dataframe[new_columns]
        
    def render(self):
        '''supply the:class:`Renderer.Renderer` with the data to render.

        The data supplied will depend on the ``groupby`` option.

        returns a ResultBlocks data structure.
        '''
        self.debug("%s: rendering data started for %i items" %
                   (self,
                    len(self.data)))

        # initiate output structure
        results = ResultBlocks(title="")

        dataframe = self.data

        if dataframe is None:
            self.warn("%s: no data after conversion" % self)
            raise ValueError("no data for renderer")

        # special patch: set column names to pruned levels
        # if there are no column names
        if len(dataframe.columns) == len(self.pruned):
            if list(dataframe.columns) == list(range(len(dataframe.columns))):
                dataframe.columns = [x[1] for x in self.pruned]

        nlevels = Utils.getDataFrameLevels(dataframe)

        self.debug("%s: rendering data started. "
                   "levels=%i, group_level=%s" %
                   (self, nlevels,
                    str(self.group_level)))

        if self.group_level < 0:
            # no grouping for renderers that will accept
            # a dataframe with any level of indices and no explicit
            # grouping has been asked for.
            results.append(self.renderer(dataframe, path=()))
        else:
            level = Utils.getGroupLevels(
                dataframe,
                max_level=self.group_level+1)

            self.debug("%s: grouping by levels: %s" %
                       (self, str(level)))

            for key, work in dataframe.groupby(level=level):

                try:
                    results.append(self.renderer(work,
                                                 path=key))
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
                # type(Tracker.Empty) == CGATReport.Tracker.Empty
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
        except Exception as ex:
            self.error("%s: exception in collection: %s" % (self, str(ex)))
            return ResultBlocks(ResultBlocks(
                Utils.buildException("collection")))
        finally:
            self.debug("profile: finished: tracker: %s" % (self.tracker))

        if self.tree is None or len(self.tree) == 0:
            self.info("%s: no data - processing complete" % self.tracker)
            return None

        data_paths = DataTree.getPaths(self.tree)
        self.debug("%s: after collection: %i data_paths: %s" %
                   (self, len(data_paths), str(data_paths)))

        # special Renderers - do not process data further but render
        # directly. Note that no transformations will be applied.
        if isinstance(self.renderer, Renderer.User):
            results = ResultBlocks(title="main")
            results.append(self.renderer(self.tree))
            return results
        elif isinstance(self.renderer, Renderer.Debug):
            results = ResultBlocks(title="main")
            results.append(self.renderer(self.tree))
            return results

        # merge all data to hierarchical indexed dataframe
        self.data = DataTree.asDataFrame(self.tree)

        if self.data is None:
            self.info("%s: no data after conversion" % self.tracker)
            return None

        self.debug("dataframe memory usage: total=%i,data=%i,index=%i,col=%i" %
                   (self.data.values.nbytes +
                    self.data.index.nbytes +
                    self.data.columns.nbytes,
                    self.data.values.nbytes,
                    self.data.index.nbytes,
                    self.data.columns.nbytes))

        # if tracks are set by tracker, call tracker with dataframe
        if self.indexFromTracker:
            self.tracker.setIndex(self.data)

        # transform data
        try:
            self.transform()
        except:
            self.error("%s: exception in transformation" % self)
            return ResultBlocks(ResultBlocks(
                Utils.buildException("transformation")))

        # data_paths = DataTree.getPaths(self.data)
        # self.debug("%s: after transformation: %i data_paths: %s" %
        #           (self, len(data_paths), str(data_paths)))
        # restrict
        try:
            self.filterPaths(self.restrict_paths, mode="restrict")
        except:
            self.error("%s: exception in restrict" % self)
            return ResultBlocks(ResultBlocks(
                Utils.buildException("restrict")))

        # data_paths = DataTree.getPaths(self.data)
        # self.debug("%s: after restrict: %i data_paths: %s" %
        #          (self, len(data_paths), str(data_paths)))
        # exclude
        try:
            self.filterPaths(self.exclude_paths, mode="exclude")
        except:
            self.error("%s: exception in exclude" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("exclude")))

        # data_paths = DataTree.getPaths(self.data)
        # self.debug("%s: after exclude: %i data_paths: %s" %
        #          (self, len(data_paths), str(data_paths)))

        # No pruning - maybe enable later as a user option
        self.pruned = []
        # try:
        #     self.prune()
        # except:
        #     self.error("%s: exception in pruning" % self)
        #     return ResultBlocks(ResultBlocks(Utils.buildException("pruning")))

        try:
            self.reframe()
        except:
            self.error("%s: exception in reframing" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("reframing")))

        # data_paths = DataTree.getPaths(self.data)
        # self.debug("%s: after pruning: %i data_paths: %s" %
        #           (self, len(data_paths), str(data_paths)))
        try:
            self.group()
        except:
            self.error("%s: exception in grouping" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("grouping")))

        # data_paths = DataTree.getPaths(self.data)
        # self.debug("%s: after grouping: %i data_paths: %s" %
        #           (self, len(data_paths), str(data_paths)))
        if self.renderer is not None:
            self.debug("profile: started: renderer: %s" % (self.renderer))

            try:
                result = self.render()
            except:
                self.error("%s: exception in rendering" % self)
                return ResultBlocks(ResultBlocks(
                    Utils.buildException("rendering")))
            finally:
                self.debug("profile: finished: renderer: %s" % (self.renderer))
        else:
            result = ResultBlocks(title="")

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
        
    def getDataTree(self):
        '''return data tree.'''
        return self.tree

    def getDataFrame(self):
        '''return data frame.'''
        return self.data
