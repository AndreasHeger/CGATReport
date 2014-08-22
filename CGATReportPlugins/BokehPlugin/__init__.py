import os
import re
from CGATReport.Component import *
from CGATReport import Config


class BokehPlugin(Component):
    '''collect bokeh plot objects and write
    javascript snippets to be included
    raw into html.
    '''

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)

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
        '''collect rst output from result blocks.

        '''

        map_figure2text = {}

        figid = 10

        for xblocks in blocks:
            for block in xblocks:
                if not hasattr(block, "bokeh"):
                    continue
                figid = block.bokeh._id
                # make sure to add the '/' at the end
                script = block.bokeh.create_html_snippet(
                    server=False,
                    embed_base_url='_static/report_directive/',
                    embed_save_loc=outdir,
                    static_path='_static/')

                text = """.. raw:: html

   <div><p>
         %s
   </p></div>
""" % script

                map_figure2text["#$bkh %s$#" % figid] = text
        return map_figure2text
