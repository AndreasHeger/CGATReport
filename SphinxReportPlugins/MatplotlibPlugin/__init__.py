import os
import warnings

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers

from SphinxReport.Component import Component
from SphinxReport import Utils

try:
    import mpld3
    HAS_MPLD3 = True
except ImportError:
    HAS_MPLD3 = False


class MatplotlibPlugin(Component):

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)

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
                links={}):
        '''collect one or more matplotlib figures and

        1. save as png, hires-png and pdf
        2. save thumbnail
        3. insert rendering code at placeholders in output

        returns a map of place holder to placeholder text.
        '''
        fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()

        map_figure2text = {}

        # determine the image formats to create
        default_format, additional_formats = Utils.getImageFormats(
            display_options)
        all_formats = [default_format, ] + additional_formats

        # create all required images
        for figman in fig_managers:

            # create all images
            figid = figman.num
            outname = "%s_%02d" % (template_name, figid)

            for id, format, dpi in all_formats:

                outpath = os.path.join(outdir, '%s.%s' % (outname, format))

                try:
                    figman.canvas.figure.savefig(outpath, dpi=dpi)
                except:
                    s = Utils.collectExceptionAsString(
                        "Exception running plot %s" % outpath)
                    warnings.warn(s)
                    return []

            is_html = False
            if HAS_MPLD3:
                outpath = os.path.join(
                    outdir,
                    '%s.html' % (outname))

                # select the correct figure
                figure = plt.figure(figid)
                # plt.legend()
                # write to file
                with open(outpath, "w") as outf:
                    outf.write(mpld3.fig_to_html(figure))
                is_html = True

            # create the text element
            rst_output = Utils.buildRstWithImage(
                outname,
                outdir,
                rstdir,
                builddir,
                srcdir,
                additional_formats,
                tracker_id,
                links,
                display_options,
                default_format,
                is_html=is_html)

            map_figure2text["#$mpl %i$#" % figid] = rst_output

        return map_figure2text
