import os
import re
from CGATReport.Component import *
from CGATReport import Config


class XLSPlugin(Component):

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
        '''collect xls output from result blocks.

        xls output is written to a file and a link will be inserted at
        the place holder.
        '''
        map_figure2text = {}
        extension = "xlsx"
        for xblocks in blocks:
            for block in xblocks:
                if not hasattr(block, "xls"):
                    continue
                    
                outname = "%s_%s" % (template_name, re.sub("/", "@", block.title))
                outputpath = os.path.join(outdir, '%s.%s' %
                                          (outname, extension))

                # save to file
                block.xls.save(outputpath)

                # use absolute path
                link = os.path.abspath(outputpath)

                rst_output = "%(link)s" % locals()
                map_figure2text["#$xls %s$#" % block.title] = rst_output

        return map_figure2text
