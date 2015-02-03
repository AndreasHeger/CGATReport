import os
import re

from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from CGATReportPlugins.Renderer import Renderer
from CGATReport.DataTree import path2str
from CGATReport import Utils

# Plain setup, simple horizontal/vertical slider
# Customization: autoplay, dragorientation, size
SETUP_PLAIN = """
<script type="text/javascript" src="_static/js/jssor.js"></script>
<script type="text/javascript" src="_static/js/jssor.slider.js"></script>
    <script>
        jQuery(document).ready(function ($) {
            var options = {
                $AutoPlay: false,
                $DragOrientation: 1,
            };
            var jssor_slider1 = new $JssorSlider$(
                                "%(name)s_container",
                                options);
        });
    </script>

<div id="%(name)s_container"
        style="position: relative; top: 0px; left: 0px;
        width: %(width)ipx; height: %(width)ipx;">
<div u="slides"
        style="cursor: move; position: absolute; left: 0px; top: 0px;
        width: %(width)ipx; height: %(width)ipx; overflow: hidden;">
"""


class SlideshowPlot(Renderer):

    options = Renderer.options

    group_level = "all"
    nlevels = 1

    # 1. DONE: automatically set paths and resources - through theme
    # 2. DONE: Multiple sliders per page without interference
    #       issue with checking if an element is up-to-date.
    #       check is for of images. Need to be different if 
    #       to add the same element.
    # 3. DONE: Make sure images are packed into report (i.e. not absolute paths)
    # 4. get dimensions from rst directive to set size (width, height)
    # 5. Refactor boiler plate code
    # 6. implement different slideshows
    #    1. implement captions
    #    2. implement thumbnails
    # 7. Implement a non-html view

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)

    def render(self, dataframe, path):

        blocks = ResultBlocks()

        # DragOrientation: 1, 2 or 3, could be optional?
        # Picture size
        width = 300
        height = 300
        name = "SlideShowPlot_%i" % (id(self))

        lines = [SETUP_PLAIN % locals()]

        for title, row in dataframe.iterrows():
            row = row[row.notnull()]
            values = row.tolist()
            headers = list(row.index)
            
            dataseries = dict(zip(headers, values))
            try:
                # return value is a series
                filename = dataseries['filename']
            except KeyError:
                self.warn(
                    "no 'filename' key in path %s" % (path2str(path)))
                return blocks

            try:
                # return value is a series
                name = dataseries['name']
            except KeyError:
                self.warn(
                    "no 'name' key in path %s" % (path2str(path)))
                return blocks

            mangled_filename = re.sub("/", "_", filename)
            filename = os.path.abspath(filename)
            outdir = Utils.getOutputDirectory()
            dest = os.path.join(outdir,
                                mangled_filename)
            os.link(filename, dest)

            lines.append(
                """<div><img u="image" src="%(dest)s" /></div>
                """ % locals())

        lines.append("""</div>""")
        lines.append("""<a style="display: none" href="http://www.jssor.com">jQuery Slider</a>
    </div>""")
        
        lines = "\n".join(lines).split("\n")
        lines = [".. htmlonly::\n"] +\
            ["   .. raw:: html\n"] +\
            ["      " + x for x in lines]

        lines = "\n".join(lines)

        blocks.append(ResultBlock(text=lines,
                                  title=path2str(path)))
        return blocks

