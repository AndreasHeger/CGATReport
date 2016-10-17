import re
import os
import sys
import imp
import io
import types
import traceback
import math
import glob
import pkgutil

from logging import debug, warn, critical
from functools import reduce

# Python 2/3 Compatibility
try:
    import configparser as configparser
except:
    import configparser

import numpy
import pandas

import CGATReport
from CGATReport.ResultBlock import ResultBlocks, ResultBlock
import CGATReport.Component as Component
import CGATReport.Config

from collections import OrderedDict as odict

ContainerTypes = (tuple, list, type(numpy.zeros(0)))
DictionaryTypes = (dict, odict)

# set with keywords that will not be pruned
# This is important for the User Tracker
TrackerKeywords = set(("text", "rst", "xls",))

# Options for rst image directive that will get passed through
# unchanged.
ImageOptions = set(("alt", "height", "width", "scale", "class"))

# Taken from numpy.scalartype, but removing the types object and unicode
# None is allowed to represent missing values. numpy.float128 is a recent
# numpy addition.
try:
    NumberTypes = (int, float, int, type(None),
                   numpy.int8, numpy.int16, numpy.int32, numpy.int64,
                   numpy.uint8, numpy.uint16, numpy.uint32, numpy.uint64,
                   numpy.float32, numpy.float64, numpy.float128)
    FloatTypes = (float,
                  numpy.float32, numpy.float64, numpy.float128)
    IntTypes = (int, int,
                numpy.int8, numpy.int16,
                numpy.int32, numpy.int64,
                numpy.uint8, numpy.uint16,
                numpy.uint32, numpy.uint64)

except AttributeError as msg:
    NumberTypes = (int, float, int, type(None),
                   numpy.int8, numpy.int16,
                   numpy.int32, numpy.int64,
                   numpy.uint8, numpy.uint16,
                   numpy.uint32, numpy.uint64,
                   numpy.float32, numpy.float64)
    FloatTypes = (float,
                  numpy.float32, numpy.float64)
    IntTypes = (int, int,
                numpy.int8, numpy.int16,
                numpy.int32, numpy.int64,
                numpy.uint8, numpy.uint16,
                numpy.uint32, numpy.uint64)


def isDataFrame(data):
    '''return True if data is a dataframe.'''
    return type(data) == pandas.DataFrame


def isDataSeries(data):
    '''return True if data is a series.'''
    return type(data) == pandas.Series


def isArray(data):
    '''return True if data is an array.'''
    return type(data) in ContainerTypes


def isMatrix(data):
    '''return True if data is a numpy matrix.

    A matrix is an array with two dimensions.
    '''
    return isinstance(data, numpy.ndarray) and len(data.shape) == 2


def isDict(data):
    '''return True if data is a dictionary'''
    return type(data) in DictionaryTypes


def isInt(obj):
    return type(obj) in IntTypes


def isFloat(obj):
    return type(obj) in FloatTypes


def isString(obj):
    # Python 3
    # return isinstance(obj, str)
    return isinstance(obj, str)


def is_numeric(obj):
    attrs = ['__add__', '__sub__', '__mul__', '__div__', '__pow__']
    return all(hasattr(obj, attr) for attr in attrs)


def asList(param):
    '''return a param as a list'''
    if type(param) not in (list, tuple):
        p = param.strip()
        if p:
            return [x.strip() for x in p.split(",")]
        else:
            return []
    else:
        return param


def quote_rst(text):
    '''quote text for restructured text.'''
    return re.sub(r"([*])", r"\\\1", str(text))


def quote_filename(text):
    '''quote filename for use as link in restructured text (remove spaces,
    quotes, slashes, etc).

    latex does not permit a "." for image files.

    Note that the quoting removes slashes and backslashes and thus removes
    any path information.

    Replace all with "_"

    '''
    return re.sub(r"""[ '"()\[\]./]""", r"_", str(text))


def getDataFrameLevels(dataframe,
                       test_for_trivial=False):

    '''return numbers of levels in the index
    of the dataframe.

    A non-hierarchical index has a level of 1.

    If test_for_trivial is set to true and the index
    is not hierarchical, return 0 if the index is
    simply the row numbers.

    '''
    index = dataframe.index
    try:
        # hierarchical index
        nlevels = len(index.levels)
    except AttributeError:
        nlevels = 1
        if test_for_trivial and isinstance(index, pandas.Int64Index) \
           and index.name is None:
            nlevels = 0
    return nlevels


