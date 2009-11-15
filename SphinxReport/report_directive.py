"""A special directive for including a matplotlib plot.

Given a path to a .py file, it includes the source code inline, then:

- On HTML, will include a .png with a link to a high-res .png.

- On LaTeX, will include a .pdf

This directive supports all of the options of the `image` directive,
except for `target` (since plot will add its own target).

Additionally, if the :include-source: option is provided, the literal
source will be included inline, as well as a link to the source.
"""

import sys, os, glob, shutil, imp, warnings, cStringIO, hashlib, re, logging, math
import traceback

from docutils.parsers.rst import directives
try:
    # docutils 0.4
    from docutils.parsers.rst.directives.images import align
except ImportError:
    # docutils 0.5
    from docutils.parsers.rst.directives.images import Image
    align = Image.align

import Renderer
import Transformer
import Dispatcher
import matplotlib
from ResultBlock import ResultBlock, ResultBlocks

SPHINXREPORT_DEBUG = False

SEPARATOR="@"

# This does not work:
# matplotlib.use('Agg', warn = False)
# Matplotlib might be imported beforehand? plt.switch_backend did not
# change the backend. The only option I found was to change my own matplotlibrc.

import matplotlib.pyplot as plt
import matplotlib.image as image
from matplotlib import _pylab_helpers

class memoized(object):
   """Decorator that caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned, and
   not re-evaluated.
   """
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      try:
         return self.cache[args]
      except KeyError:
         self.cache[args] = value = self.func(*args)
         return value
      except TypeError:
         # uncachable -- for instance, passing a list as an argument.
         # Better to not cache than to blow up entirely.
         return self.func(*args)
   def __repr__(self):
      """Return the function's docstring."""
      return self.func.__doc__

@memoized
def getModule( name ):
    """load module in fullpath
    """
    # remove leading '.'
    logging.debug( "getModule %s" % name )
    (file, pathname, description) = imp.find_module( name )
    stdout = sys.stdout
    sys.stdout = cStringIO.StringIO()
    try:
        module = imp.load_module(name, file, pathname, description )
    except:
        raise
    finally:
        file.close()
        sys.stdout = stdout

    return module, pathname

@memoized
def getTracker( fullpath ):
    """retrieve an instantiated tracker and its associated code.
    
    returns a tuple (code, tracker).
    """
    name, cls = os.path.splitext(fullpath)
    # remove leading '.'
    cls = cls[1:]

    module, pathname = getModule( name )

    # extract code
    code = []
    infile = open( pathname, "r")
    for line in infile:
        x = re.search( "(\s*)class\s+%s" % cls, line ) 
        if x:
            indent = len( x.groups()[0] )
            code.append( line )
            break
    for line in infile:
        if len( re.match( "^(\s*)", line).groups()[0] ) <= indent: break
        code.append(line)
    infile.close()

    logging.debug( "instantiating tracker %s" % cls )
    try:
        tracker =  getattr( module, cls)()
    except AttributeError, msg:
        logging.critical( "instantiating tracker %s.%s failed: %s" % (module, cls, msg))
        raise

    return code, tracker

FORMATS = [ ('png', 80),
            ('hires.png', 200),
#            ('pdf', 50),
            ]

MAP_TRANSFORMER = { 
    'stats' : Transformer.TransformerStats, 
    'correlation' : Transformer.TransformerCorrelation, 
    'histogram' : Transformer.TransformerHistogram,
    'filter' : Transformer.TransformerFilter,
    'select' : Transformer.TransformerSelect,
    }

MAP_RENDERER= { 
    'line-plot': Renderer.RendererLinePlot,
    'pie-plot': Renderer.RendererPiePlot,
    'scatter-plot': Renderer.RendererScatterPlot,
    'scatter-rainbow-plot': Renderer.RendererScatterPlotWithColor,
    'table': Renderer.RendererTable,
    'matrix': Renderer.RendererMatrix,
    'matrix-plot': Renderer.RendererMatrixPlot,
    'hinton-plot': Renderer.RendererHintonPlot,
    'bar-plot': Renderer.RendererBarPlot,
    'stacked-bar-plot': Renderer.RendererStackedBarPlot,
    'interleaved-bar-plot': Renderer.RendererInterleavedBarPlot,
    'box-plot': Renderer.RendererBoxPlot,
    'glossary' : Renderer.RendererGlossary 
}

