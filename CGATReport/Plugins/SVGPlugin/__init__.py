import os
from CGATReport.Plugins.Collector import Collector
from CGATReport import Utils


class SVGPlugin(Collector):

    def __init__(self, *args, **kwargs):
        Collector.__init__(self, *args, **kwargs)

    def collect(self, blocks, figure_key="", subfig=0):
        '''collect svg output from result blocks.

        SVG output is written to a file and an image will be inserted
        at the place holder.
        '''
        map_figure2text = {}
        extension = "svg"
        rst_text = '''.. figure:: /{absfn}
'''
        for block in blocks:
            if not hasattr(block, "svg"):
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
            with open(outputpath, "w") as outf:
                outf.write(block.svg)

            # use absolute path
            absfn = os.path.abspath(outputpath)
            map_figure2text["#$svg %s$#" % block.title] = rst_text.format(
                absfn=absfn)

        return map_figure2text