def getGroupLevels(dataframe,
                   max_level=None,
                   modify_levels=None):
    '''return expression for pandas groupby statement.

    If dataframe has a multiindex, return a tuple
    of levels.

    If *modify_levels* is set to *n*, the tuple of group_levels
    will be reduced:
    If n is > 0, the first n levels are dropped. If n is negative,
    the last n levels are dropped.

    If dataframe is not a multiindex, return a level
    of 0.
    '''
    nlevels = getDataFrameLevels(dataframe)
    if nlevels == 1:
        return 0
    else:
        if max_level is not None:
            return tuple(range(min(max_level, nlevels)))
        elif modify_levels is not None:
            if modify_levels > 0:
                l = list(range(modify_levels, nlevels))
            else:
                l = list(range(0, nlevels+modify_levels))
            return tuple(l)
        else:
            return tuple(range(nlevels))


def pruneDataFrameIndex(dataframe,
                        expected_levels=None,
                        original=None):
    '''prune levels in index of a dataframe.

    If *original* is given, prune to the same
    number of levels as in *original*.

    This function is used after a pandas.concat
    operation. If the concatenated dataframes
    contain indices, they will be in the final
    result.

    This method modifies the dataframe in-place.
    '''
    if original is not None:
        expected_levels = original.index.nlevels

    if expected_levels is not None:
        nlevels = dataframe.index.nlevels
        if nlevels > expected_levels:
            dataframe.reset_index(
                level=list(range(expected_levels,
                            nlevels)),
                drop=True,
                inplace=True)


def toMultipleSeries(dataframe):
    '''split a dataframe with a hierarchical
    index into separated data series.'''

    level = getGroupLevels(dataframe)
    dataseries = []
    for key, work in dataframe.groupby(
            level=level):
        for column in work.columns:
            dataseries.append((key+(column,), work[column]))
    return dataseries


# default values
PARAMS = {
    "report_show_errors": True,
    "report_show_warnings": True,
    "report_sql_backend": "sqlite:///./csvdb",
    "report_cachedir": "_cache",
    "report_urls": "data,code,rst",
    "report_images": "hires,hires.png,200,eps,eps,50",
}


def convertValue(value, list_detection=False):
    '''convert a value to int, float or str.'''
    rx_int = re.compile("^\s*[+-]*[0-9]+\s*$")
    rx_float = re.compile("^\s*[+-]*[0-9.]+[.+\-eE][+-]*[0-9.]*\s*$")

    if value is None:
        return value

    if list_detection and "," in value:
        values = []
        for value in value.split(","):
            if rx_int.match(value):
                values.append(int(value))
            elif rx_float.match(value):
                values.append(float(value))
            else:
                values.append(value)
        return values
    else:
        if rx_int.match(value):
            return int(value)
        elif rx_float.match(value):
            return float(value)
        return value


def configToDictionary(config):
    p = {}
    for section in config.sections():
        for key, value in config.items(section):
            v = convertValue(value)
            p["%s_%s" % (section, key)] = v
            if section == "general":
                p["%s" % (key)] = v

    for key, value in list(config.defaults().items()):
        p["%s" % (key)] = convertValue(value)

    return p


def update_parameters(filenames):
    '''read one or more config files and update parameter
    dictionary.

    Sections and keys are combined with an underscore. If a key
    without section does not exist, it will be added plain.

    For example::

       [general]
       input=input1.file

       [special]
       input=input2.file

    will be entered as { 'general_input': "input1.file",
    'input: "input1.file", 'special_input': "input2.file" }

    This function also updates the module-wide parameter map.

    The section [DEFAULT] is equivalent to [general].

    '''

    global CONFIG

    CONFIG = configparser.ConfigParser()
    CONFIG.read([x for x in filenames if x])

    p = configToDictionary(CONFIG)
    PARAMS.update(p)

    return PARAMS