DISPLAY_OPTIONS = {'alt': directives.unchanged,
                  'height': directives.length_or_unitless,
                  'width': directives.length_or_percentage_or_unitless,
                  'scale': directives.nonnegative_int,
                  'align': align,
                  'class': directives.class_option,
                  'render' : directives.unchanged,
                  'transform' : directives.unchanged,
                  'include-source': directives.flag }

RENDER_OPTIONS = { 'cumulative': directives.flag,
                   'reverse-cumulative': directives.flag,
                   'error' : directives.unchanged,
                   'label' : directives.unchanged,
                   'normalized-max': directives.flag,
                   'normalized-total': directives.flag,
                   'groupby' : directives.unchanged,
                   'layout' : directives.unchanged,
                   'bins' : directives.unchanged,
                   'logscale' : directives.unchanged,
                   'title' : directives.unchanged,
                   'xtitle' : directives.unchanged,
                   'ytitle' : directives.unchanged,
                   'range' : directives.unchanged,
                   'add-total': directives.flag,
                   'xrange' : directives.unchanged,
                   'yrange' : directives.unchanged,
                   'zrange' : directives.unchanged,
                   'palette' : directives.unchanged,
                   'reverse-palette' : directives.flag,
                   'transpose' : directives.flag,
                   'transform-matrix' : directives.unchanged,
                   'plot-value' : directives.unchanged,
                   'tracks': directives.unchanged,
                   'slices': directives.unchanged,
                   'as-lines': directives.flag,  
                   'format' : directives.unchanged,
                   'colorbar-format' : directives.unchanged,
                   'filename' : directives.unchanged,
                   'pie-min-percentage' : directives.unchanged,
                   'max-rows' : directives.unchanged,
                   'max-cols' : directives.unchanged,
                   'mpl-figure' : directives.unchanged,
                   'mpl-legend' : directives.unchanged,
                   'mpl-subplot' : directives.unchanged,
                   'mpl-rc' : directives.unchanged, }

TRANSFORM_OPTIONS = {
    'tf-fields' : directives.unchanged,
    'tf-level' : directives.length_or_unitless,
    }

TEMPLATE_PLOT = """
.. htmlonly::

   .. image:: %(linkedname)s.png
%(display_options)s

   [`source code <%(linked_codename)s>`__,
   `rst <%(linkedname)s.txt>`__,
   `png <%(linkedname)s.hires.png>`__,
   `pdf <%(linkedname)s.pdf>`__]

.. latexonly::
   .. image:: %(linkedname)s.pdf
%(display_options)s
"""

TEMPLATE_TEXT = """
.. htmlonly::

   [`source code <%(linked_codename)s>`__]

"""

EXCEPTION_TEMPLATE = """
.. htmlonly::

   [`source code <%(linked_codename)s.py>`__]

.. warning::

   %%(title)s
"""


# latex does not permit a "." for image files - replace it with "-"
def quoted( fn ):
    return re.sub( "[.]", "-", fn )

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

def collectImagesFromMatplotlib( template_name, 
                                 outdir, 
                                 linkdir, 
                                 content,
                                 display_options,
                                 linked_codename ):
    ''' collect one or more pylab figures and 
        save as png, hires-png and pdf
        save thumbnail
        insert rendering code at placeholders in output

    returns a map of place holder to placeholder text.
    '''
    fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()

    map_figure2text = {}

    for i, figman in enumerate(fig_managers):
        for format, dpi in FORMATS:
            if len(fig_managers) == 1:
                outname = template_name
            else:
                outname = "%s_%02d" % (template_name, i)

            outpath = os.path.join(outdir, '%s.%s' % (outname, format))

            try:
                figman.canvas.figure.savefig( outpath, dpi=dpi )
            except:
                s = exception_to_str("Exception running plot %s" % outpath)
                warnings.warn(s)
                return []

            if format=='png':
                thumbdir = os.path.join(outdir, 'thumbnails')
                if not os.path.exists(thumbdir): os.makedirs(thumbdir)
                thumbfile = str('%s.png' % os.path.join(thumbdir, outname) )
                captionfile = str('%s.txt' % os.path.join(thumbdir, outname) )
                if not os.path.exists(thumbfile):
                    # thumbnail only available in matplotlib >= 0.98.4
                    try:
                        figthumb = image.thumbnail(str(outpath), str(thumbfile), scale=0.3)
                    except AttributeError:
                        pass
                outfile = open(captionfile,"w")
                outfile.write( "\n".join( content ) + "\n" )
                outfile.close()

        linkedname = re.sub( "\\\\", "/", os.path.join( linkdir, outname ) )

        map_figure2text[ "#$mpl %i$#" % i] = TEMPLATE_PLOT % locals()

    return map_figure2text

