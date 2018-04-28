import re
import os
import sys
import traceback
import math
import glob
import pkgutil
import pandas

from logging import warning
from functools import reduce
import multiprocessing

# Python 2/3 Compatibility
try:
    import ConfigParser as configparser
except:
    import configparser


import CGATReport
from CGATReport.ResultBlock import ResultBlocks, ResultBlock
import CGATReport.Component as Component
import CGATReport.Config
from CGATReport.Types import quote_filename, quote_rst, is_string, as_list

# set with keywords that will not be pruned
# This is important for the User Tracker
TrackerKeywords = set(("text", "rst", "xls",))

# Options for rst image directive that will get passed through
# unchanged.
ImageOptions = set(("alt", "height", "width", "scale", "class"))

# TODO: make configurable parameter
# TODO: create configuration system
MAX_BLOCKS_PER_TAB = 6

# default values
PARAMS = {
    "report_show_errors": True,
    "report_show_warnings": True,
    "report_sql_backend": "sqlite:///./csvdb",
    "report_cachedir": "_cache",
    "report_urls": "data,code,rst",
    "report_images": "hires,hires.png,200,eps,eps,50",
}


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
            return self.cache[args + list(kwargs)]
        except KeyError:
            self.cache[
                args + list(kwargs)] = value = self.func(*args, **kwargs)
            return value
        except TypeError:
            # uncachable -- for instance, passing a list as an argument.
            # Better to not cache than to blow up entirely.
            return self.func(*args, **kwargs)

    def __repr__(self):
        """Return the function's docstring."""
        return self.func.__doc__


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
                l = list(range(0, nlevels + modify_levels))
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
            dataseries.append((key + (column,), work[column]))
    return dataseries


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

def limit_file_path(path,
                    max_length=255,
                    component_sep="-_",
                    join_sep="-"):
    """if a path is longer than max_length, try to truncate
    the filename part."""

    take = 5
    while len(path) > max_length and take > 0:
        dirname, basename = os.path.split(path)
        components = re.split("[{}]".format(component_sep),
                              basename)
        new_components = []
        for component in components:
            if len(component) > 2 * take:
                component = component[:take] + component[-take:]
            new_components.append(component)
        basename = join_sep.join(new_components)
        path = os.path.join(dirname, basename)
        take -= 1
    return path


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
            warning(":display: only expects one format, additional ignored at %s" %
                    display_options["display"])
        data = as_list(all_data[0])
        default_format = _toFormat(data)
    elif "report_default_format" in PARAMS:
        default_format = _toFormat(PARAMS["report_default_format"].split(","))
    else:
        default_format = CGATReport.Config.HTML_IMAGE_FORMAT

    # get default extra formats from the config file
    additional_formats = []
    if "report_images" in PARAMS:
        data = as_list(PARAMS["report_images"])
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
            data = as_list(all_data[0])
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


def indent(text, indent):
    '''return *text(indented by *indent*.'''
    return "\n".join([" " * indent + x for x in text.split("\n")])


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
        return num_cols * ('+' + (col_width) * '=') + '+\n'
    else:
        return num_cols * ('+' + (col_width) * '-') + '+\n'


def table2rst(table):
    """convert a table (list of lists) to rst table.
    """
    cell_width = 2 + max(
        reduce(lambda x, y: x + y,
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


def layoutBlocks(blocks, layout="column", long_titles=False):
    """layout blocks of rst text.

    layout can be one of "column", "row", "grid" or "tabs".

    The ``tabs`` layout requires the ``sphinx-tabs`` extension.

    The layout uses an rst table to arrange elements.
    """

    logger = Component.get_logger()

    lines = []
    if len(blocks) == 0:
        return lines

    # flatten blocks
    # bb = ResultBlocks()
    # for b in blocks:
    #     if b.title:
    #         b.updateTitle(b.title, "prefix")
    #     try:
    #         bb.extend(b)
    #     except TypeError:
    #         bb.append(b)
    # blocks = bb

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
                logger.warning("report_directive.layoutBlocks: missing title")

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

    elif layout == "tabs":
        if not long_titles:
            blocks.shorten_titles()

        # limit tabs. This could be made more intelligent by:
        # A. taking into account title lengths
        # B. wrap titles around in Java-script
        # C. ...
        for nblock in range(0, len(blocks), MAX_BLOCKS_PER_TAB):
            block_group = blocks[nblock:nblock + MAX_BLOCKS_PER_TAB]

            lines.append(".. tabs::")
            lines.append("")

            for blockid, block in enumerate(block_group):
                if block.title:
                    lines.append("   .. tab:: {}".format(block.title))
                else:
                    lines.append("   .. tab:: tab{}".format(blockid))

                lines.append("")
                lines.extend(indent(block.text, 6).split("\n"))
                lines.append("")
                lines.extend(block.postamble.split("\n"))

            lines.append("")

            if postamble:
                lines.extend(postamble.split("\n"))
                lines.append("")

            lines.append("")
            lines.append("")

        return lines

    else:
        raise ValueError("unknown layout %s " % layout)

    if ncols == 0:
        logger.warn("no columns")
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
        blocks.extend(ResultBlocks(
            [ResultBlock("", "")] * (ncols - len(blocks) % ncols)))

    for nblock in range(0, len(blocks), ncols):

        ##################################################
        # add content cells to layout
        lines.append(separator)
        max_height = max(text_heights[nblock:nblock + ncols])
        per_cell_lines = []

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

            per_cell_lines.append(txt)

        for row in zip(*per_cell_lines):
            lines.append("|%s|" % "|".join(row))

        ##################################################
        # add subtitle cells to layout
        max_height = max(title_heights[nblock:nblock + ncols])
        if max_height > 0:

            per_cell_lines = []
            lines.append(separator)

            for xx in range(nblock, min(nblock + ncols, len(blocks))):

                txt, col = blocks[xx].title.split("\n"), xx % ncols

                max_width = columnwidths[col]
                # add missing lines
                txt.extend([""] * (max_height - len(txt)))
                # extend lines
                txt = [x + " " * (max_width - len(x)) for x in txt]

                per_cell_lines.append(txt)

            for row in zip(*per_cell_lines):
                lines.append("|%s|" % "|".join(row))

    lines.append(separator)

    if postamble:
        lines.append(postamble)

    lines.append("")

    return lines


def get_params():
    return PARAMS


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

    logger = Component.get_logger()

    cmd_options = [
        'do_print = False',
        'tracker="%s"' % tracker,
        'trackerdir="%s"' % os.path.dirname(tracker_path),
        'workdir="%s"' % os.getcwd()]

    for key, val in options:
        if val is None:
            cmd_options.append("%s" % key)
        else:
            if is_string(val):
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
        logger.warning("notebook options contain ': %s" % (rendered_options))

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

    requested_urls = as_list(PARAMS["report_urls"])

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
