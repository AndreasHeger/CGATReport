import os
import re

from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from CGATReportPlugins.Renderer import Renderer
from CGATReport.DataTree import path2str
from CGATReport import Utils

import PIL

# Plain setup, simple horizontal/vertical slider
# Customization: autoplay, dragorientation, size
PLAIN_SETUP = """
<script type="text/javascript" src="_static/js/jquery-1.9.1.min.js"></script>
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

LIST_SETUP = """
<script type="text/javascript" src="_static/js/jquery-1.9.1.min.js"></script>
<script type="text/javascript" src="_static/js/jssor.js"></script>
<script type="text/javascript" src="_static/js/jssor.slider.js"></script>
<script>
    jQuery(document).ready(function ($) {
        var options = {
            $AutoPlay: false,
            $DragOrientation: 2,
            $ThumbnailNavigatorOptions: {
                    $Class: $JssorThumbnailNavigator$,
                    $ChanceToShow: 2,
                    $Loop: 2,
                    $AutoCenter: 3,
                    $Lanes: 1,
                    $SpacingX: 4,
                    $SpacingY: 4,
                    $DisplayPieces: 4,
                    $ParkingPosition: 0,
                    $Orientation: 2,
                }
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

LIST_SKIN = """
        <!-- ThumbnailNavigator Skin Begin -->
        <div u="thumbnavigator" class="jssort11" style="position: absolute; width: 200px; height: 300px; left:605px; top:0px;">
            <!-- Thumbnail Item Skin Begin -->
            <style>
                /* jssor slider thumbnail navigator skin 11 css */
                /*
                .jssort11 .p            (normal)
                .jssort11 .p:hover      (normal mouseover)
                .jssort11 .pav          (active)
                .jssort11 .pav:hover    (active mouseover)
                .jssort11 .pdn          (mousedown)
                */
                .jssort11
                {
                        font-family: Arial, Helvetica, sans-serif;
                }
                .jssort11 .i, .jssort11 .pav:hover .i
                {
                        position: absolute;
                        top:3px;
                        left:3px;
                        WIDTH: 60px;
                        HEIGHT: 30px;
                        border: white 1px dashed;
                }
                * html .jssort11 .i
                {
                        WIDTH /**/: 62px;
                        HEIGHT /**/: 32px;
                }
                .jssort11 .pav .i
                {
                        border: white 1px solid;
                }
                .jssort11 .t, .jssort11 .pav:hover .t
                {
                        position: absolute;
                        top: 3px;
                        left: 68px;
                        width:129px;
                        height: 32px;
                        line-height:32px;
                        text-align: center;
                        color:#fc9835;
                        font-size:13px;
                        font-weight:700;
                }
                .jssort11 .pav .t, .jssort11 .phv .t, .jssort11 .p:hover .t
                {
                        color:#fff;
                }
                .jssort11 .c, .jssort11 .pav:hover .c
                {
                        position: absolute;
                        top: 38px;
                        left: 3px;
                        width:197px;
                        height: 31px;
                        line-height:31px;
                        color:#fff;
                        font-size:11px;
                        font-weight:400;
                        overflow: hidden;
                }
                .jssort11 .pav .c, .jssort11 .phv .c, .jssort11 .p:hover .c
                {
                        color:#fc9835;
                }
                .jssort11 .t, .jssort11 .c
                {
                        transition: color 2s;
                    -moz-transition: color 2s;
                    -webkit-transition: color 2s;
                    -o-transition: color 2s;
                    -webkit-transition: color 2s;
                    -o-transition: color 2s;
                }
                .jssort11 .p:hover .t, .jssort11 .phv .t, .jssort11 .pav:hover .t, .jssort11 .p:hover .c, .jssort11 .phv .c, .jssort11 .pav:hover .c
                {
                        transition: none;
                    -moz-transition: none;
                    -webkit-transition: none;
                    -o-transition: none;
                }
                .jssort11 .p
                {
                        background:#181818;
                }
                .jssort11 .pav, .jssort11 .pdn
                {
                        background:#462300;
                }
                .jssort11 .p:hover, .jssort11 .phv, .jssort11 .pav:hover
                {
                        background:#333;
                }
            </style>
            <div u="slides" style="cursor: move;">
                <div u="prototype" class="p" style="position: absolute; width: 200px; height: 69px; top: 0; left: 0;">
                    <div u="thumbnailtemplate" style=" width: 100%%; height: 100%%; border: none;position:absolute; top: 0; left: 0;"></div>
                </div>
            </div>
            <!-- Thumbnail Item Skin End -->
        </div>
        <!-- ThumbnailNavigator Skin End -->
"""

class SlideshowPlot(Renderer):

    options = Renderer.options

    group_level = "all"
    nlevels = 1

    prefix = PLAIN_SETUP
    skin = ""

    width = 300
    height = 300

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

    def add_image(self, filename, name):

        mangled_filename = re.sub("/", "_", filename)
        filename = os.path.abspath(filename)
        outdir = Utils.getOutputDirectory()
        dest = os.path.join(outdir,
                            mangled_filename)
        os.link(filename, dest)

        return [
            """<div><img u="image" src="%(dest)s" /></div>
            """ % locals()]

    def render(self, dataframe, path):

        blocks = ResultBlocks()

        width = self.width
        height = self.height
        name = "SlideShowPlot_%i" % (id(self))

        lines = [self.prefix % locals()]

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

            lines.extend(self.add_image(filename, name))

        lines.append("""</div>""")

        lines.append(self.skin % locals())

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


class SlideshowWithThumbnailsPlot(SlideshowPlot):

    prefix = LIST_SETUP
    skin = LIST_SKIN

    thumbnail_size = 128, 128

    width = 600
    heigh = 300

    def add_image(self, filename, name):

        mangled_filename = re.sub("/", "_", filename)
        filename = os.path.abspath(filename)
        outdir = Utils.getOutputDirectory()
        dest = os.path.join(outdir,
                            mangled_filename)
        thumb = os.path.join(outdir,
                             "thumb-%s.png" % mangled_filename)
        os.link(filename, dest)

        image = PIL.Image.open(filename)
        image.thumbnail(self.thumbnail_size)
        image.save(thumb)

        return [
            """<div>
                   <img u="image" src="%(dest)s" />
                   <div u="thumb">
                        <img class="i" src="%(thumb)s" />
                   </div>
            </div>
            """ % locals()]

