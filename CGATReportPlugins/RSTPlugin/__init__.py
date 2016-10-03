import os
import re
from CGATReport.Component import Component


class RSTPlugin(Component):
    '''collect rst text.

    This plugin looks for image/figure directives in literal text
    output and changes absolute paths to relative paths so that they
    are valid within sphinx.

    images: path relative to rst directory

    links: path relative to html content

    '''

    capabilities = ['collect']

    # include white spaces at the end for length-neutral substitution
    # Pattern will also include a terminating '"'. This is used to
    # test if the context is a csv table, in which case no padding
    # should be done.
    rx_img = re.compile("\.\. (image|figure):: ([^ |+,:]+[ ]*)")

    # external link targets:
    # .. _link: target
    rx_link = re.compile("\.\. _([^ |+,:]+)\s*:\s*([^ |+,:]+)[ ]*")

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

        def replace_and_pad(s, old, new):
            '''replace old with new in s such that length of
            new+spaces is at least that of old+spaces.

            There needs to be enough space for padding. If there is not
            enough space, the new string will be truncated and an error
            issued.
            '''
            # do not pad in csv tables
            if not old.endswith('"'):
                oldlen = len(old)
                newlen = len(new)
                new = new + " " * (oldlen - newlen)

            if len(new) > len(old):
                self.warn("length of substitution string ({}) is "
                          "longer than original ({}):\n{}\n{}".format(
                        len(new), len(old),
                        new, old))
                new = new[:len(old)]

            n = s.replace(old, new)
            return n

        for xblocks in blocks:
            for block in xblocks:
                if not hasattr(block, "text"):
                    continue
                lines = block.text.split("\n")
                n = []
                for l in lines:
                    ll = l
                    for x in self.rx_img.finditer(ll):
                        directive, filename = x.groups()
                        relpath = os.path.relpath(
                            filename.strip(),
                            os.path.abspath(rstdir))
                        newpath = re.sub("\\\\", "/", relpath)
                        l = replace_and_pad(l, filename, newpath)

                    for x in self.rx_link.finditer(ll):
                        directive, filename = x.groups()
                        newpath = re.sub(
                            "\\\\", "/",
                            os.path.abspath(filename.strip()))
                        # pad with spaces to keep table alignment
                        l = replace_and_pad(l, filename, newpath)

                    n.append(l)
                block.text = "\n".join(n)

        return map_figure2text
