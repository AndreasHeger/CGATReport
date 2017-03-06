import os
import re
from CGATReport.Plugins.Collector import Collector
from CGATReport import Config


class XLSPlugin(Collector):

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Collector.__init__(self, *args, **kwargs)

    def collect(self, blocks):
        '''collect xls output from result blocks.

        xls output is written to a file and a link will be inserted at
        the place holder.
        '''
        map_figure2text = {}
        extension = "xlsx"
        for block in blocks:
            if not hasattr(block, "xls"):
                continue

            outname = "%s_%s" % (
                self.template_name, re.sub("/", "@", block.title))
            outputpath = os.path.join(self.outdir, '%s.%s' %
                                      (outname, extension))

            # save to file
            block.xls.save(outputpath)

            # use absolute path
            link = os.path.abspath(outputpath)

            rst_output = "%(link)s" % locals()
            map_figure2text["#$xls %s$#" % block.title] = rst_output

        return map_figure2text