def layoutBlocks( blocks, layout = "column"):
    """layout blocks of rst text.

    layout can be one of "column", "row", or "grid".

    The layout uses an rst table.
    """

    lines = []
    if len(blocks) == 0: return lines

    # flatten blocks
    x = ResultBlocks()
    for i in blocks: 
        if i.title: i.updateTitle( i.title, "prefix" )
        x.extend( i )
    blocks = x

    if layout == "column":
        for block in blocks: 
            if block.title:
                lines.extend( block.title.split("\n") )
                lines.append( "" )
            else:
                logging.warn( "missing title" )

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
    codename = quoted(reference) + ".code"

    return basedir, fname, basename, ext, outdir, codename

def run(arguments, options, lineno, content, state_machine = None, document = None):
    """process :report: directive."""

    logging.debug( "started report_directive.run: %s:%i" % (str(document), lineno) )

    # sort out the paths
    # reference is used for time-stamping
    reference = directives.uri(arguments[0])

    basedir, fname, basename, ext, outdir, codename = buildPaths( reference )

    # get the directory of the rst file
    rstdir, rstfile = os.path.split( document ) # state_machine.document.attributes['source'])
    # reldir = rstdir[len(setup.confdir)+1:]
    reldir = rstdir[len(os.path.abspath( os.getcwd() ))+1:]
    relparts = [p for p in os.path.split(reldir) if p.strip()]
    nparts = len(relparts)

    linkdir = ('../' * (nparts)) + outdir

    logging.debug( "arguments=%s, options=%s, lineno=%s, content=%s, document=%s" % (str(arguments),
                                                                                     str(options),
                                                                                     str(lineno),
                                                                                     str(content),
                                                                                     str(document)))

    logging.debug( "plotdir=%s, basename=%s, ext=%s, fname=%s, rstdir=%s, reldir=%s, relparts=%s, nparts=%d" %\
                       (reference, basename, ext, fname, rstdir, reldir, relparts, nparts) )
    logging.debug( "reference=%s, basedir=%s, linkdir=%s, outdir=%s, codename=%s" % (reference, basedir, linkdir, outdir, codename))

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
    transformer_names = []
    renderer_name = None

    render_options = selectAndDeleteOptions( options, RENDER_OPTIONS )
    transform_options = selectAndDeleteOptions( options, TRANSFORM_OPTIONS)

    if options.has_key("transform"): 
        transformer_names = options["transform"].split(",")
        del options["transform"]

    if options.has_key("render"): 
        renderer_name = options["render"]
        del options["render"]

    # get layout option
    try: layout = options["layout"]
    except KeyError: layout = "column"

    ########################################################
    # add sphinx options for image display
    if options.items:
        display_options = "\n".join( ['      :%s: %s' % (key, val) for key, val in
                                      options.items()] )
    else:
        display_options = ""

    ########################################################        
    # check for missing files
    if renderer_name != None:
        options_hash = hashlib.md5( str(render_options) + str(transform_options) ).hexdigest()

        template_name = quoted( SEPARATOR.join( (reference, renderer_name, options_hash ) ))
        filename_text = os.path.join( outdir, "%s.txt" % (template_name))

        logging.debug( "options_hash=%s" %  options_hash)

        ###########################################################
        # check for existing files
        # update strategy does not use file stamps, but checks
        # for presence/absence of text element and if all figures
        # mentioned it the text element are present
        ###########################################################
        queries = [ re.compile( "%s(%s\S+.%s)" % ("\.\./" * nparts, outdir,suffix ) ) for suffix in ("png", "pdf") ]

        logging.debug( "checking for changed files." )

        # check if text element exists
        if os.path.exists( filename_text ):
            lines = [ x[:-1] for x in open( filename_text, "r").readlines() ]

            filenames = []

            # check if all figures are present
            for line in lines:
                for query in queries:
                    x = query.search( line )
                    if x: filenames.extend( list( x.groups()) )

            logging.debug( "checking for %s" % str(filenames))
            for filename in filenames:
                if not os.path.exists( filename ):
                    logging.info( "redo: %s missing" % filename )
                    break
            else:
                logging.info( "no redo: all files are present" )
                ## all is present - save text and return
                if lines and state_machine:
                    state_machine.insert_input(
                        lines, state_machine.input_lines.source(0) )
                return []
    else:
        template_name = ""
        filename_text = None

    # we need to clear between runs
    plt.close('all')    
    # matplotlib.rcdefaults()
    # set a figure size that doesn't overflow typical browser windows
    matplotlib.rcParams['figure.figsize'] = (5.5, 4.5)

    ##########################################################
    ## instantiate tracker, dispatcher, renderer and transformers
    ## and collect output
    ###########################################################
    try:
        ########################################################
        # find the tracker
        logging.debug( "collecting tracker." )
        code, tracker = getTracker( reference )
        if not tracker: 
            logging.debug( "no tracker - no output from %s " % str(document) )
            raise ValueError( "tracker `%s` not found" % reference )

        logging.debug( "collected tracker." )

        ########################################################
        # determine the transformer
        transformers = []
        logging.debug( "creating transformers." )

        for transformer in transformer_names:
            if transformer not in MAP_TRANSFORMER: 
                raise KeyError('unknown transformer `%s`' % transformer )
            else: transformers.append( MAP_TRANSFORMER[transformer](**transform_options)) 

        ########################################################
        # determine the renderer
        logging.debug( "creating renderer." )
        if renderer_name == None:
            raise ValueError("the report directive requires a renderer.")

        if renderer_name not in MAP_RENDERER:
            raise KeyError("unknown renderer `%s`" % renderer_name)

        renderer = MAP_RENDERER[renderer_name]

        logging.debug( "creating dispatcher" )
        dispatcher = Dispatcher.Dispatcher( tracker, renderer(tracker, **render_options), transformers )     
        blocks = dispatcher( **render_options )
    except:
        blocks = Renderer.buildException( "invocation" )
        code = None

    ########################################################
    ## write code output
    linked_codename = re.sub( "\\\\", "/", os.path.join( linkdir, codename )) 
    if code and basedir != outdir:
        outfile = open( os.path.join(outdir, codename ), "w" )
        for line in code: outfile.write( line )
        outfile.close()

    ###########################################################
    # collect images
    ###########################################################
    map_figure2text = collectImagesFromMatplotlib( template_name, 
                                                   outdir, 
                                                   linkdir, 
                                                   content, 
                                                   display_options,
                                                   linked_codename)

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

    #try:
    #    lines.extend( [ '    %s' % row.strip() for row in tracker.__doc__.split('\n')] )
    #except AttributeError:
    #    pass
    # lines.extend( [ '    renderer=%s' % row.strip() for row in renderer.getCaption().split('\n')] )
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

    return []

