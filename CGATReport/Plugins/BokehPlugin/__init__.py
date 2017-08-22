import os
from CGATReport.Component import Component
from CGATReport.Utils import indent

try:
    import bokeh.embed
    import bokeh.plotting
    HAS_BOKEH = True
except ImportError:
    HAS_BOKEH = False


class BokehPlugin(Component):
    '''collect bokeh plot objects and write
    javascript snippets to be included
    raw into html.
    '''

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)

    def collect(self,
                blocks, figure_key="", subfig=0):
        '''collect rst output from result blocks.

        '''

        map_figure2text = {}

        if not HAS_BOKEH:
            return map_figure2text

        figid = 10

        for block in blocks:
            if not hasattr(block, "bokeh"):
                continue

            figid = block.bokeh._id
            res = bokeh.resources.CDN
            script_path = os.path.join(
                '_static/report_directive/', "%s.js" % figid)

            js_txt, script_txt = bokeh.embed.autoload_static(
                block.bokeh, res, script_path)

            # make sure to add the '/' at the end
            # script = block.bokeh.create_html_snippet(
            #     server=False,
            #     embed_base_url='_static/report_directive/',
            #     embed_save_loc=outdir,
            #     static_path='_static/')

            with open(script_path, "w") as outf:
                outf.write(js_txt)

            text = """.. raw:: html

   <div><p>
{}
   </p></div>
""".format(indent(script_txt, 8))

            map_figure2text["#$bkh %s$#" % figid] = text
        return map_figure2text
