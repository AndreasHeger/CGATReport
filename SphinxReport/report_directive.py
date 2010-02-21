"""A special directive for including a matplotlib plot.

Given a path to a .py file, it includes the source code inline, then:

- On HTML, will include a .png with a link to a high-res .png.

- On LaTeX, will include a .pdf

This directive supports all of the options of the `image` directive,
except for `target` (since plot will add its own target).

Additionally, if the :include-source: option is provided, the literal
source will be included inline, as well as a link to the source.
"""

import sys, os, glob, shutil, imp, warnings, cStringIO, hashlib, re, logging, math, types
import traceback

from docutils.parsers.rst import directives

from SphinxReport import Config, Renderer, Tracker, Transformer, Dispatcher, Utils, Cache
from SphinxReport.ResultBlock import ResultBlock, ResultBlocks
from SphinxReport.Reporter import *

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

def collectImagesFromMatplotlib( template_name, 
                                 outdir, 
                                 linkdir, 
                                 content,
                                 display_options,
                                 linked_codename,
                                 tracker_id):
    ''' collect one or more pylab figures and 
        
    1. save as png, hires-png and pdf
    2. save thumbnail
    3. insert rendering code at placeholders in output

    returns a map of place holder to placeholder text.
    '''
    fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()

    map_figure2text = {}

    # determine the image formats to create
    default_format = Config.HTML_IMAGE_FORMAT
    additional_formats = []

    try:
        additional_formats.extend( sphinxreport_images )
    except NameError:
        additional_formats.extend( Config.ADDITIONAL_FORMATS )

    if Config.LATEX_IMAGE_FORMAT: additional_formats.append( Config.LATEX_IMAGE_FORMAT )

    all_formats = [default_format,] + additional_formats

    # create all the images
    for i, figman in enumerate(fig_managers):
        # create all images

        for id, format, dpi in all_formats:

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
                try:
                    os.makedirs(thumbdir)
                except OSError:
                    pass
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

        # create the text element
        rst_output = ""
        imagepath = re.sub( "\\\\", "/", os.path.join( linkdir, outname ) )
        linked_text = imagepath + ".txt"

        if Config.HTML_IMAGE_FORMAT:
            id, format, dpi = Config.HTML_IMAGE_FORMAT
            template = '''
.. htmlonly::

   .. image:: %(linked_image)s
%(display_options)s

   [%(code_url)s %(rst_url)s %(data_url)s  %(extra_images)s]
'''
            
            linked_image = imagepath + ".%s" % format
            extra_images=[]
            for id, format, dpi in additional_formats:
                extra_images.append( "`%(id)s <%(imagepath)s.%(format)s>`__" % locals())
            if extra_images: extra_images = " " + " ".join( extra_images)
            else: extra_images = ""

            # construct additional urls
            code_url, data_url, rst_url = "", "", ""
            if "code" in sphinxreport_urls:
                code_url = "`code <%(linked_codename)s>`__" % locals()

            if "data" in sphinxreport_urls: 
                data_url = "`data </data/%(tracker_id)s>`__" % locals()
                
            if "rst" in sphinxreport_urls:
                rst_url = "`rst <%(linked_text)s>`__" % locals()

            rst_output += template % locals()
            
        # treat latex separately
        if Config.LATEX_IMAGE_FORMAT:
            id, format, dpi = Config.LATEX_IMAGE_FORMAT
            template = '''
.. latexonly::

   .. image:: %(linked_image)s
%(display_options)s
'''
            linked_image = imagepath + ".%s" % format
            rst_output += template % locals()
        
        map_figure2text[ "#$mpl %i$#" % i] = rst_output

    return map_figure2text

