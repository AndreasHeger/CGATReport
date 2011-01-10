"""A special directive for including a matplotlib plot.

Given a path to a .py file, it includes the source code inline, then:

- On HTML, will include a .png with a link to a high-res .png.

- On LaTeX, will include a .pdf

This directive supports all of the options of the `image` directive,
except for `target` (since plot will add its own target).

Additionally, if the :include-source: option is provided, the literal
source will be included inline, as well as a link to the source.
"""

import sys, os, glob, shutil, imp, warnings, cStringIO
import hashlib, re, logging, math, types, operator
import traceback

from docutils.parsers.rst import directives

from SphinxReport import Config, Dispatcher, Utils, Cache
from SphinxReport.ResultBlock import ResultBlock, ResultBlocks
from SphinxReport.Component import *

SPHINXREPORT_DEBUG = False

# This does not work:
# matplotlib.use('Agg', warn = False)
# Matplotlib might be imported beforehand? plt.switch_backend did not
# change the backend. The only option I found was to change my own matplotlibrc.

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as image
from matplotlib import _pylab_helpers

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


def layoutBlocks( blocks, layout = "column"):
    """layout blocks of rst text.

    layout can be one of "column", "row", or "grid".

    The layout uses an rst table to arrange elements.
    """

    lines = []
    if len(blocks) == 0: return lines

    # flatten blocks
    x = ResultBlocks()
    for b in blocks:
        if b.title: b.updateTitle( b.title, "prefix" )
        x.extend( b )
    blocks = x

    if layout == "column":
        for block in blocks: 
            if block.title:
                lines.extend( block.title.split("\n") )
                lines.append( "" )
            else:
                logging.warn( "report_directive.layoutBlocks: missing title" )

            lines.extend(block.text.split("\n"))
        lines.extend( [ "", ] )
        return lines
    elif layout in ("row", "grid"):
        if layout == "row": ncols = len(blocks)
        elif layout == "grid": ncols = int(math.ceil(math.sqrt( len(blocks) )))
    elif layout.startswith("column"):
        ncols = min( len(blocks), int(layout.split("-")[1]))
    else:
        raise ValueError( "unknown layout %s " % layout )

    # compute column widths
    widths = [ x.getWidth() for x in blocks ]
    text_heights = [ x.getTextHeight() for x in blocks ]
    title_heights = [ x.getTitleHeight() for x in blocks ]

    columnwidths = []
    for x in range(ncols):
        columnwidths.append( max( [widths[y] for y in range( x, len(blocks), ncols ) ] ) )

    separator = "+%s+" % "+".join( ["-" * x for x in columnwidths ] )

    ## add empty blocks
    if len(blocks) % ncols:
        blocks.extend( [ ResultBlock( "", "" )]  * (ncols - len(blocks) % ncols) )

    for nblock in range(0, len(blocks), ncols ):

        ## add text
        lines.append( separator )
        max_height = max( text_heights[nblock:nblock+ncols] )
        new_blocks = ResultBlocks()
        
        for xx in range(nblock, min(nblock+ncols,len(blocks))):
            txt, col = blocks[xx].text.split("\n"), xx % ncols

            max_width = columnwidths[col]

            # add missig lines 
            txt.extend( [""] * (max_height - len(txt)) )
            # extend lines
            txt = [ x + " " * (max_width - len(x)) for x in txt ]

            new_blocks.append( txt )

        for l in zip( *new_blocks ):
            lines.append( "|%s|" % "|".join( l ) )

        ## add subtitles
        max_height = max( title_heights[nblock:nblock+ncols] )

        if max_height > 0:

            new_blocks = ResultBlocks()
            lines.append( separator )

            for xx in range(nblock, min(nblock+ncols,len(blocks))):
                
                txt, col = blocks[xx].title.split("\n"), xx % ncols

                max_width = columnwidths[col]
                # add missig lines 
                txt.extend( [""] * (max_height - len(txt) ) )
                # extend lines
                txt = [ x + " " * (max_width - len(x)) for x in txt ]

                new_blocks.append( txt )

            for l in zip( *new_blocks ):
                lines.append( "|%s|" % "|".join( l ) )
            
    lines.append( separator )
    lines.append( "" )
    return lines

def selectAndDeleteOptions( options, select ):
    '''collect options in select.'''
    new_options = {}
    for k, v in options.items():
        if k in select:
            new_options[k] = v
            del options[k]
    return new_options

