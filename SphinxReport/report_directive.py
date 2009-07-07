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
import matplotlib

DEBUG = False
FORCE = False

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
    tracker =  getattr( module, cls)()
    return code, tracker

FORMATS = [('png', 80),
           ('hires.png', 200),
           ('pdf', 50),
           ]

MAP_RENDERER= { 'stats': Renderer.RendererStats,
                'pairwise-stats': Renderer.RendererPairwiseStats,
                'pairwise-stats-matrix-plot': Renderer.RendererPairwiseStatsMatrixPlot,
                'pairwise-stats-bar-plot': Renderer.RendererPairwiseStatsBarPlot,
                'pairwise-stats-plot': Renderer.RendererPairwiseStatsMatrixPlot,
                'histogram': Renderer.RendererHistogram,
                'scatter-plot': Renderer.RendererScatterPlot,
                'scatter-rainbow-plot': Renderer.RendererScatterPlotWithColor,
                'table': Renderer.RendererTable,
                'grouped-table': Renderer.RendererGroupedTable,
                'matrix': Renderer.RendererMatrix,
                'matrix-plot': Renderer.RendererMatrixPlot,
                'stacked-bars': Renderer.RendererStackedBars,
                'interleaved-bars': Renderer.RendererInterleavedBars,
                'bars': Renderer.RendererInterleavedBars,
                'histogram-plot': Renderer.RendererHistogramPlot,
                'multihistogram-plot': Renderer.RendererMultiHistogramPlot,
                'box-plot': Renderer.RendererBoxPlot }

DISPLAY_OPTIONS = {'alt': directives.unchanged,
                  'height': directives.length_or_unitless,
                  'width': directives.length_or_percentage_or_unitless,
                  'scale': directives.nonnegative_int,
                  'align': align,
                  'class': directives.class_option,
                  'render' : directives.unchanged,
                  'include-source': directives.flag }