# DEFAULT: read parameters from config files
# in the current directory sorted by name
# If 'inifile' is in conf.py, read it first.
def get_parameters():
    return update_parameters(
        filenames=[getattr(CGATReport.Config, 'inifile', None)] +
        sorted(glob.glob("*.ini")))


def selectAndDeleteOptions(options, select):
    '''collect options in *select* and from *options* and remove those found.

    returns dictionary of options found.
    '''
    new_options = {}
    for k, v in list(options.items()):
        if k in select:
            new_options[k] = v
            del options[k]
    return new_options


def getImageFormats(display_options=None):
    '''return list of image formats to render (in addition to the default
    format).
    '''

    def _toFormat(data):
        if len(data) == 1:
            return (data[0], data[0], 100)
        elif len(data) == 2:
            return (data[0], data[1], 100)
        elif len(data) == 3:
            return (data[0], data[1], int(data[2]))
        else:
            raise ValueError(
                ":format: option expects one to three params, "
                "got {}".format(data))

    if "display" in display_options:
        all_data = [x.strip() for x in display_options["display"].split(";")]
        if len(all_data) > 1:
            warn(":display: only expects one format, additional ignored at %s" %
                 display_options["display"])
        data = asList(all_data[0])
        default_format = _toFormat(data)
    elif "report_default_format" in PARAMS:
        default_format = _toFormat(PARAMS["report_default_format"].split(","))
    else:
        default_format = CGATReport.Config.HTML_IMAGE_FORMAT

    # get default extra formats from the config file
    additional_formats = []
    if "report_images" in PARAMS:
        data = asList(PARAMS["report_images"])
        if len(data) % 3 != 0:
            raise ValueError(
                "need multiple of 3 number of arguments to report_images "
                "option, got {}".format(data))
        for x in range(0, len(data), 3):
            additional_formats.append((data[x], data[x + 1], int(data[x + 2])))
    else:
        additional_formats.extend(CGATReport.Config.ADDITIONAL_FORMATS)

    # add formats specified in the document
    if "extra-formats" in display_options:
        all_data = [x.strip() for x in
                    display_options["extra-formats"].split(";")]
        for data in all_data:
            data = asList(all_data[0])
            additional_formats.append(_toFormat(data))

    if CGATReport.Config.LATEX_IMAGE_FORMAT:
        additional_formats.append(CGATReport.Config.LATEX_IMAGE_FORMAT)

    return default_format, additional_formats


def get_default_display_options():
    """return dictionary with default display options from the config file.
    """
    
    display_options = {}
    if "report_default_width" in PARAMS:
        display_options["width"] = PARAMS["report_default_width"]
    return display_options


def getImageOptions(display_options=None, indent=0):
    '''return string with display_options for ``:image:`` directive.'''
    indent = ' ' * indent
    if display_options:
        return "\n".join(
            ['%s:%s: %s' % (indent, key, val)
             for key, val in list(display_options.items())
             if key in ImageOptions])
    else:
        return ''


# read placeholders from config file in current directory
# It would be nice to read default values, but the location
# of the documentation source files are not known to this module.
class memoized(object):

    """Decorator that caches a function's return value each time it is called.
    If called later with the same arguments, the cached value is returned, and
    not re-evaluated.
    """

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs):
        try:
            return self.cache[args+list(kwargs)]
        except KeyError:
            self.cache[args+list(kwargs)] = value = self.func(*args, **kwargs)
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args, **kwargs)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__


