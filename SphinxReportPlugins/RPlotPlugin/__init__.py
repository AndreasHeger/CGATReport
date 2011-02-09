from SphinxReport.Component import *
from SphinxReport import Config

import os, re

from rpy2.robjects import r as R
import rpy2.robjects as ro
import rpy2.robjects.numpy2ri

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
                 rst2rootdir, 
                 rst2builddir,
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

        try:
            maxid = max( R.dev_list().values() )
        except AttributeError:
            return map_figure2text

        for figid in range( 2, maxid+1 ):

            for id, format, dpi in all_formats:

                R.dev_set( figid )

                outname = "%s_%02d" % (template_name, figid)

                outpath = os.path.join(outdir, '%s.%s' % (outname, format))

                if format.endswith( "png" ):
                    R.dev_copy( device = R.png,
                                filename = outpath,
                                res = dpi )
                    R.dev_off()

                elif format.endswith( "svg" ):
                    R.dev_copy( device = R.svg,
                                filename = outpath )
                    R.dev_off()

                elif format.endswith( "eps" ):
                    R.dev_copy( device = R.postscript,
                                file = outpath,
                                onefile = True )
                    R.dev_off()
                else:
                    raise ValueError( "format '%s' not supported" % format )

                if not os.path.exists( outpath ):
                    raise ValueError( "file %s could not be created" )

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

            R.dev_off(figid)

            # create the text element
            rst_output = ""
            # for image diretive - image path is relative from rst file to external build dir
            imagepath = re.sub( "\\\\", "/", os.path.join( rst2builddir, outname ) )
            # for links - path is from rst file to internal root dir
            relative_imagepath = re.sub( "\\\\", "/", os.path.join( rst2rootdir, outname ) )

            linked_text = relative_imagepath + ".txt"

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
                    extra_images.append( "`%(id)s <%(relative_imagepath)s.%(format)s>`__" % locals())
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

            map_figure2text[ "#$rpl %i$#" % figid] = rst_output

        return map_figure2text

