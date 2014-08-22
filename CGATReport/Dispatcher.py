import os
import sys
import re
import shelve
import traceback
import pickle
import types
import itertools

from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from CGATReport import DataTree
from CGATReport.Component import *
from CGATReport import Utils
from CGATReport import Cache
from CGATReport import Tracker

# move User renderer to CGATReport main distribution
from CGATReportPlugins import Renderer
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
        self.group_level = 0

    def __del__(self):
        pass

    def getCaption(self):
        """return a caption string."""
        return self.__doc__

    def parseArguments(self, *args, **kwargs):
        '''argument parsing.'''

        self.groupby = kwargs.get("groupby", "default")
        try:
            self.groupby = int(self.groupby)
        except ValueError:
            pass

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
                self.tracker, len(all_paths)))
            raise ValueError(
                "%s: number of nesting in data paths too large: %i" % (
                    self.tracker, len(all_paths)))

        all_paths = list(itertools.product(*datapaths))
        self.debug(
            "%s: collecting data started for %i data paths" % (
                self.tracker,
                len(all_paths)))

        self.data = odict()
        for path in all_paths:

            d = self.getData(path)

            # ignore empty data sets
            if d is None:
                continue

            # save in data tree as leaf
            DataTree.setLeaf(self.data, path, d)

        self.debug(
            "%s: collecting data finished for %i data paths" % (
                self.tracker,
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
                        "%s: ignoring path %s because of:"
                        "exclude:=%s" % (self.tracker, path, s))
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
                            "%s: ignoring path %s because of: "
                            "exclude:=%s" % (self.tracker, path, s))
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
        '''rearrange dataframe for desired grouping.

        Through grouping the dataframe is rearranged such that the
        level at which data will be grouped will be the first level in
        hierarchical index.

        If grouping by "track" is set, additional level will be added
        to ensure that grouping will happen.

        If grouping by "slice" is set, the first two levels will
        be swopped.

        The group level indicates at which level in the nested dictionary
        the data will be grouped with 0 indicating that everything will
        grouped together.
        '''

        nlevels = Utils.getDataFrameLevels(self.data)
        default_level = self.renderer.group_level
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
                    [1, 0] + range(2, nlevels))
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

        debug("grouping: nlevel=%i, groupby=%s, default=%s, group=%i" %
              (nlevels, groupby, str(default_level), self.group_level))

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
        self.debug("%s: rendering data started for %i items" %
                   (self,
                    len(self.data)))

        # initiate output structure
        results = ResultBlocks(title="")

        dataframe = self.data

        # dataframe.write_csv("test.csv")

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
            level = Utils.getGroupLevels(dataframe,
                                         max_level=self.group_level+1)

            debug("%s: grouping by levels: %s" % (self, str(level)))

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
        except:
            self.error("%s: exception in collection" % self)
            return ResultBlocks(ResultBlocks(
                Utils.buildException("collection")))
        finally:
            self.debug("profile: finished: tracker: %s" % (self.tracker))

        if len(self.data) == 0:
            self.info("%s: no data - processing complete" % self.tracker)
            return None

        data_paths = DataTree.getPaths(self.data)
        self.debug("%s: after collection: %i data_paths: %s" %
                   (self, len(data_paths), str(data_paths)))

        # merge all data to hierarchical indexed dataframe
        self.data = DataTree.asDataFrame(self.data)
        # transform data
        try:
            self.debug('transformations disabled')
            self.transform()
        except:
            self.error("%s: exception in transformation" % self)
            return ResultBlocks(ResultBlocks(
                Utils.buildException("transformation")))

        # data_paths = DataTree.getPaths(self.data)
        # self.debug("%s: after transformation: %i data_paths: %s" %
        #           (self, len(data_paths), str(data_paths)))

        # special Renderers - do not process data further but render directly
        if isinstance(self.renderer, Renderer.User):
            results = ResultBlocks(title="main")
            results.append(self.renderer(self.data, ('')))
            return results
        elif isinstance(self.renderer, Renderer.Debug):
            results = ResultBlocks(title="main")
            results.append(self.renderer(self.data, ('')))
            return results

        # restrict
        try:
            self.debug('restrictions disabled')
            # self.restrict()
        except:
            self.error("%s: exception in restrict" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("restrict")))

        # data_paths = DataTree.getPaths(self.data)
        # self.debug("%s: after restrict: %i data_paths: %s" %
        #          (self, len(data_paths), str(data_paths)))

        # exclude
        try:
            self.debug('exclusions disabled')
            # self.exclude()
        except:
            self.error("%s: exception in exclude" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("exclude")))

        # data_paths = DataTree.getPaths(self.data)
        # self.debug("%s: after exclude: %i data_paths: %s" %
        #          (self, len(data_paths), str(data_paths)))

        # remove superfluous levels
        try:
            self.pruned = []
            self.debug('pruning disabled')
            # self.prune()
        except:
            self.error("%s: exception in pruning" % self)
            return ResultBlocks(ResultBlocks(Utils.buildException("pruning")))

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

        self.debug("profile: started: renderer: %s" % (self.renderer))

        try:
            result = self.render()
        except:
            self.error("%s: exception in rendering" % self)
            return ResultBlocks(ResultBlocks(
                Utils.buildException("rendering")))
        finally:
            self.debug("profile: finished: renderer: %s" % (self.renderer))

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