@memoized
def getModule(name):
    """load module in fullpat
    """
    # remove leading '.'
    debug("entered getModule with `%s`" % name)

    parts = name.split(".")
    if parts[0] == "Tracker":
        # special case: Trackers shipped with CGATReport
        if len(parts) > 2:
            raise NotImplementedError("built-in trackers are Tracker.<name> ")
        name = "Tracker"
        path = [os.path.join(CGATReport.__path__[0])]

    # the first part needs to be on the python sys.path
    elif len(parts) > 1:
        try:
            (file, pathname, description) = imp.find_module(parts[0])
        except ImportError as msg:
            warn("could not find module %s: msg=%s" % (name, msg))
            raise ImportError("could not find module %s: msg=%s" % (name, msg))

        path = [os.path.join(pathname, *parts[1:-1])]
        name = parts[-1]
    else:
        path = None

    debug("searching for module name=%s at path=%s" % (name, str(path)))

    # find module
    try:
        (modulefile, pathname, description) = imp.find_module(name, path)
    except ImportError as msg:
        warn("could not find module %s in %s: msg=%s" % (name, path, msg))
        raise ImportError(
            "could not find module %s in %s: msg=%s" % (name, path, msg))

    if modulefile is None:
        warn("could not find module %s in %s" % (name, path))
        raise ImportError(
            "find_module returned None for %s in %s" %
            (name, path))

    stdout = sys.stdout
    sys.stdout = io.StringIO()
    debug("loading module: %s: %s, %s, %s" %
          (name, modulefile, pathname, description))
    # imp.load_module modifies sys.path - save original and restore
    oldpath = sys.path

    # add to sys.path to ensure that imports in the directory work
    if pathname not in sys.path:
        sys.path.append(os.path.dirname(pathname))

    try:
        module = imp.load_module(name, modulefile, pathname, description)
    except:
        warn("could not load module %s" % name)
        raise
    finally:
        modulefile.close()
        sys.stdout = stdout
        sys.path = oldpath

    return module, pathname


def getCode(cls, pathname):
    '''retrieve code for methods and functions.'''
    # extract code
    code = []
    infile = open(pathname, "r")
    for line in infile:
        x = re.search("(\s*)(class|def)\s+%s" % cls, line)
        if x:
            indent = len(x.groups()[0])
            code.append(line)
            break
    for line in infile:
        if len(re.match("^(\s*)", line).groups()[0]) <= indent:
            break
        code.append(line)
    infile.close()

    return code


def indent(text, indent):
    '''return *text(indented by *indent*.'''
    return "\n".join([" " * indent + x for x in text.split("\n")])


def isClass(obj):
    '''return true if obj is a class.

    return False if it is a function object.
    raise ValueError if neither
    '''

    # checking for subclass of Tracker causes a problem
    # for classes defined in the module Tracker itself.
    # The problem is that 'Tracker' is CGATReport.Tracker.Tracker,
    # while the one in tracker is simply Tracker
    # issubclass(obj, Tracker) and \

    if isinstance(obj, type) and \
            hasattr(obj, "__call__"):
        return True
    elif isinstance(obj, (type, types.FunctionType)):
        return False
    elif isinstance(obj, (type, types.LambdaType)):
        return False

    raise ValueError("can not make sense of tracker %s" % str(obj))


def makeObject(path, args=(), kwargs={}):
    '''return object of type *path*

    This function is similar to an import statement, but
    also instantiates the class and returns the object.

    The object is instantiated with *args* and **kwargs**.
    '''

    # split class from module
    name, cls = os.path.splitext(path)

    # remove leading '.'
    cls = cls[1:]

    debug("instantiating class %s" % cls)

    module, pathname = getModule(name)

    # get class from module
    try:
        obj = getattr(module, cls)
    except AttributeError:
        raise AttributeError("module %s (%s) has no attribute '%s'" %
                             (module, pathname, cls))
    # instantiate, if it is a class
    if isClass(obj):
        try:
            obj = obj(*args, **kwargs)
        except AttributeError as msg:
            critical("instantiating class %s.%s failed: %s" %
                     (module, cls, msg))
            raise

    return obj, module, pathname, cls


@memoized
def makeTracker(path, args=(), kwargs={}):
    """retrieve an instantiated tracker and its associated code.

    returns a tuple (code, tracker, pathname).
    """
    obj, module, pathname, cls = makeObject(path, args, kwargs)
    code = getCode(cls, pathname)
    return code, obj, pathname


@memoized
def makeRenderer(path, args=(), kwargs={}):
    """retrieve an instantiated Renderer.

    returns the object.
    """
    obj, module, pathname, cls = makeObject(path, args, kwargs)
    return obj


@memoized
def makeTransformer(path, args=(), kwargs={}):
    """retrieve an instantiated Transformer.

    returns the object.
    """
    obj, module, pathname, cls = makeObject(path, args, kwargs)
    return obj


