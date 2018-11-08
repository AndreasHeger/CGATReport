import os
from CGATReport.Plugins.Collector import Collector
from CGATReport import Utils


class HTMLPlugin(Collector):

    def __init__(self, *args, **kwargs):
        Collector.__init__(self, *args, **kwargs)

    def collect(self, blocks, figure_key="", subfig=0):
        '''collect html output from result blocks.

        HTML output is written to a file and a link will be inserted at
        the place holder.
        '''
        map_figure2text = {}
        extension = "html"
        for block in blocks:
            if not hasattr(block, "html"):
                continue

            # remove special characters from filename. I think the docutils
            # system removes these from links which later causes problems
            # as the link does not point to the correct location of the
            # file.
            outname = Utils.quote_filename(
                "%s_%s" % (self.template_name, block.title))
            outputpath = os.path.join(
                self.outdir, '%s.%s' % (outname, extension))

            # save to file
            with open(outputpath, "w", encoding="utf-8") as outf:
                outf.write(block.html)

            # use absolute path
            link = os.path.abspath(outputpath)
            rst_output = ":download:`(link) </{}>`".format(link)
            map_figure2text["#$html %s$#" % block.title] = rst_output

        return map_figure2text
