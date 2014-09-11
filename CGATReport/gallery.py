#!/bin/env python

# generate a thumbnail gallery of plots
# taken from the maptlotlib documentation
"""
cgatreport-gallery
--------------------

The:file:`cgatreport-gallery` utility examines the build directory for images
and constructs a gallery. It should be called from the:term:`source directory`.

   $ cgatreport-gallery

Calling:file:`cgatreport-gallery` is usually not necessary if:file:`cgatreport-build`
is used.
"""

import os
import glob
import re
import collections
import sys

template = """\
{%% extends "layout.html" %%}
{%% set title = "Thumbnail gallery" %%}
{%% block extrahead %%}
<link type="text/css" rel="stylesheet" href="_static/webtoolkit.contextmenu.css" />
<link type="text/css" rel="stylesheet" href="_static/contextmenu.css" />
<script type="text/javascript" src="_static/webtoolkit.contextmenu.js"></script>
<script type="text/javascript">
SimpleContextMenu.setup({'preventDefault':true, 'preventForms':false});
SimpleContextMenu.attach('container', 'CM1');
</script>
{%% endblock %%}

{%% block body %%}

<h3>Click on any image to see the source code</h3>
<br/>

%s
{%% endblock %%}
"""

"""
<div id="divContext" style="border: 1px solid blue; display: none; position: absolute">
<ul class="cmenu">
<li><a id="aContextNav" href="#">Navigate to</a></li>
<li><a id="aAddWebmark" href="#">Add to WebMark</a></li>
<li class="topSep">  <a id="aDisable" href="#">disable this menu</a>  </li>
</ul> </div>

<p><a id="aEnable" style="display:none" href="#">Enable context menus</a></p>
<ul>
<li><a href="http://luke.breuer.com">Author's Hompage</a></li>
<li><a href="http://luke.breuer.com/tutorial">Tutorials</a></li>
<li><a href="http://luke.breuer.com/webmark">WebMark</a></li>
</ul>
"""

multiimage = re.compile('(.*)_\d\d')
rootdir = '_static/report_directive'
dest = '_templates/gallery.html'

# create directory if not present
if not os.path.exists(os.path.dirname(dest)):
    os.makedirs(os.path.dirname(dest))

# number of columns in gallery
columns = 5

SEPARATOR = "@"

# images we want to skip for the gallery because they are an unusual
# size that doesn't layout well in a table, or because they may be
# redundant with other images or uninteresting
skips = set([
    'mathtext_examples',
    'matshow_02',
    'matshow_03',
    'matplotlib_icon',
])

# build map of images to html files
rx = re.compile("_images/(\S+).png")
map_image2file = collections.defaultdict(set)

basedir = '_build/html'


def main(argv=sys.argv):

    for root, dirs, files in os.walk(basedir):
        for f in files:
            if f.endswith(".html"):
                fn = os.path.join(root, f)
                infile = open(fn, "r")
                for l in infile:
                    x = rx.search(l)
                    if x:
                        map_image2file[x.groups()[0]].add(
                            fn[len(basedir) + 1:])

    data = []
    for subdir in ('',):
        thisdir = os.path.join(rootdir, subdir)
        if not os.path.exists(thisdir):
            print("no directory '%s' - no gallery created" % thisdir)
            return
        thumbdir = os.path.join(thisdir, 'thumbnails')
        if not os.path.exists(thumbdir):
            print("no thumbnail directory '%s' - no gallery created" %
                  thumbdir)
            return 0

        print("CGATReport: collecting thumbnails from %s" % thumbdir)

        # we search for pdfs here because there is one pdf for each
        # successful image build (2 pngs since one is high res) and the
        # mapping between py files and images is 1->many
        for captionfile in sorted(glob.glob(os.path.join(thisdir, '*.txt'))):
            basepath, filename = os.path.split(captionfile)
            basename, ext = os.path.splitext(filename)
            # print 'generating', subdir, basename

            if basename in skips:
                continue

            pdffile = os.path.join(thisdir, '%s.pdf' % basename)
            pngfile = os.path.join(thisdir, '%s.png' % basename)
            thumbfile = os.path.join(thumbdir, '%s.png' % basename)
            # captionfile = os.path.join(thumbdir, '%s.txt' % basename)
            if not os.path.exists(pngfile):
                pngfile = None
            if not os.path.exists(thumbfile):
                thumbfile = None

            try:
                datasource, renderer, options = basename.split(SEPARATOR)
            except ValueError:
                print("could not parse %s into three components" % basename)
                continue

            # print 'datasource=', datasource, "renderer=", renderer, "filename=",filename, "basename=",basename, "ext=",ext
            # print 'pngfile', pngfile, "thumbfile", thumbfile
            data.append(
                (datasource, subdir, thisdir, renderer, basename, pngfile, thumbfile, captionfile))
    link_template = """
    <td>
    <table>
    <tr>
    <td>
    <a href="%(png)s"><img title="%(caption)s" src="%(thumbfile)s" border="0" alt="%(basename)s"/></a>
    <td>
    </tr>
    <tr>
    <td>
    <a href="%(code)s">[src]</a>
    <a href="%(hires)s">[hires]</a>
    <a href="%(rst)s">[rst]</a>
    <a href="%(pdf)s">[pdf]</a>
    </td>
    </tr>
    """
    # sort data by datasource
    data.sort()

    rows = []

    print("CGATReport: creating %i thumbnails" % len(data))
    col = 0
    last_datasource = None
    for (datasource, subdir, thisdir, renderer, basename, pngfile, thumbfile, captionfile) in data:
        if datasource != last_datasource:
            if last_datasource:
                rows.append("</tr></table>")
            rows.append("<table><tr><th>%s</th></tr><tr>" % datasource)
        last_datasource = datasource

        if col > columns:
            rows.append("</tr><tr>")
            col = 0

        if thumbfile is not None:
            code = os.path.join(thisdir, datasource) + ".code"
            rst = os.path.join(thisdir, basename) + ".txt"
            png = os.path.join(thisdir, basename) + ".png"
            hires = os.path.join(thisdir, basename) + ".hires.png"
            pdf = os.path.join(thisdir, basename) + ".pdf"

            if os.path.exists(captionfile):
                caption = "".join(open(captionfile, "r").readlines())
            else:
                caption = "no caption"

            rows.append(link_template % locals())

            b = re.sub(SEPARATOR, "&#64;", basename)
            if b in map_image2file:
                rows.append("<tr><td>")
                for x, link in enumerate(map_image2file[b]):
                    rows.append("""<a href="%s">[%i]</a> """ % (link, x))
                rows.append("</td></tr>")

            rows.append("</table></td>")

        col += 1

    rows.append("</tr></table>")

    fh = file(dest, 'w')
    fh.write(template % '\n'.join(rows))
    fh.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
