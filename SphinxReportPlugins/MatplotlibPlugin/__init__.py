import os
import re
import warnings

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.image as image
from matplotlib import _pylab_helpers
from matplotlib.cbook import exception_to_str
import seaborn

from SphinxReport.Component import *
from SphinxReport import Config, Utils

class MatplotlibPlugin(Component):

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Component.__init__(self,*args,**kwargs)

        plt.close('all')
        # matplotlib.rcdefaults()
        # set a figure size that doesn't overflow typical browser windows
        matplotlib.rcParams['figure.figsize'] = (5.5, 4.5)

    def collect(self,
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
        '''collect one or more matplotlib figures and

        1. save as png, hires-png and pdf
        2. save thumbnail
        3. insert rendering code at placeholders in output

        returns a map of place holder to placeholder text.
        '''
        fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()

        map_figure2text = {}

        # determine the image formats to create
        default_format, additional_formats = Utils.getImageFormats(display_options)
        all_formats = [default_format,] + additional_formats


        # create all the images
        for figman in fig_managers:

            # create all images
            figid = figman.num
            outname = "%s_%02d" % (template_name, figid)

            for id, format, dpi in all_formats:

                outpath = os.path.join(outdir, '%s.%s' % (outname, format))

                try:
                    figman.canvas.figure.savefig(outpath, dpi=dpi)
                except:
                    s = Utils.collectExceptionAsString("Exception running plot %s" % outpath)
                    warnings.warn(s)
                    return []

                # if format=='png':
                #     thumbdir = os.path.join(outdir, 'thumbnails')
                #     try:
                #         os.makedirs(thumbdir)
                #     except OSError:
                #         pass
                #     thumbfile = str('%s.png' % os.path.join(thumbdir, outname))
                #     captionfile = str('%s.txt' % os.path.join(thumbdir, outname))
                #     if not os.path.exists(thumbfile):
                #         # thumbnail only available in matplotlib >= 0.98.4
                #         try:
                #             figthumb = image.thumbnail(str(outpath), str(thumbfile), scale=0.3)
                #         except AttributeError:
                #             pass
                #     outfile = open(captionfile,"w")
                #     outfile.write("\n".join(content) + "\n")
                #     outfile.close()

            # create the text element
            rst_output = Utils.buildRstWithImage(outname,
                                                  outdir,
                                                  rstdir,
                                                  builddir,
                                                  srcdir,
                                                  additional_formats,
                                                  tracker_id,
                                                  links,
                                                  display_options,
                                                  default_format)

            map_figure2text[ "#$mpl %i$#" % figid] = rst_output

        return map_figure2text

