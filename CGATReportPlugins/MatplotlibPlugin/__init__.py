import os
import warnings

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers

from CGATReport.Component import Component
from CGATReport import Utils

try:
    import mpld3
    USE_MPLD3 = Utils.PARAMS.get('report_mpl', None) == 'mpld3'
except ImportError:
    USE_MPLD3 = False

try:
    import bokeh.plotting
    import bokeh.embed
    import bokeh.mpl
    import bokeh.mplexporter.exporter
    USE_BOKEH = Utils.PARAMS.get('report_mpl', None) == 'bokeh'
except ImportError:
    USE_BOKEH = False


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

            # select the correct figure
            figure = plt.figure(figid)

            # save explicit formats
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

            # insert display figure
            is_html = False
            script_text = None
            if USE_MPLD3:
                outpath = os.path.join(
                    outdir,
                    '%s.html' % (outname))

                # plt.legend()
                # write to file
                with open(outpath, "w") as outf:
                    outf.write(mpld3.fig_to_html(figure))
                is_html = True

            elif USE_BOKEH:
                outpath = os.path.join(
                    outdir,
                    '%s.html' % (outname))
                is_html = True

                # (try to) convert to bokeh figure
                try:
                    # pd_job - use pandas object
                    # xkcd - use xkcd style
                    renderer = bokeh.mpl.BokehRenderer(pd_obj=True,
                                                       xkcd=False)
                    exporter = bokeh.mplexporter.exporter.Exporter(renderer)
                    exporter.run(figure)
                    bpl = renderer.fig

                except NotImplementedError:
                    # fall back to matplotlib
                    is_html = False

                if is_html:
                    bokeh_id = bpl._id
                    res = bokeh.resources.CDN
                    script_path = os.path.join(
                        '_static/report_directive/',
                        "%s.js" % bokeh_id)

                    # get js figure and html snippet
                    js_text, script_text = bokeh.embed.autoload_static(
                        bpl, res, script_path)

                    with open(script_path, "w") as outf:
                        outf.write(js_text)

                    with open(outpath, "w") as outf:
                        outf.write(script_text)

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
                is_html=is_html,
                text=script_text)

            map_figure2text["#$mpl %i$#" % figid] = rst_output

        return map_figure2text
