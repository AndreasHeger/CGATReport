"""A special directive for including a matplotlib plot.

Given a path to a .py file, it includes the source code inline, then:

- On HTML, will include a .png with a link to a high-res .png.

- On LaTeX, will include a .pdf

This directive supports all of the options of the `image` directive,
except for `target` (since plot will add its own target).

"""

import sys, os, glob, shutil, imp, warnings, cStringIO
import hashlib, re, logging, math, types, operator
import traceback

from docutils.parsers.rst import directives

from SphinxReport import Config, Dispatcher, Utils, Cache
from SphinxReport.ResultBlock import ResultBlock, ResultBlocks
from SphinxReport.Component import *

SPHINXREPORT_DEBUG = False

TEMPLATE_TEXT = """
.. htmlonly::

   [`source code <%(linked_codename)s>`__]

"""

def out_of_date(original, derived):
    """
    Returns True if derivative is out-of-date wrt original,
    both of which are full file paths.
    """
    return (not os.path.exists(derived) \
        or os.stat(derived).st_mtime < os.stat(original).st_mtime)

def exception_to_str(s = None):

    sh = cStringIO.StringIO()
    if s is not None: print >>sh, s
    traceback.print_exc(file=sh)
    return sh.getvalue()


def run(arguments, 
        options, 
        lineno, 
        content, 
        state_machine = None, 
        document = None,
        srcdir = None,
        builddir = None ):
    """process :report: directive.

    *srdir* - top level directory of rst documents
    *builddir* - build directory
    """

    tag = "%s:%i" % (str(document), lineno)

    logging.debug( "report_directive.run: profile: started: rst: %s" % tag )

    # sort out the paths
    # reference is used for time-stamping
    reference = directives.uri(arguments[0])

    basedir, fname, basename, ext, outdir, codename = Utils.buildPaths( reference )

    # get the directory of the rst file
    rstdir, rstfile = os.path.split( document ) # state_machine.document.attributes['source'])

    # root of document tree
    if not srcdir:
        srcdir = setup.srcdir

    # build directory 
    if not builddir:
        builddir = setup.confdir
    
    # remove symbolic links
    srcdir, builddir, rstdir = [ os.path.realpath(x) for x in (srcdir, builddir, rstdir) ]

    # there are three directories:
    # builddir = directory where document is built in (usually _build/html or similar)
    # rstdir   = directory where rst sources are located
    # srcdir   = directory from which the build process is started

    # path to root relative to rst
    rst2srcdir = os.path.join( os.path.relpath( srcdir, start = rstdir ), outdir )

    # path to root relative to rst
    rst2builddir = os.path.join( os.path.relpath( builddir, start = rstdir ), outdir )

    # path relative to source (for images)
    root2builddir = os.path.join( os.path.relpath( builddir, start = srcdir ), outdir )

    logging.debug( "report_directive.run: arguments=%s, options=%s, lineno=%s, content=%s, document=%s" % (str(arguments),
                                                                                                           str(options),
                                                                                                           str(lineno),
                                                                                                           str(content),
                                                                                                           str(document)))

    logging.debug( "report_directive.run: plotdir=%s, basename=%s, ext=%s, fname=%s, rstdir=%s, srcdir=%s, builddir=%s" %\
                       (reference, basename, ext, fname, rstdir, srcdir, builddir ) )
    logging.debug( "report_directive.run: reference=%s, basedir=%s, rst2src=%s, root2build=%s, outdir=%s, codename=%s" %\
                   (reference, basedir, rst2srcdir, rst2builddir, outdir, codename))

    # try to create. If several processes try to create it,
    # testing with `if` will not work.
    try:
        os.makedirs(outdir)
    except OSError, msg:
        pass

    if not os.path.exists(outdir): 
        raise OSError( "could not create directory %s: %s" % (outdir, msg ))

    ########################################################
    # collect options
    # replace placedholders
    try:
        options = Utils.updateOptions( options )
    except ValueError, msg:
        logging.warn( "failure while updating options: %s" % msg )

    logging.debug( "report_directive.run: options=%s" % (str(options),) )

    transformer_names = []
    renderer_name = None

    # get layout option
    layout = options.get( "layout", "column" )

    option_map = getOptionMap()
    renderer_options = Utils.selectAndDeleteOptions( options, option_map["render"])
    transformer_options = Utils.selectAndDeleteOptions( options, option_map["transform"])
    dispatcher_options = Utils.selectAndDeleteOptions( options, option_map["dispatch"] )
    tracker_options = Utils.selectAndDeleteOptions( options, option_map["tracker"] )
    display_options = Utils.selectAndDeleteOptions( options, option_map["display"] )

    logging.debug( "report_directive.run: renderer options: %s" % str(renderer_options) )
    logging.debug( "report_directive.run: transformer options: %s" % str(transformer_options) )
    logging.debug( "report_directive.run: dispatcher options: %s" % str(dispatcher_options) )
    logging.debug( "report_directive.run: tracker options: %s" % str(tracker_options) )
    logging.debug( "report_directive.run: display options: %s" % str(display_options) )

    if display_options.has_key("transform"): 
        transformer_names = display_options["transform"].split(",")
        del display_options["transform"]

    if display_options.has_key("render"): 
        renderer_name = display_options["render"]
        del display_options["render"]

    ########################################################        
    # check for missing files
    if renderer_name != None:
        
        options_hash = hashlib.md5( str(renderer_options) +\
                                        str(transformer_options) +\
                                        str(dispatcher_options) +\
                                        str(tracker_options) +\
                                        str(transformer_names) ).hexdigest()

        template_name = Utils.quote_filename( \
            Config.SEPARATOR.join( (reference, renderer_name, options_hash ) ))
        filename_text = os.path.join( outdir, "%s.txt" % (template_name))

        logging.debug( "report_directive.run: options_hash=%s" %  options_hash)

        ###########################################################
        # check for existing files
        # update strategy does not use file stamps, but checks
        # for presence/absence of text element and if all figures
        # mentioned in the text element are present
        ###########################################################
        queries = [ re.compile( "%s(%s\S+.%s)" % ( root2builddir, outdir, suffix ) ) for suffix in ("png", "pdf") ]

        logging.debug( "report_directive.run: checking for changed files." )

        # check if text element exists
        if os.path.exists( filename_text ):

            lines = [ x[:-1] for x in open( filename_text, "r").readlines() ]
            filenames = []

            # check if all figures are present
            for line in lines:
                for query in queries:
                    x = query.search( line )
                    if x: filenames.extend( list( x.groups()) )

            logging.debug( "report_directive.run: %s: checking for %s" % (tag, str(filenames)))
            for filename in filenames:
                if not os.path.exists( filename ):
                    logging.info( "report_directive.run: %s: redo: %s missing" % (tag, filename ))
                    break
            else:
                logging.info( "report_directive.run: %s: noredo: all files are present" % tag )
                ## all is present - save text and return
                if lines and state_machine:
                    state_machine.insert_input(
                        lines, state_machine.input_lines.source(0) )
                return []
        else:
            logging.debug( "report_directive.run: %s: no check performed: %s missing" % (tag, str(filename_text)))
    else:
        template_name = ""
        filename_text = None
      
    ##########################################################
    # Initialize collectors
    collectors = []
    for collector in getPlugins( "collect" ).values():
        collectors.append( collector() )

    ##########################################################
    ## instantiate tracker, dispatcher, renderer and transformers
    ## and collect output
    ###########################################################
    try:
        ########################################################
        # find the tracker
        logging.debug( "report_directive.run: collecting tracker %s with options %s " % (reference, tracker_options) )
        code, tracker = Utils.makeTracker( reference, (), tracker_options )
        if not tracker: 
            logging.error( "report_directive.run: no tracker - no output from %s " % str(document) )
            raise ValueError( "tracker `%s` not found" % reference )

        logging.debug( "report_directive.run: collected tracker %s" % reference )

        tracker_id = Cache.tracker2key( tracker )

        ########################################################
        # determine the transformer
        logging.debug( "report_directive.run: creating transformers" )

        transformers = Utils.getTransformers( transformer_names, transformer_options )

        ########################################################
        # determine the renderer
        logging.debug( "report_directive.run: creating renderer." )
        
        if renderer_name == None:
            logging.error( "report_directive.run: no renderer - no output from %s" % str(document))
            raise ValueError("the report directive requires a renderer")

        renderer = Utils.getRenderer( renderer_name, renderer_options )

        ########################################################
        # create and call dispatcher
        logging.debug( "report_directive.run: creating dispatcher" )

        dispatcher = Dispatcher.Dispatcher( tracker, 
                                            renderer,
                                            transformers )

        # add the tracker options
        dispatcher_options.update( tracker_options )
        blocks = dispatcher( **dispatcher_options )

        if blocks == None:
            blocks = ResultBlocks(ResultBlocks( 
                    Utils.buildWarning( "NoData", "tracker %s returned no Data" % str(tracker)) ))
            code = None
            tracker_id = None
            
    except:

        logging.warn("report_directive.run: exception caught at %s:%i - see document" % (str(document), lineno) )

        blocks = ResultBlocks(ResultBlocks( Utils.buildException( "invocation" ) ))
        code = None
        tracker_id = None


    logging.debug( "report_directive.run: profile: started: collecting: %s" % tag )

    ########################################################
    ## write code output
    linked_codename = re.sub( "\\\\", "/", os.path.join( rst2srcdir, codename ))
    if code and basedir != outdir:
        outfile = open( os.path.join(outdir, codename ), "w" )
        for line in code: outfile.write( line )
        outfile.close()

    ###########################################################
    # collect images
    ###########################################################
    map_figure2text = {}
    for collector in collectors:
        map_figure2text.update( collector.collect( blocks,
                                                   template_name, 
                                                   outdir, 
                                                   rstdir,
                                                   builddir,
                                                   srcdir,
                                                   content, 
                                                   display_options,
                                                   linked_codename,
                                                   tracker_id ) )
        
    ###########################################################
    # replace place holders or add text
    ###########################################################
    ## add default for text-only output
    map_figure2text["default-prefix"] = TEMPLATE_TEXT % locals()
    map_figure2text["default-suffix"] = ""

    blocks.updatePlaceholders( map_figure2text )
    
    ###########################################################
    ## render the output taking into account the layout
    lines = Utils.layoutBlocks( blocks, layout )

    ###########################################################
    # add caption
    lines.extend( ['::', ''])
    if content:
        lines.extend( [ '    %s' % row.strip() for row in content] )
        lines.append( "" )

    lines.append( "" )

    # output rst text for this renderer
    if filename_text:
        outfile = open( filename_text, "w" )
        outfile.write("\n".join(lines) )
        outfile.close()

    if SPHINXREPORT_DEBUG:
        for x, l in enumerate( lines): print "%5i %s" % (x, l)

    if len(lines) and state_machine:
        state_machine.insert_input(
            lines, state_machine.input_lines.source(0))

    logging.debug( "report_directive.run: profile: finished: collecting: %s" % tag )
    logging.debug( "report_directive.run: profile: finished: rst: %s:%i" % (str(document), lineno) )

    return []

