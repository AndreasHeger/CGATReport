import os
from CGATReport.Plugins.Collector import Collector
from CGATReport import Utils

try:
    import holoviews as hv
    from holoviews.plotting import mpl
    HAS_HOLOVIEW = True
except ImportError:
    HAS_HOLOVIEW = False


try:
    import bokeh.embed
    import bokeh.plotting
    HAS_BOKEH = True
except ImportError:
    HAS_BOKEH = False
    

class HoloviewsPlugin(Collector):

    engine = "bokeh"
    
    def __init__(self, *args, **kwargs):
        Collector.__init__(self, *args, **kwargs)

    def collect(self, blocks, figure_key="", subfig=0):
        '''collect holoview output.

        '''
        map_figure2text = {}
        extension = "svg"
        rst_text = '''.. figure:: /{absfn}
'''

        for block in blocks:
            if not hasattr(block, "hv"):
                continue

            if self.engine == "mpl":
                renderer = hv.Store.renderers['matplotlib'].instance(fig='svg')
                plot = renderer.get_plot(block.hv)
                rendered = renderer(plot, fmt="auto")
        
                (data, info) = rendered
            
                # remove special characters from filename. I think the docutils
                # system removes these from links which later causes problems
                # as the link does not point to the correct location of the
                # file.
                outname = Utils.quote_filename(
                    "%s_%s" % (self.template_name, block.title))
                outputpath = os.path.join(
                    self.outdir, '%s.%s' % (outname, extension))

                # save to file
                with open(outputpath, "w") as outf:
                    outf.write(data)

                # use absolute path
                absfn = os.path.abspath(outputpath)
                map_figure2text["#$hv %s$#" % block.title] = rst_text.format(
                    absfn=absfn)
            elif self.engine == "bokeh":
                renderer = hv.renderer("bokeh")
                html = renderer.static_html(block.hv)

                lines = [".. only:: html\n"] +\
                        ["   .. raw:: html\n"] +\
                        ["      " + x for x in html.splitlines()]

                lines = "\n".join(lines)
                
                map_figure2text["#$hv %s$#" % block.title] = lines

        return map_figure2text
