from SphinxReport.Component import *
from SphinxReport import Config, Utils

import os, re

try:
    from rpy2.robjects import r as R
    import rpy2.robjects as ro
    import rpy2.robjects.numpy2ri
    import rpy2.rinterface
except ImportError:
    R = None

import matplotlib.image as image

import warnings

class RPlotPlugin(Component):

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Component.__init__(self,*args,**kwargs)
    
    def collect( self, 
                 blocks,
                 template_name, 
                 outdir, 
                 rstdir,
                 builddir,
                 srcdir,
                 content,
                 display_options,
                 tracker_id,
                 links = {}):
        '''collect one or more R figures from all active devices
        and
        
        1. save as png, hires-png and pdf
        2. save thumbnail
        3. insert rendering code at placeholders in output

        returns a map of place holder to placeholder text.
        '''
        
        # disable plotting if no rpy installed
        if R == None: return {}

        map_figure2text = {}

        # determine the image formats to create
        default_format, additional_formats = Utils.getImageFormats( display_options )
        all_formats = [default_format,] + additional_formats
        image_options = Utils.getImageOptions( display_options )

        devices = R["dev.list"]()
        try:
            maxid = max( R["dev.list"]() )
        except TypeError:
            return map_figure2text
        
        for figid in range( 2, maxid+1 ):

            for id, format, dpi in all_formats:

                R["dev.set"]( figid )

                outname = "%s_%02d" % (template_name, figid)

                outpath = os.path.join(outdir, '%s.%s' % (outname, format))

                if format.endswith( "png" ):
                    # for busy images there is a problem with figure margins
                    # simply increase dpi until it works.
                    R["dev.set"]( figid )

                    width = height = 480 * dpi / 80
                    x = 0
                    while 1:
                        try: 
                            R["dev.copy"]( device = R.png,
                                           filename = outpath,
                                           res = dpi,
                                           width = width, 
                                           height = height )
                            R["dev.off"]()
                        except rpy2.rinterface.RRuntimeError:
                            width *= 2
                            height *= 2
                            if x < 5:
                                continue
                        break

                elif format.endswith( "svg" ):
                    R["dev.copy"]( device = R.svg,
                                   filename = outpath )
                    R["dev.off"]()

                elif format.endswith( "eps" ):
                    R["dev.copy"]( device = R.postscript,
                                   paper = 'special',
                                   width = 6,
                                   height = 6,
                                   file = outpath,
                                   onefile = True )
                    R["dev.off"]()
                elif format.endswith( "pdf" ):
                    R["dev.copy"]( device = R.pdf,
                                   paper = 'special',
                                   width = 6,
                                   height = 6,
                                   file = outpath,
                                   onefile = True )
                    R["dev.off"]()
                else:
                    raise ValueError( "format '%s' not supported" % format )

                if not os.path.exists( outpath ):
                    continue
                    # raise ValueError( "rendering problem: image file was not be created: %s" % outpath )

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

            R["dev.off"](figid)

            # create the text element
            rst_output = Utils.buildRstWithImage( outname,
                                                  outdir,
                                                  rstdir,
                                                  builddir,
                                                  srcdir,
                                                  additional_formats,
                                                  tracker_id, 
                                                  links,
                                                  display_options )

            map_figure2text[ "#$rpl %i$#" % figid] = rst_output

        return map_figure2text

