import os
from CGATReport.Component import Component
from CGATReport import Utils


class HTMLPlugin(Component):

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
        '''collect html output from result blocks.

        HTML output is written to a file and a link will be inserted at
        the place holder.
        '''
        map_figure2text = {}
        extension = "html"

        for xblocks in blocks:
            for block in xblocks:
                if not hasattr(block, "html"):
                    continue

                # remove special characters from filename. I think the docutils
                # system removes these from links which later causes problems
                # as the link does not point to the correct location of the
                # file.
                outname = Utils.quote_filename(
                    "%s_%s" % (template_name, block.title))
                outputpath = os.path.join(
                    outdir, '%s.%s' % (outname, extension))

                # save to file
                outf = open(outputpath, "w")
                outf.write(block.html)
                outf.close()

                # use absolute path
                link = os.path.abspath(outputpath)

                rst_output = "%(link)s" % locals()
                map_figure2text["#$html %s$#" % block.title] = rst_output

        return map_figure2text