def buildPaths( reference ):
    '''return paths.'''

    basedir, fname = os.path.split(reference)
    basename, ext = os.path.splitext(fname)
    outdir = os.path.join('_static', 'report_directive', basedir)
    codename = Utils.quote_filename(reference) + ".code"

    return basedir, fname, basename, ext, outdir, codename

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

    logging.debug( "report_directive.run: profile: started: rst: %s:%i" % (str(document), lineno) )

    # sort out the paths
    # reference is used for time-stamping
    reference = directives.uri(arguments[0])

    basedir, fname, basename, ext, outdir, codename = buildPaths( reference )

    # get the directory of the rst file
    rstdir, rstfile = os.path.split( document ) # state_machine.document.attributes['source'])

    # root of document tree
    if not srcdir:
        srcdir = setup.srcdir

    # build directory 
    if not builddir:
        builddir = setup.confdir
    
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
    logging.debug( "report_directive.run: reference=%s, basedir=%s, rst2root=%s, root2build=%s, outdir=%s, codename=%s" %\
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
    options = Utils.updateOptions( options )
    transformer_names = []
    renderer_name = None

    # get layout option
    layout = options.get( "layout", "column" )

    option_map = getOptionMap()
    renderer_options = selectAndDeleteOptions( options, option_map["render"])
    transformer_options = selectAndDeleteOptions( options, option_map["transform"])
    dispatcher_options = selectAndDeleteOptions( options, option_map["dispatch"] )
        
    logging.debug( "report_directive.run: renderer options: %s" % str(renderer_options) )
    logging.debug( "report_directive.run: transformer options: %s" % str(transformer_options) )
    logging.debug( "report_directive.run: dispatcher options: %s" % str(dispatcher_options) )

    if options.has_key("transform"): 
        transformer_names = options["transform"].split(",")
        del options["transform"]

    if options.has_key("render"): 
        renderer_name = options["render"]
        del options["render"]

    ########################################################
    # add sphinx options for image display
    if options.items:
        display_options = "\n".join( \
            ['      :%s: %s' % (key, val) for key, val in options.items()] )
    else:
        display_options = ''

    ########################################################        
    # check for missing files
    if renderer_name != None:
        
        options_hash = hashlib.md5( str(renderer_options) +\
                                        str(transformer_options) +\
                                        str(dispatcher_options) +\
                                        str(transformer_names) ).hexdigest()

        template_name = Utils.quote_filename( \
            Config.SEPARATOR.join( (reference, renderer_name, options_hash ) ))
        filename_text = os.path.join( outdir, "%s.txt" % (template_name))

        logging.debug( "report_directive.run: options_hash=%s" %  options_hash)

        ###########################################################
        # check for existing files
        # update strategy does not use file stamps, but checks
        # for presence/absence of text element and if all figures
        # mentioned it the text element are present
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

            logging.debug( "report_directive.run: checking for %s" % str(filenames))
            for filename in filenames:
                if not os.path.exists( filename ):
                    logging.info( "report_directive.run: redo: %s missing" % filename )
                    break
            else:
                logging.info( "no redo: all files are present" )
                ## all is present - save text and return
                if lines and state_machine:
                    state_machine.insert_input(
                        lines, state_machine.input_lines.source(0) )
                return []
        else:
            logging.debug( "report_directive.run: no check performed: %s missing" % str(filename_text))
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
        logging.debug( "report_directive.run: collecting tracker %s." % reference )
        code, tracker = Utils.makeTracker( reference )
        if not tracker: 
            logging.debug( "report_directive.run: no tracker - no output from %s " % str(document) )
            raise ValueError( "tracker `%s` not found" % reference )

        logging.debug( "report_directive.run: collected tracker." )

        tracker_id = Cache.tracker2key( tracker )

        ########################################################
        # determine the transformer
        logging.debug( "report_directive.run: creating transformers." )

        transformers = Utils.getTransformers( transformer_names, **transformer_options )

        ########################################################
        # determine the renderer
        logging.debug( "report_directive.run: creating renderer." )
        
        if renderer_name == None:
            raise ValueError("the report directive requires a renderer.")

        renderer = Utils.getRenderer( renderer_name, **renderer_options )

        ########################################################
        # create and call dispatcher
        logging.debug( "report_directive.run: creating dispatcher" )

        dispatcher = Dispatcher.Dispatcher( tracker, 
                                            renderer,
                                            transformers )     
        blocks = dispatcher( **dispatcher_options )

    except:

        logging.warn("report_directive.run: exception caught at %s:%i - see document" % (str(document), lineno) )

        blocks = Utils.buildException( "invocation" )
        code = None
        tracker_id = None

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
                                                   rst2srcdir,
                                                   rst2builddir,
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
    lines = layoutBlocks( blocks, layout )

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

report_directive.__doc__ = __doc__

# directives.register_directive('report', report_directive)

def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir
    setup.srcdir = app.srcdir
    app.add_config_value('sphinxreport_show_warnings', True, False)
    app.add_directive('report', report_directive)

report_directive.__doc__ = __doc__

directives.register_directive('report', report_directive)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream = open( LOGFILE, "a" ) )

