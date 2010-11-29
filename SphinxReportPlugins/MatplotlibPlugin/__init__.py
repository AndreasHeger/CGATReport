from SphinxReport.Component import *
from SphinxReport import Config

import os, re

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as image
from matplotlib import _pylab_helpers

class MatplotlibPlugin(Component):

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Component.__init__(self,*args,**kwargs)
    
        plt.close('all')    
        # matplotlib.rcdefaults()
        # set a figure size that doesn't overflow typical browser windows
        matplotlib.rcParams['figure.figsize'] = (5.5, 4.5)

    def collect( self, 
                 blocks,
                 template_name, 
                 outdir, 
                 relative_linkdir, 
                 root_linkdir,
                 content,
                 display_options,
                 linked_codename,
                 tracker_id):
        '''collect one or more matplotlib figures and 
        
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
            imagepath = re.sub( "\\\\", "/", os.path.join( relative_linkdir, outname ) )
            print "rel_link=", relative_linkdir, outname
            print "imagepath=", imagepath

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

