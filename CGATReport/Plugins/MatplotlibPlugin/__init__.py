import os
import warnings

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers

from CGATReport import Utils
from CGATReport.Plugins.Collector import Collector


class MatplotlibPlugin(Collector):

    def __init__(self, *args, **kwargs):
        Collector.__init__(self, *args, **kwargs)

        plt.close('all')
        # matplotlib.rcdefaults()
        # set a figure size that doesn't overflow typical browser windows
        matplotlib.rcParams['figure.figsize'] = (5.5, 4.5)

    def collect(self, blocks, figure_key=None, subfig=0):
        '''collect one or more matplotlib figures and

        1. save as png, hires-png and pdf
        2. save thumbnail
        3. insert rendering code at placeholders in output

        returns a map of place holder to placeholder text.
        '''
        fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()

        self.debug("figure_key: {}, subfig: {}: collecting {} matplotlib images".format(
            figure_key, subfig, len(fig_managers)))

        map_figure2text = {}

        # determine the image formats to create
        default_format, additional_formats = Utils.getImageFormats(
            self.display_options)
        all_formats = [default_format, ] + additional_formats

        # create all required images
        for figman in fig_managers:

            # create all images
            figid = figman.num

            # select the correct figure
            figure = plt.figure(figid)

            # save explicit formats
            outname = "%s_%s_%02d_%02d" % (self.template_name, figure_key, subfig, figid)

            has_output = False

            for id, format, dpi in all_formats:

                outpath = os.path.join(self.outdir, '%s.%s' % (outname, format))

                # sanitize figure size for Agg.
                if figure.get_figwidth() > 32768 or figure.get_figheight() > 32768:
                    warnings.warn(
                        "figure size unexpected large {} x {}, "
                        "patching to 10x10 inches".format(
                            figure.get_figwidth(), figure.get_figheight()))
                    figure.set_size_inches(10, 10)

                try:
                    figman.canvas.figure.savefig(outpath, dpi=dpi)
                except Exception as ex:
                    s = Utils.collectExceptionAsString(
                        "exception raised while building plot '%s': %s" %
                        (outpath, str(ex)))
                    warnings.warn(s)
                    continue
                has_output = True

            if not has_output:
                warnings.warn("no output for '%s'" % outpath)
                continue

            # insert display figure
            is_html = False
            script_text = None

            # release memory
            plt.close(figure)

            # create the text element
            rst_output = Utils.buildRstWithImage(
                outname,
                self.outdir,
                self.rstdir,
                self.builddir,
                self.srcdir,
                additional_formats,
                self.tracker_id,
                self.links,
                self.display_options,
                default_format,
                is_html=is_html,
                text=script_text)

            if figure_key is None:
                f = figid
            else:
                f = "{}.{}".format(figure_key, figid)
            map_figure2text["#$mpl {}$#".format(f)] = rst_output

        return map_figure2text