def buildWarning(name, message):
    '''build a cgatreport warning message with name *name*
    and message *message*.

    Note that *name* should not contain any spaces.

    '''
    if PARAMS["report_show_warnings"]:
        WARNING_TEMPLATE = '''

.. warning:: %(name)s

   * %(message)s

'''
        name = re.sub("\s", "_", name)
        return ResultBlock(WARNING_TEMPLATE % locals(),
                           title="")
    else:
        return None


def buildException(stage):
    '''build an exception text element.

    It uses the last exception.
    '''

    if PARAMS["report_show_errors"]:
        EXCEPTION_TEMPLATE = '''
.. error:: %(exception_name)s

   * stage: %(stage)s
   * exception: %(exception_name)s
   * message: %(exception_value)s
   * traceback:

%(exception_stack)s
'''

        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        lines = traceback.format_tb(exceptionTraceback)
        # remove all the ones relate to Dispatcher.py
        # xlines = filter(lambda x: not re.search("Dispatcher.py", x), lines)
        xlines = lines
        # if nothing left, use the full traceback
        if len(xlines) > 0:
            lines = xlines
        # add prefix of 6 spaces
        prefix = "\n" + " " * 6
        exception_stack = quote_rst(prefix +
                                    prefix.join("".join(lines).split("\n")))
        if exceptionType.__module__ == "exceptions":
            exception_name = quote_rst(exceptionType.__name__)
        else:
            exception_name = quote_rst(exceptionType.__module__ + '.' +
                                       exceptionType.__name__)

        exception_value = quote_rst(str(exceptionValue))

        return ResultBlock(EXCEPTION_TEMPLATE % locals(),
                           title="")
    else:
        return None


def collectExceptionAsString(msg):
    '''return exception as a string.'''
    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
    lines = traceback.format_tb(exceptionTraceback)
    return 'exception: %s\nmsg=%s\n%s' % (str(exceptionType),
                                          msg,
                                          "".join(lines))


def getTransformers(transformers, kwargs={}):
    '''find and instantiate all transformers.'''

    result = []
    for transformer in transformers:
        k = "transform-%s" % transformer
        if k in Component.getPlugins()["transform"]:
            cls = Component.getPlugins()["transform"][k]
            instance = cls(**kwargs)
        else:
            instance = makeTransformer(transformer, (), kwargs)

        if not instance:
            msg = "could not find transformer '%s'. Available transformers:\n  %s" % \
                (transformer,
                 "\n  ".join(sorted(getPlugins()["transform"].keys())))
            raise KeyError(msg)

        result.append(instance)

    return result


def updateOptions(kwargs):
    '''replace placeholders in kwargs with
    with PARAMS read from config file.

    returns the update dictionary.
    '''

    for key, value in list(kwargs.items()):
        try:
            v = value.strip()
        except AttributeError:
            # ignore non-string types
            continue

        if v.startswith("@") and v.endswith("@"):
            code = v[1:-1]
            if code in PARAMS:
                kwargs[key] = PARAMS[code]
            else:
                raise ValueError("unknown placeholder `%s`" % code)

    return kwargs


def getRenderer(renderer_name, kwargs={}):
    '''find and instantiate renderer.'''

    renderer = None

    try:
        cls = Component.getPlugins()["render"]["render-%s" % renderer_name]
        renderer = cls(**kwargs)
    except KeyError:
        # This was uncommented to fix one bug
        # but uncommenting invalidates user renderers
        # TODO: needs to be revisited
        renderer = makeRenderer(renderer_name, kwargs)

    if not renderer:
        raise KeyError(
            "could not find renderer '%s'. Available renderers:\n  %s" %
            (renderer_name,
             "\n  ".join(
                 sorted(Component.getPlugins()["render"].keys()))))

    return renderer


