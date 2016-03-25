"""A special directive for including a matplotlib plot.

Given a path to a .py file, it includes the source code inline, then:

- On HTML, will include a .png with a link to a high-res .png.

- On LaTeX, will include a .pdf

This directive supports all of the options of the `image` directive,
except for `target` (since plot will add its own target).

"""

import os
import hashlib
import re
import logging
import collections

from docutils.parsers.rst import directives
from docutils.parsers.rst import Directive

from CGATReport import Config, Dispatcher, Utils, Cache, Component
from CGATReport.ResultBlock import ResultBlocks

CGATREPORT_DEBUG = "CGATREPORT_DEBUG" in os.environ

TEMPLATE_TEXT = """
.. only:: html

   %(url_template)s

"""


def out_of_date(original, derived):
    """
    Returns True if derivative is out-of-date wrt original,
    both of which are full file paths.
    """
    return (not os.path.exists(derived)
            or os.stat(derived).st_mtime < os.stat(original).st_mtime)


def run(arguments,
        options,
        lineno,
        content,
        state_machine=None,
        document=None,
        srcdir=None,
        builddir=None):
    """process:report: directive.

    *srdir* - top level directory of rst documents
    *builddir* - build directory
    """

    tag = "%s:%i" % (str(document), lineno)

    logger = Component.get_logger()

    logger.debug("report_directive.run: profile: started: rst: %s" % tag)

    # sort out the paths
    # reference is used for time-stamping
    tracker_name = directives.uri(arguments[0])

    (basedir, fname, basename, ext, outdir,
     codename, notebookname) = Utils.build_paths(tracker_name)

    # get the directory of the rst file
    # state_machine.document.attributes['source'])
    rstdir, rstfile = os.path.split(document)
    # root of document tree
    if srcdir is None:
        srcdir = setup.srcdir

    # build directory
    if builddir is None:
        builddir = setup.builddir

    # remove symbolic links
    srcdir, builddir, rstdir = [
        os.path.abspath(os.path.realpath(x)) for x in (srcdir, builddir, rstdir)]

    # there are three directories:
    # builddir = directory where document is built in
    #            (usually _build/html or similar)
    # rstdir   = directory where rst sources are located
    # srcdir   = directory from which the build process is started

    # path to root relative to rst
    rst2srcdir = os.path.join(os.path.relpath(srcdir, start=rstdir), outdir)

    # path to root relative to rst
    rst2builddir = os.path.join(
        os.path.relpath(builddir, start=rstdir), outdir)

    # path relative to source (for images)
    root2builddir = os.path.join(
        os.path.relpath(builddir, start=srcdir), outdir)

    logger.debug(
        "report_directive.run: arguments=%s, options=%s, lineno=%s, "
        "content=%s, document=%s" %
        (str(arguments),
         str(options),
         str(lineno),
         str(content),
         str(document)))
    logger.debug(
        "report_directive.run: plotdir=%s, basename=%s, ext=%s, "
        "fname=%s, rstdir=%s, srcdir=%s, builddir=%s" %
        (tracker_name, basename, ext, fname, rstdir, srcdir, builddir))
    logger.debug(
        "report_directive.run: tracker_name=%s, basedir=%s, "
        "rst2src=%s, root2build=%s, outdir=%s, codename=%s" %
        (tracker_name, basedir, rst2srcdir, rst2builddir, outdir, codename))

    # try to create. If several processes try to create it,
    # testing with `if` will not work.
    try:
        os.makedirs(outdir)
    except OSError as msg:
        pass

    if not os.path.exists(outdir):
        raise OSError("could not create directory %s: %s" % (outdir, msg))

    ########################################################
    # collect options
    # replace placedholders
    try:
        options = Utils.updateOptions(options)
    except ValueError as msg:
        logger.warn("failure while updating options: %s" % msg)

    logger.debug("report_directive.run: options=%s" % (str(options),))

    transformer_names = []
    renderer_name = None

    layout = options.get("layout", "column")
    option_map = Component.getOptionMap()
    renderer_options = Utils.selectAndDeleteOptions(
        options, option_map["render"])
    transformer_options = Utils.selectAndDeleteOptions(
        options, option_map["transform"])
    dispatcher_options = Utils.selectAndDeleteOptions(
        options, option_map["dispatch"])
    tracker_options = Utils.selectAndDeleteOptions(
        options, option_map["tracker"])
    display_options = Utils.get_default_display_options()
    display_options.update(Utils.selectAndDeleteOptions(
        options, option_map["display"]))

    logger.debug("report_directive.run: renderer options: %s" %
                  str(renderer_options))
    logger.debug("report_directive.run: transformer options: %s" %
                  str(transformer_options))
    logger.debug("report_directive.run: dispatcher options: %s" %
                  str(dispatcher_options))
    logger.debug("report_directive.run: tracker options: %s" %
                  str(tracker_options))
    logger.debug("report_directive.run: display options: %s" %
                  str(display_options))

    if "transform" in display_options:
        transformer_names = display_options["transform"].split(",")
        del display_options["transform"]

    if "render" in display_options:
        renderer_name = display_options["render"]
        del display_options["render"]

    ########################################################
    # check for missing files
    if renderer_name is not None:

        options_key = str(renderer_options) +\
            str(transformer_options) +\
            str(dispatcher_options) +\
            str(tracker_options) +\
            str(transformer_names) +\
            re.sub("\s", "", "".join(content))
                
        options_hash = hashlib.md5(options_key.encode()).hexdigest()

        template_name = Utils.quote_filename(
            Config.SEPARATOR.join((tracker_name, renderer_name,
                                   options_hash)))
        filename_text = os.path.join(outdir, "%s.txt" % (template_name))
        rstname = os.path.basename(filename_text)
        notebookname += options_hash

        logger.debug("report_directive.run: options_hash=%s" % options_hash)

        ###########################################################
        # check for existing files
        # update strategy does not use file stamps, but checks
        # for presence/absence of text element and if all figures
        # mentioned in the text element are present
        ###########################################################
        queries = [re.compile("%s/(\S+.%s)" %
                              (root2builddir, suffix))
                   for suffix in ("png", "pdf", "svg")]

        logger.debug("report_directive.run: checking for changed files.")

        # check if text element exists
        if os.path.exists(filename_text):

            with open(filename_text, "r") as inf:
                lines = [x[:-1] for x in inf]
            filenames = []

            # check if all figures are present
            for line in lines:
                for query in queries:
                    x = query.search(line)
                    if x:
                        filenames.extend(list(x.groups()))

            filenames = [os.path.join(outdir, x) for x in filenames]

            logger.debug(
                "report_directive.run: %s: checking for %s" %
                (tag, str(filenames)))
            for filename in filenames:
                if not os.path.exists(filename):
                    logger.info(
                        "report_directive.run: %s: redo: file %s is missing" %
                        (tag, filename))
                    break
            else:
                logger.info(
                    "report_directive.run: %s: noredo: all files are present" %
                    tag)
                # all is present - save text and return
                if lines and state_machine:
                    state_machine.insert_input(
                        lines, state_machine.input_lines.source(0))
                return []
        else:
            logger.debug(
                "report_directive.run: %s: no check performed: %s missing" %
                (tag, str(filename_text)))
    else:
        template_name = ""
        filename_text = None

    ##########################################################
    # Initialize collectors
    collectors = []
    for collector in list(Component.getPlugins("collect").values()):
        collectors.append(collector())

    ##########################################################
    # instantiate tracker, dispatcher, renderer and transformers
    # and collect output
    ###########################################################
    try:
        ########################################################
        # find the tracker
        logger.debug(
            "report_directive.run: collecting tracker %s with options %s " %
            (tracker_name, tracker_options))
        code, tracker, tracker_path = Utils.makeTracker(
            tracker_name, (), tracker_options)
        if not tracker:
            logger.error(
                "report_directive.run: no tracker - no output from %s " %
                str(document))
            raise ValueError("tracker `%s` not found" % tracker_name)

        logger.debug(
            "report_directive.run: collected tracker %s" % tracker_name)

        tracker_id = Cache.tracker2key(tracker)

        ########################################################
        # determine the transformer
        logger.debug("report_directive.run: creating transformers")

        transformers = Utils.getTransformers(
            transformer_names, transformer_options)

        ########################################################
        # determine the renderer
        logger.debug("report_directive.run: creating renderer.")

        if renderer_name is None:
            logger.error(
                "report_directive.run: no renderer - no output from %s" %
                str(document))
            raise ValueError("the report directive requires a renderer")

        renderer = Utils.getRenderer(renderer_name, renderer_options)

        try:
            renderer.set_paths(rstdir, srcdir, builddir)
            renderer.set_display_options(display_options)
        except AttributeError:
            # User renderers will not have these methods
            pass

        ########################################################
        # create and call dispatcher
        logger.debug("report_directive.run: creating dispatcher")

        dispatcher = Dispatcher.Dispatcher(tracker,
                                           renderer,
                                           transformers)

        # add the tracker options
        dispatcher_options.update(tracker_options)

        blocks = dispatcher(**dispatcher_options)

        if blocks is None:
            blocks = ResultBlocks(ResultBlocks(
                Utils.buildWarning(
                    "NoData",
                    "tracker %s returned no Data" % str(tracker))))
            code = None
            tracker_id = None

    except:

        logger.warn(
            "report_directive.run: exception caught at %s:%i - see document" %
            (str(document), lineno))

        blocks = ResultBlocks(ResultBlocks(
            Utils.buildException("invocation")))
        code = None
        tracker_id = None

    logger.debug(
        "report_directive.run: profile: started: collecting: %s" % tag)

    ########################################################
    # write code output
    linked_codename = re.sub("\\\\", "/", os.path.join(rst2builddir, codename))
    if code and basedir != outdir:
        with open(os.path.join(outdir, codename), "w") as outfile:
            for line in code:
                outfile.write(line)

    ########################################################
    # write notebook snippet
    linked_notebookname = re.sub(
        "\\\\", "/", os.path.join(rst2builddir, notebookname))

    if basedir != outdir and tracker_id is not None:
        with open(os.path.join(outdir, notebookname), "w") as outfile:
            Utils.writeNoteBookEntry(outfile,
                                     renderer=renderer_name,
                                     tracker=tracker_name,
                                     transformers=transformer_names,
                                     tracker_path=tracker_path,
                                     options=renderer_options.items() +
                                     tracker_options.items() +
                                     transformer_options.items())

    if filename_text is not None:
        linked_rstname = re.sub(
            "\\\\", "/", os.path.join(rst2builddir, rstname))
    else:
        linked_rstname = None

    ###########################################################
    # collect images
    ###########################################################
    map_figure2text = {}
    links = {'code_url': linked_codename,
             'rst_url': linked_rstname,
             'notebook_url': linked_notebookname}
    try:
        for collector in collectors:
            map_figure2text.update(collector.collect(
                blocks,
                template_name,
                outdir,
                rstdir,
                builddir,
                srcdir,
                content,
                display_options,
                tracker_id,
                links=links))
    except:

        logger.warn("report_directive.run: exception caught while "
                     "collecting with %s at %s:%i - see document" %
                     (collector, str(document), lineno))
        blocks = ResultBlocks(ResultBlocks(
            Utils.buildException("collection")))
        code = None
        tracker_id = None

    ###########################################################
    # replace place holders or add text
    ###########################################################
    # add default for text-only output
    requested_urls = Utils.asList(Utils.PARAMS["report_urls"])

    urls = []
    if "code" in requested_urls:
        urls.append(":download:`code <%(code_url)s>`" % links)

    if "notebook" in requested_urls:
        urls.append(":download:`nb <%(notebook_url)s>`" % links)
    
    map_figure2text["default-prefix"] = ""
    map_figure2text["default-suffix"] = ""

    if urls and "no-links" not in display_options:
        url_template = "[{}]".format(" ".join(urls))
    else:
        url_template = ""

    map_figure2text["default-prefix"] = TEMPLATE_TEXT % locals()

    blocks.updatePlaceholders(map_figure2text)

    # render the output taking into account the layout
    lines = Utils.layoutBlocks(blocks, layout)
    lines.append("")

    # add caption
    if content and "no-caption" not in display_options:
        lines.extend(['::', ''])
        lines.extend(['    %s' % row.strip() for row in content])
        lines.append("")

    # output rst text for this renderer
    if filename_text:
        outfile = open(filename_text, "w")
        outfile.write("\n".join(lines))
        outfile.close()

    if CGATREPORT_DEBUG:
        for x, l in enumerate(lines):
            print("%5i %s" % (x, l))

    if len(lines) and state_machine:
        state_machine.insert_input(
            lines, state_machine.input_lines.source(0))

    logger.debug(
        "report_directive.run: profile: finished: collecting: %s" % tag)
    logger.debug(
        "report_directive.run: profile: finished: rst: %s:%i" %
        (str(document), lineno))

    return []


class report_directive(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = True
    final_argument_whitespace = True

    # build option spec
    option_spec = Component.getOptionSpec()

    def run(self):
        document = self.state.document.current_source
        logger = Component.get_logger()
        logger.info("report_directive: starting: %s:%i" %
                     (str(document), self.lineno))

        return run(self.arguments,
                   self.options,
                   self.lineno,
                   self.content,
                   self.state_machine,
                   document)


def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir
    setup.srcdir = app.srcdir
    setup.builddir = os.getcwd()
    app.add_directive('report', report_directive)

    # update global parameters in Utils module.
    PARAMS = Utils.get_parameters()
    app.add_config_value('PARAMS', collections.defaultdict(), 'env')

    setup.logger = Component.get_logger()

    # return {'parallel_read_safe': True}

directives.register_directive('report', report_directive)