RENDER_OPTIONS = { 'cumulative': directives.flag,
                   'reverse-cumulative': directives.flag,
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
                   'transform-matrix' : directives.unchanged,
                   'plot-value' : directives.unchanged,
                   'tracks': directives.unchanged,
                   'slices': directives.unchanged,
                   'as-lines': directives.flag,  
                   'mpl-figure' : directives.unchanged,
                   'mpl-legend' : directives.unchanged,
                   'mpl-subplot' : directives.unchanged,
                   'mpl-rc' : directives.unchanged,
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

   [`source code <%(linkdir)s/%(basename)s.py>`__]

Exception occurred rendering plot.

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

def collectImagesFromMatplotlib( blocks, template_name, outdir, linkdir, content,
                                 display_options,
                                 linked_codename ):
    """collect one or more pylab figures and 
        save as png, hires-png and pdf
        save thumbnail
        insert rendering code at placeholders in output

    returns True if images have been collected.
    """
    fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()
    if len(fig_managers) == 0: return None

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

        ## replace placeholders in blocks to be output
        new_blocks = []
        for txt in blocks:
            new_blocks.append( re.sub( "(## Figure %i ##)" % (i+1), 
                                       TEMPLATE_PLOT % locals(),
                                       txt))
        blocks = new_blocks
        ## if not found?
        # output.append( TEMPLATE_PLOT % locals() )

    return blocks

def layoutBlocks( blocks, layout = "column"):
    """layout blocks of rst text.

    layout can be one of "column", "row", or "grid".

    The layout uses an rst table.
    """

    lines = []
    if len(blocks) == 0: return lines

    if layout == "column":
        for block in blocks: 
            lines.extend(block.split("\n"))
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
    widths = [ max( [len(x) for x in y.split("\n")] )for y in blocks ]
    heights = [ len(y.split("\n")) for y in blocks ]
    columnwidths = []
    for x in range(ncols):
        columnwidths.append( max( [widths[y] for y in range( x, len(blocks), ncols ) ] ) )

    separator = "+%s+" % "+".join( ["-" * x for x in columnwidths ] )

    ## add empty blocks
    if len(blocks) % ncols:
        blocks = list(blocks)
        blocks.extend( [""] * (ncols - len(blocks) % ncols) )

    for x in range(0, len(blocks), ncols ):
        lines.append( separator )
        max_height = max( heights[x:x+ncols] )
        new_blocks = []
        
        for xx in range(x, min(x+ncols,len(blocks))):
            block, col = blocks[xx].split("\n"), xx % ncols

            max_width = widths[col]
            # add missig lins 
            block.extend( [""] * (max_height - len(block)) )
            # extend lines
            block = [ x + " " * (max_width - len(x)) for x in block ]

            new_blocks.append( block )

        for l in zip( *new_blocks ):
            lines.append( "|%s|" % "|".join( l ) )
            
    lines.append( separator )
    lines.append( "" )
    return lines

            
def run(arguments, options, lineno, content, state_machine = None, document = None):
    """process :report: directive."""

    logging.debug( "started report_directive.run: %s:%i" % (str(document), lineno) )

    # sort out the paths
    # reference is used for time-stamping
    reference = directives.uri(arguments[0])
    basedir, fname = os.path.split(reference)
    basename, ext = os.path.splitext(fname)

    # get the directory of the rst file
    rstdir, rstfile = os.path.split( document ) # state_machine.document.attributes['source'])
    # reldir = rstdir[len(setup.confdir)+1:]
    reldir = rstdir[len(os.path.abspath( os.getcwd() ))+1:]
    relparts = [p for p in os.path.split(reldir) if p.strip()]
    nparts = len(relparts)
    outdir = os.path.join('_static', 'report_directive', basedir)
    linkdir = ('../' * (nparts)) + outdir

    if DEBUG:
        print "arguments=", arguments
        print "options=", options
        print "lineno", lineno
        print "content=", content
        print "document=", document
        print 'plotdir=', reference, "basename=", basename, "ext=", ext, "fname=", fname
        print 'rstdir=%s, reldir=%s, relparts=%s, nparts=%d'%(rstdir, reldir, relparts, nparts)
        print 'reference="%s", basedir="%s", linkdir="%s", outdir="%s"'%(reference, basedir, linkdir, outdir)

    # try to create. If several processes try to create it,
    # testing with `if` will not work.
    try:
        os.makedirs(outdir)
    except OSError, msg:
        pass

    if not os.path.exists(outdir): 
        raise OSError( "could not create directory %s: %s" % (outdir, msg ))

    # check if we need to update. 
    logging.debug( "collecting tracker." )
    code, tracker = getTracker( reference )
    logging.debug( "collected tracker." )

    codename = quoted(fname) + ".code"
    linked_codename = re.sub( "\\\\", "/", os.path.join( linkdir, codename )) 
    if basedir != outdir:
        outfile = open( os.path.join(outdir, codename ), "w" )
        for line in code: outfile.write( line )
        outfile.close()

    logging.debug( "invocating renderer." )

    ########################################################
    # collect options
    #
    # determine the renderer
    renderer_name = "stats"
    if options.has_key("render"): 
        renderer_name = options["render"]
        del options["render"]

    try:
        renderer = MAP_RENDERER[ renderer_name ]( tracker )
    except KeyError:
        raise KeyError("unknown renderer %s" % renderer_name)

    # determine layout
    try: layout = options["layout"]
    except KeyError: layout = "column"

    # collect options for renderer and remove others
    render_options = {}
    for k, v in options.items():
        if k in RENDER_OPTIONS: render_options[k] = v

    for k in RENDER_OPTIONS.keys():
        try: del options[k]
        except KeyError: pass

    # add sphinx options for image display
    display_options = "\n".join( ['      :%s: %s' % (key, val) for key, val in
                                  options.items()] )

    options_hash = hashlib.md5( str(render_options) ).hexdigest()

    template_name = quoted( SEPARATOR.join( (reference, renderer_name, options_hash ) ))
    filename_text = os.path.join( outdir, "%s.txt" % (template_name))

    if DEBUG:
        print "options_hash=", options_hash

    ###########################################################
    # check for existing files
    # update strategy does not use file stamps, but checks
    # for presence/absence of text element and if all figures
    # mentioned it the text element are present
    ###########################################################
    queries = [ re.compile( "%s(%s.+.%s)" % ("\.\./" * nparts, outdir,suffix ) ) for suffix in ("png", "pdf") ]

    logging.debug( "checking for changed files." )
    
    # check if text element exists
    if not FORCE and os.path.exists( filename_text ):
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

    ###########################################################
    # collect output
    ###########################################################

    # we need to clear between runs
    plt.close('all')    
    # matplotlib.rcdefaults()
    # set a figure size that doesn't overflow typical browser windows
    matplotlib.rcParams['figure.figsize'] = (5.5, 4.5)
        
    lines = []
    input_blocks = renderer( **render_options )
    ###########################################################
    # collect images
    ###########################################################
    output_blocks = collectImagesFromMatplotlib( input_blocks, 
                                                 template_name, 
                                                 outdir, 
                                                 linkdir, 
                                                 content, 
                                                 display_options,
                                                 linked_codename)

    if not output_blocks:
        # process text
        output_blocks = []
        for block in input_blocks:
            output_blocks.append( TEMPLATE_TEXT % locals() + block )

    ###########################################################
    ## render the output taking into account the layout
    lines = layoutBlocks( output_blocks, layout )

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
    outfile = open( filename_text, "w" )
    outfile.write("\n".join(lines) )
    outfile.close()

    if DEBUG: 
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
    report_directive.options = RENDER_OPTIONS.copy()
    report_directive.options.update( DISPLAY_OPTIONS.copy() )

    _directives['report'] = report_directive
else:
    class report_directive(Directive):
        required_arguments = 1
        optional_arguments = 0
        has_content = True
        final_argument_whitespace = True
        option_spec = RENDER_OPTIONS.copy()
        option_spec.update( DISPLAY_OPTIONS )
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