def collectHTML( result_blocks,
                 template_name, 
                 outdir, 
                 linkdir, 
                 content,
                 display_options,
                 linked_codename,
                 tracker_id):
    '''collect html output from result blocks.

    HTML output is written to a file and a link will be inserted at
    the place holder.
    '''
    map_figure2text = {}
    extension = "html"
    
    for blocks in result_blocks:
        for block in blocks:
            if not hasattr( block, "html" ): continue
            
            outname = "%s_%s" % (template_name, block.title)
            outputpath = os.path.join(outdir, '%s.%s' % (outname, extension))

            # save to file
            outf = open( outputpath, "w")
            outf.write( block.html )
            outf.close()

            path = re.sub( "\\\\", "/", os.path.join( linkdir, outname ) )
            link = path + "." + extension

            rst_output = "%(link)s" % locals()

            map_figure2text[ "#$html %s$#" % block.title] = rst_output

    return map_figure2text

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
    codename = Utils.quote_filename(reference) + ".code"

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

    # get layout option
    try: 
        layout = options["layout"]
        del options["layout"]
    except KeyError: 
        layout = "column"
    
    render_options = selectAndDeleteOptions( options, Config.RENDER_OPTIONS )
    transform_options = selectAndDeleteOptions( options, Config.TRANSFORM_OPTIONS)
    dispatcher_options = selectAndDeleteOptions( options, Config.DISPATCHER_OPTIONS)

    logging.debug( "renderer options: %s" % str(render_options) )
    logging.debug( "transformer options: %s" % str(transform_options) )
    logging.debug( "dispatcher options: %s" % str(dispatcher_options) )

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
        
        options_hash = hashlib.md5( str(render_options) +\
                                        str(transform_options) +\
                                        str(dispatcher_options) +\
                                        str(transformer_names) ).hexdigest()

        template_name = Utils.quote_filename( \
            Config.SEPARATOR.join( (reference, renderer_name, options_hash ) ))
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
            logging.debug( "no check performed: %s missing" % str(filename_text))
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
        logging.debug( "collecting tracker %s." % reference )
        code, tracker = Utils.getTracker( reference )
        if not tracker: 
            logging.debug( "no tracker - no output from %s " % str(document) )
            raise ValueError( "tracker `%s` not found" % reference )

        logging.debug( "collected tracker." )

        tracker_id = Cache.tracker2key( tracker )

        ########################################################
        # determine the transformer
        transformers = []
        logging.debug( "creating transformers." )

        for transformer in transformer_names:
            if transformer not in Config.MAP_TRANSFORMER: 
                raise KeyError('unknown transformer `%s`' % transformer )
            else: transformers.append( Config.MAP_TRANSFORMER[transformer](**transform_options)) 

        ########################################################
        # determine the renderer
        logging.debug( "creating renderer." )
        if renderer_name == None:
            raise ValueError("the report directive requires a renderer.")

        if renderer_name not in Config.MAP_RENDERER:
            raise KeyError("unknown renderer `%s`" % renderer_name)

        renderer = Config.MAP_RENDERER[renderer_name]

        ########################################################
        # create and call dispatcher
        logging.debug( "creating dispatcher" )

        dispatcher = Dispatcher.Dispatcher( tracker, 
                                            renderer(tracker, **render_options), 
                                            transformers )     
        blocks = dispatcher( **dispatcher_options )

    except:

        logging.warn("exception caught at %s:%i - see document" % (str(document), lineno) )

        blocks = Renderer.buildException( "invocation" )
        code = None
        tracker_id = None

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
                                                   linked_codename,
                                                   tracker_id )

    ###########################################################
    # collect text
    ###########################################################
    map_figure2text.update( collectHTML(  blocks,
                                          template_name, 
                                          outdir, 
                                          linkdir, 
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

    logging.debug( "finished report_directive.run: %s:%i" % (str(document), lineno) )

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
    report_directive.options = dict( Config.RENDER_OPTIONS.items() +\
                                         Config.TRANSFORM_OPTIONS.items() +\
                                         Config.DISPLAY_OPTIONS.items() +\
                                         Config.DISPATCHER_OPTIONS.items() )

    _directives['report'] = report_directive
else:
    class report_directive(Directive):
        required_arguments = 1
        optional_arguments = 0
        has_content = True
        final_argument_whitespace = True
        option_spec = dict( Config.RENDER_OPTIONS.items() +\
                                Config.TRANSFORM_OPTIONS.items() +\
                                Config.DISPLAY_OPTIONS.items() +\
                                Config.DISPATCHER_OPTIONS.items() )
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
    app.add_config_value('sphinxreport_show_warnings', True, False)

report_directive.__doc__ = __doc__

directives.register_directive('report', report_directive)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    stream = open( LOGFILE, "a" ) )

