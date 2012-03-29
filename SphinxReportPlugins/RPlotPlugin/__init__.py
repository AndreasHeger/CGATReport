from SphinxReport.Component import *
from SphinxReport import Config, Utils

import os, re

from rpy2.robjects import r as R
import rpy2.robjects as ro
import rpy2.robjects.numpy2ri
import rpy2.rinterface

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
                 linked_codename,
                 tracker_id):
        '''collect one or more R figures from all active devices
        and
        
        1. save as png, hires-png and pdf
        2. save thumbnail
        3. insert rendering code at placeholders in output

        returns a map of place holder to placeholder text.
        '''

        # path to build directory from rst directory
        rst2builddir = os.path.join( os.path.relpath( builddir, start = rstdir ), outdir )

        # path to src directory from rst directory
        rst2srcdir = os.path.join( os.path.relpath( srcdir, start = rstdir ), outdir )
        
        map_figure2text = {}

        # determine the image formats to create
        default_format, additional_formats = Utils.getImageFormats( display_options )
        all_formats = [default_format,] + additional_formats
        image_options = Utils.getImageOptions( display_options )

        urls = Utils.asList( Utils.PARAMS["report_urls"] )

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
            rst_output = ""
            # for image diretive - image path is relative from rst file to external build dir
            imagepath = re.sub( "\\\\", "/", os.path.join( rst2builddir, outname ) )
            # for links - path is from rst file to internal root dir
            relative_imagepath = re.sub( "\\\\", "/", os.path.join( rst2srcdir, outname ) )

            linked_text = relative_imagepath + ".txt"

            if Config.HTML_IMAGE_FORMAT:
                id, format, dpi = Config.HTML_IMAGE_FORMAT
                template = '''
.. htmlonly::

   .. image:: %(linked_image)s
%(image_options)s

   [%(code_url)s %(rst_url)s %(data_url)s  %(extra_images)s]
'''

                linked_image = imagepath + ".%s" % format

                extra_images=[]
                for id, format, dpi in additional_formats:
                    extra_images.append( "`%(id)s <%(relative_imagepath)s.%(format)s>`__" % locals())
                if extra_images: extra_images = " " + " ".join( extra_images)
                else: extra_images = ""

                # construct additional urls
                code_url, data_url, rst_url = "", "", ""
                if "code" in urls:
                    code_url = "`code <%(linked_codename)s>`__" % locals()

                if "data" in urls:
                    data_url = "`data </data/%(tracker_id)s>`__" % locals()

                if "rst" in urls:
                    rst_url = "`rst <%(linked_text)s>`__" % locals()

                rst_output += template % locals()

            # treat latex separately
            if Config.LATEX_IMAGE_FORMAT:
                id, format, dpi = Config.LATEX_IMAGE_FORMAT
                template = '''
.. latexonly::

   .. image:: %(linked_image)s
%(image_options)s
'''
                linked_image = imagepath + ".%s" % format
                rst_output += template % locals()

            map_figure2text[ "#$rpl %i$#" % figid] = rst_output

        return map_figure2text