try:
    from docutils.parsers.rst import Directive
except ImportError:
    from docutils.parsers.rst.directives import _directives

    def report_directive(name, 
                         arguments, 
                         options, 
                         content, lineno,
                         content_offset, 
                         block_text, 
                         state, 
                         state_machine):
        return run(arguments, options, lineno, content, state_machine )

    report_directive.__doc__ = __doc__
    report_directive.arguments = (1, 0, 1)
    report_directive.options = dict( RENDER_OPTIONS.items() + TRANSFORM_OPTIONS.items() + DISPLAY_OPTIONS.items() )

    _directives['report'] = report_directive
else:
    class report_directive(Directive):
        required_arguments = 1
        optional_arguments = 0
        has_content = True
        final_argument_whitespace = True
        option_spec = dict( RENDER_OPTIONS.items() + TRANSFORM_OPTIONS.items() + DISPLAY_OPTIONS.items() )
        def run(self):
            document = self.state.document.current_source
            logging.info( "starting: %s:%i" % (str(document), self.lineno) )
            return run(self.arguments, 
                       self.options,
                       self.lineno,
                       self.content, 
                       self.state_machine, 
                       document)
    report_directive.__doc__ = __doc__

    directives.register_directive('report', report_directive)

def setup(app):
    setup.app = app
    setup.config = app.config
    setup.confdir = app.confdir

report_directive.__doc__ = __doc__

directives.register_directive('report', report_directive)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream = open( "sphinxreport.log", "a" ) )