def my_get_data(package, resource):
    """Get a resource from a package.

    This is a wrapper round the PEP 302 loader get_data API. The package
    argument should be the name of a package, in standard module format
    (foo.bar). The resource argument should be in the form of a relative
    filename, using '/' as the path separator. The parent directory name '..'
    is not allowed, and nor is a rooted name (starting with a '/').

    The function returns a binary string, which is the contents of the
    specified resource.

    For packages located in the filesystem, which have already been imported,
    this is the rough equivalent of

        d = os.path.dirname(sys.modules[package].__file__)
        data = open(os.path.join(d, resource), 'rb').read()

    If the package cannot be located or loaded, or it uses a PEP 302 loader
    which does not support get_data(), then None is returned.
    """

    loader = pkgutil.get_loader(package)
    if loader is None or not hasattr(loader, 'get_data'):
        return None
    mod = sys.modules.get(package) or loader.load_module(package)
    if mod is None or not hasattr(mod, '__file__'):
        return None

    # Modify the resource name to be compatible with the loader.get_data
    # signature - an os.path format "filename" starting with the dirname of
    # the package's __file__
    parts = resource.split('/')
    parts.insert(0, os.path.dirname(mod.__file__))
    resource_name = os.path.join(*parts)
    return loader.get_data(resource_name)

# get_data only available in python >2.6
try:
    from pkgutil import get_data
except ImportError:
    get_data = my_get_data


def getTemplatesDir():
    '''returns the location of the templates.'''
    return os.path.join(os.path.dirname(__file__), "templates")


def normalize_cell(s, length):
    return s + ((length - len(s)) * ' ')


def table_div(num_cols, col_width, header_flag):
    if header_flag == 1:
        return num_cols*('+' + (col_width)*'=') + '+\n'
    else:
        return num_cols*('+' + (col_width)*'-') + '+\n'


def table2rst(table):
    """convert a table (list of lists) to rst table.
    """
    cell_width = 2 + max(
        reduce(lambda x,y: x+y,
               [[max(list(map(len, str(item).split('\n')))) for item in row]
                for row in table], []))
    num_cols = len(table[0])
    rst = table_div(num_cols, cell_width, 0)
    header_flag = 1
    for row in table:
        split_row = [str(cell).split('\n') for cell in row]
        lines_remaining = 1

        while lines_remaining > 0:
            normalized_cells = []
            lines_remaining = 0
            for cell in split_row:
                lines_remaining += len(cell)

                if len(cell) > 0:
                    normalized_cell = normalize_cell(
                        str(cell.pop(0)), cell_width - 1)
                else:
                    normalized_cell = normalize_cell(
                        '', cell_width - 1)

                normalized_cells.append(normalized_cell)

            rst = rst + '| ' + '| '.join(normalized_cells) + '|\n'

        rst = rst + table_div(num_cols, cell_width, header_flag)
        header_flag = 0

    return rst


def layoutBlocks(blocks, layout="column"):
    """layout blocks of rst text.

    layout can be one of "column", "row", or "grid".

    The layout uses an rst table to arrange elements.
    """

    lines = []
    if len(blocks) == 0:
        return lines

    # flatten blocks
    bb = ResultBlocks()
    for b in blocks:
        if b.title:
            b.updateTitle(b.title, "prefix")
        try:
            bb.extend(b)
        except TypeError:
            bb.append(b)

    blocks = bb

    # check if postambles are identical across all blocks
    postambles = set([b.postamble for b in blocks])

    if len(postambles) == 1:
        blocks.clearPostamble()
        postamble = postambles.pop()
    else:
        postamble = None

    if layout == "column":
        for block in blocks:
            if block.title:
                lines.extend(block.title.split("\n"))
                lines.append("")
            else:
                warn("report_directive.layoutBlocks: missing title")

            lines.extend(block.text.split("\n"))
            lines.extend(block.postamble.split("\n"))

        lines.append("")

        if postamble:
            lines.extend(postamble.split("\n"))
            lines.append("")
        return lines

    elif layout in ("row", "grid"):
        if layout == "row":
            ncols = len(blocks)
        elif layout == "grid":
            ncols = int(math.ceil(math.sqrt(len(blocks))))

    elif layout.startswith("column"):
        ncols = min(len(blocks), int(layout.split("-")[1]))
        # TODO: think about appropriate fix for empty data
        if ncols == 0:
            ncols = 1
            return lines
    else:
        raise ValueError("unknown layout %s " % layout)

    if ncols == 0:
        warn("no columns")
        return lines

    # compute column widths
    widths = [x.getWidth() for x in blocks]
    text_heights = [x.getTextHeight() for x in blocks]
    title_heights = [x.getTitleHeight() for x in blocks]

    columnwidths = []
    for x in range(ncols):
        columnwidths.append(max([widths[y] for y in
                                 range(x, len(blocks), ncols)]))

    separator = "+%s+" % "+".join(["-" * x for x in columnwidths])

    # add empty blocks
    if len(blocks) % ncols:
        blocks.extend([ResultBlock("", "")] * (ncols - len(blocks) % ncols))

    for nblock in range(0, len(blocks), ncols):

        # add text
        lines.append(separator)
        max_height = max(text_heights[nblock:nblock + ncols])
        new_blocks = ResultBlocks()

        for xx in range(nblock, min(nblock + ncols, len(blocks))):
            txt, col = blocks[xx].text.split("\n"), xx % ncols
            txt = blocks[xx].text.split("\n") + \
                  blocks[xx].postamble.split("\n")
            col = xx % ncols

            max_width = columnwidths[col]

            # add missig lines
            txt.extend([""] * (max_height - len(txt)))
            # extend lines
            txt = [x + " " * (max_width - len(x)) for x in txt]

            new_blocks.append(txt)

        for l in zip(*new_blocks):
            lines.append("|%s|" % "|".join(l))

        # add subtitles
        max_height = max(title_heights[nblock:nblock + ncols])

        if max_height > 0:

            new_blocks = ResultBlocks()
            lines.append(separator)

            for xx in range(nblock, min(nblock + ncols, len(blocks))):

                txt, col = blocks[xx].title.split("\n"), xx % ncols

                max_width = columnwidths[col]
                # add missing lines
                txt.extend([""] * (max_height - len(txt)))
                # extend lines
                txt = [x + " " * (max_width - len(x)) for x in txt]

                new_blocks.append(txt)

            for l in zip(*new_blocks):
                lines.append("|%s|" % "|".join(l))

    lines.append(separator)

    if postamble:
        lines.append(postamble)

    lines.append("")

    return lines