#try:
#    from docutils.parsers.rst import Directive
# except ImportError:
#     from docutils.parsers.rst.directives import _directives

#     def report_directive(name, 
#                          arguments, 
#                          options, 
#                          content, lineno,
#                          content_offset, 
#                          block_text, 
#                          state, 
#                          state_machine):
#         return run(arguments, options, lineno, content, state_machine )

#     report_directive.__doc__ = __doc__
#     report_directive.arguments = (1, 0, 1)
#     report_directive.options = dict( Config.RENDER_OPTIONS.items() +\
#                                          # Config.TRANSFORM_OPTIONS.items() +\
#                                          Config.DISPLAY_OPTIONS.items() +\
#                                          Config.DISPATCHER_OPTIONS.items() )

#     _directives['report'] = report_directive
# else:

from docutils.parsers.rst import Directive

class report_directive(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = True
    final_argument_whitespace = True

    # build option spec
    option_spec = getOptionSpec()

    def run(self):
        document = self.state.document.current_source
        logging.info( "report_directive: starting: %s:%i" % (str(document), self.lineno) )

        return run(self.arguments, 
                   self.options,
                   self.lineno,
                   self.content, 
                   self.state_machine, 
                   document )

# directives.register_directive('report', report_directive)

def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir
    setup.srcdir = app.srcdir
    app.add_directive('report', report_directive)

directives.register_directive('report', report_directive)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream = open( LOGFILE, "a" ) )

