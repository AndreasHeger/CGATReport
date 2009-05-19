"""A special directive for including a matplotlib plot.

Given a path to a .py file, it includes the source code inline, then:

- On HTML, will include a .png with a link to a high-res .png.

- On LaTeX, will include a .pdf

This directive supports all of the options of the `image` directive,
except for `target` (since plot will add its own target).

Additionally, if the :include-source: option is provided, the literal
source will be included inline, as well as a link to the source.
"""

import sys, os, glob, shutil, imp, warnings, cStringIO, hashlib, re, logging

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

# This does not work:
# matplotlib.use('Agg', warn = False)
# Matplotlib might be imported beforehand? plt.switch_backend did not
# change the backend. The only option I found was to change my own matplotlibrc.

import matplotlib.pyplot as plt
import matplotlib.image as image
from matplotlib import _pylab_helpers

def getTracker( fullpath ):
    """retrieve an instantiated tracker and its associated code.
    
    returns a tuple (code, tracker).
    """
    name, cls = os.path.splitext(fullpath)
    # remove leading '.'
    cls = cls[1:]
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
                   'as-lines': directives.flag
                   }

TEMPLATE_PLOT = """
.. htmlonly::

   [`source code <%(linkdir)s/%(codename)s>`__,
   `rst <%(linkdir)s/%(outname)s.txt>`__,
   `png <%(linkdir)s/%(outname)s.hires.png>`__,
   `pdf <%(linkdir)s/%(outname)s.pdf>`__]

   .. image:: %(linkdir)s/%(outname)s.png
%(display_options)s

.. latexonly::
   .. image:: %(linkdir)s/%(outname)s.pdf
%(display_options)s
"""

TEMPLATE_TEXT = """
.. htmlonly::

   [`source code <%(linkdir)s/%(codename)s>`__]

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

    sh = StringIO.StringIO()
    if s is not None: print >>sh, s
    traceback.print_exc(file=sh)
    return sh.getvalue()

def run(arguments, options, lineno, content, state_machine = None, document = None):

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


    if not os.path.exists(outdir): os.makedirs(outdir)

    # check if we need to update. 

    code, tracker = getTracker( reference )
    codename = quoted(fname) + ".code"
    if basedir != outdir:
        outfile = open( os.path.join(outdir, codename ), "w" )
        for line in code: outfile.write( line )
        outfile.close()

    # determine the renderer
    renderer_name = "stats"
    if options.has_key("render"): 
        renderer_name = options["render"]
        del options["render"]
    try:
        renderer = MAP_RENDERER[ renderer_name ]( tracker )
    except KeyError:
        raise KeyError("unknown renderer %s" % renderer_name)

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

    template_name = quoted( "@".join( (reference, renderer_name, options_hash ) ))
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

    ###########################################################
    # collect output
    ###########################################################

    # we need to clear between runs
    plt.close('all')    
    # matplotlib.rcdefaults()
    # set a figure size that doesn't overflow typical browser windows
    matplotlib.rcParams['figure.figsize'] = (5.5, 4.5)
        
    lines = []
    output = renderer( **render_options )

    ###########################################################
    # deal with one or more pylab figures
    #    save as png, hires-png and pdf
    #    save thumbnail
    #    insert rendering code at placeholders
    fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()

    if len(fig_managers) > 0:

        if output: 
            lines.extend( output )
            lines.append( "" )

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
                    return 0, module

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

            try:
                l = lines.index( "## Figure %i ##" % (i+1) )
                lines[l:l+1] = (TEMPLATE_PLOT % locals()).split('\n')
            except IndexError:
                lines.extend((TEMPLATE_PLOT % locals()).split('\n'))

    else:
        # process text
        lines.extend( (TEMPLATE_TEXT % locals()).split( "\n") )

        # add any text
        if output: 
            lines.extend( output )
            lines.append( "" )
        

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
        for x, l in enumerate( lines): print x, l

    if len(lines) and state_machine:
        state_machine.insert_input(
            lines, state_machine.input_lines.source(0))
    return []

try:
    from docutils.parsers.rst import Directive
except ImportError:
    from docutils.parsers.rst.directives import _directives

    def report_directive(name, arguments, options, content, lineno,
                       content_offset, block_text, state, state_machine):
        return run(arguments, options, lineno, content, state_machine )
    report_directive.__doc__ = __doc__
    report_directive.arguments = (1, 0, 1)
    report_directive.options = options

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