def getOutputDirectory():
    return os.path.join('_static', 'report_directive')


def build_paths(reference):
    '''return paths and filenames for a tracker.

    Reference is usually a Tracker such as "Tracker.TrackerImages".
    '''
    basedir, name = os.path.split(reference)
    # quote name to filename
    filename = quote_filename(name)
    basename, ext = os.path.splitext(filename)
    # note: outdir had basedir at the end?
    outdir = getOutputDirectory()
    codename = os.path.join(basedir, filename) + ".code"
    notebookname = os.path.join(basedir, filename) + ".notebook"

    return basedir, filename, basename, ext, outdir, codename, notebookname

NOTEBOOK_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<script src="%(staticdir)s/jquery.min.js"></script>
<script src="%(staticdir)s/notebook.js"></script>
<script>
$(document).ready(function() {
$("#rendered").click(function(){
    create_notebook('%(rendered_options)s');})
});
$(document).ready(function() {
$("#data").click(function(){
    create_notebook('%(data_options)s');})
});
</script>

</head>
<body>

<h1>Notebook integration</h1>

<p>
Click on the buttons below to import the figure
or the data into your notebook.
</p>
<button type="button" id="data">Data</button>
<button type="button" id="rendered">Figure</button>

<h2>Copy and Paste</h2>
Copy and paste the text below for importing the data
in your notebook without rendering.

<pre>
%%matplotlib inline
import CGATReport.test
result = CGATReport.test.main(%(data_options)s)
</pre>

Copy and paste below for importing the rendered
display item in your notebook.
<pre>
%%matplotlib inline
import CGATReport.test
result = CGATReport.test.main(%(rendered_options)s)
</pre>

</body>
</html>
"""

NOTEBOOK_TEXT_TEMPLATE = """
%%matplotlib inline
import CGATReport.test
result = CGATReport.test.main(%(options)s)
"""


def writeNoteBookEntry(outfile, tracker, renderer, transformers,
                       tracker_path, options):
    '''output text for pasting into an ipython notebook into *outfile*
    '''

    cmd_options = [
        'do_print = False',
        'tracker="%s"' % tracker,
        'trackerdir="%s"' % os.path.dirname(tracker_path),
        'workdir="%s"' % os.getcwd()]

    for key, val in options:
        if val is None:
            cmd_options.append("%s" % key)
        else:
            if isString(val):
                cmd_options.append('%s="%s"' % (key, val))
            else:
                cmd_options.append("%s=%s" % (key, str(val)))

    if transformers:
        cmd_options.append('transformers=["%s"]' % '","'.join(transformers))

    # For the javascript to work, the options must not contain any
    # single quotes.
    rendered_options = ",".join(cmd_options + ['renderer="%s"' % renderer])
    data_options = ",".join(cmd_options + ['renderer="none"'])
    if "'" in rendered_options:
        warn("notebook options contain ': %s" % (rendered_options))

    # no module name in tracker
    # javascript files life in the "_static" directory, while
    # the notebook entry will end up in "_static/report_directive"
    params = {"rendered_options": rendered_options,
              "data_options": data_options,
              "curdir": os.getcwd(),
              "staticdir": ".."}

    outfile.write(NOTEBOOK_TEMPLATE % params)


def buildRstWithImage(outname,
                      outdir, rstdir, builddir, srcdir,
                      additional_formats,
                      tracker_id,
                      links,
                      display_options,
                      default_format=None,
                      is_html=False,
                      text=None):
    '''output rst text for inserting an image.'''
    rst_output = ""

    # path to build directory from rst directory
    rst2builddir = os.path.join(os.path.relpath(builddir,
                                                start=rstdir), outdir)

    # path to src directory from rst directory
    rst2srcdir = os.path.join(os.path.relpath(srcdir,
                                              start=rstdir), outdir)

    # for image directive - image path is relative from rst file to
    # external build dir
    imagepath = re.sub("\\\\", "/",
                       os.path.join(rst2builddir,
                                    outname))

    # for links - path is from rst file to internal root dir
    relative_imagepath = re.sub("\\\\", "/",
                                os.path.join(
                                    rst2srcdir,
                                    outname))

    requested_urls = asList(PARAMS["report_urls"])

    image_options = getImageOptions(display_options, indent=6)

    if CGATReport.Config.HTML_IMAGE_FORMAT:

        if default_format:
            id, format, dpi = default_format
        else:
            id, format, dpi = CGATReport.Config.HTML_IMAGE_FORMAT

        #######################################################
        # Define templates
        if text is not None:

            template = '''
.. only:: html

   .. raw:: html

      <div><p>
         %(outname)s
      <p><div>

   %(url)s
'''
            # put text in outname
            outname = indent(text, 6)

        elif is_html:
            # put in html
            template = '''
.. only:: html

   .. raw:: html
      :file: %(outname)s

   %(url)s
'''
            # use absolute path for html file
            outname = os.path.abspath(os.path.join(outdir, outname)) + ".html"

        else:
            # put in image directive
            template = '''
.. only:: html

   .. image:: %(linked_image)s
%(image_options)s

   %(url)s

.. only:: pdf

   .. image:: %(linked_image)s
%(image_options)s
'''
            linked_image = imagepath + ".%s" % format
        #######################################################

        extra_images = []
        for id, format, dpi in additional_formats:
            extra_images.append(
                ":download:`%(id)s <%(imagepath)s.%(format)s>`" %
                locals())
        if extra_images:
            extra_images = " " + " ".join(extra_images)
        else:
            extra_images = ""

        # construct additional urls
        urls = []
        if "code" in requested_urls:
            urls.append(":download:`code <%(code_url)s>`" % links)
        if "notebook" in requested_urls:
            urls.append(":download:`nb <%(notebook_url)s>`" % links)
        if "data" in requested_urls:
            urls.append(":download:`data </data/%(tracker_id)s>`" % locals())
        if "rst" in requested_urls and links["rst_url"] is not None:
            urls.append(":download:`rst <%(rst_url)s>`" % links)
        if extra_images:
            urls.append(extra_images)

        if urls and "no-links" not in display_options:
            url = "[{}]".format(" ".join(urls))
        else:
            url = ""
        
        rst_output += template % locals()

    # treat latex separately
    if CGATReport.Config.LATEX_IMAGE_FORMAT:
        id, format, dpi = CGATReport.Config.LATEX_IMAGE_FORMAT
        template = '''
.. only:: latex

   .. image:: %(linked_image)s
%(image_options)s
'''
        linked_image = imagepath + ".%s" % format
        rst_output += template % locals()

    return rst_output
