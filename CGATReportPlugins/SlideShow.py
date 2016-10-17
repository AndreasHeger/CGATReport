import os
import re
import random

from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from CGATReportPlugins.Renderer import Renderer
from CGATReport.DataTree import path2str
from CGATReport import Utils
from docutils.parsers.rst import directives

import PIL

# Any scripts need to be added to layout.html in the theme.
# This will ensure that the relative path is used if a page
# is within a subdirectory. As a downside, all js code will
# be imported on every page.

# Plain setup, simple horizontal/vertical slider
# Customization: autoplay, dragorientation, size
PLAIN_SETUP = """
<script>
   jQuery(document).ready(function ($) {
            var options = {
                $AutoPlay: %(autoplay)s,
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
<script>
    jQuery(document).ready(function ($) {
        var options = {
            $AutoPlay: %(autoplay)s,
            $DragOrientation: 2,
            $ThumbnailNavigatorOptions: {
                    $Class: $JssorThumbnailNavigator$,
                    $ChanceToShow: 2,
                    $Loop: 2,
                    $AutoCenter: 3,
                    $Lanes: %(thumbnail_lanes)i,
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
        width: %(width)ipx; height: %(height)ipx;">
   <div u="slides"
        style="cursor: move; position: absolute; left: 0px; top: 0px;
        width: %(width)ipx; height: %(height)ipx; overflow: hidden;">

"""

LIST_SKIN = """
        <!-- ThumbnailNavigator Skin Begin -->
        <div u="thumbnavigator" class="jssort11" style="position: absolute;
              width: %(thumbnail_width)ipx; height: %(height)ipx;
              left:%(width)ipx; top:0px;">
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
                        width: %(lane_width)ipx;
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
                .jssort11 .p:hover .t, .jssort11 .phv .t, .jssort11
                .pav:hover .t, .jssort11 .p:hover .c, .jssort11 .phv .c,
                .jssort11 .pav:hover .c
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
                <div u="prototype" class="p" style="position: absolute;
                     width: %(lane_width)ipx; height: 69px; top: 0; left: 0;">
                    <div u="thumbnailtemplate" style="
                     width: 100%%; height: 100%%;
                     border: none;position:absolute; top: 0; left: 0;"></div>
                </div>
            </div>
            <!-- Thumbnail Item Skin End -->
        </div>
        <!-- ThumbnailNavigator Skin End -->
"""


class SlideShowPlot(Renderer):
    """Factory class for slide show plots.

    The ``style`` option determines the slide show
    type that is returned.
    """
    
    options = Renderer.options +\
        (("autoplay", directives.flag),
         ("style", directives.unchanged),
         ("thumbnail-width", directives.positive_int),
         ("thumbnail-display", directives.positive_int),
         ("thumbnail-lanes", directives.positive_int))

    def __new__(cls, *args, **kwargs):

        # return special instances depending on style argument
        style = kwargs.get("style", "plain")

        if style == "plain":
            return PlainSlideShow(*args, **kwargs)
        elif style == "caption":
            return CaptionSlideShow(*args, **kwargs)
        elif style == "thumbnail-navigator":
            return ThumbnailSlideShow(*args, **kwargs)
        else:
            raise ValueError("unknown slide show style '%s'" % style)


class PlainSlideShow(Renderer):

    prefix = PLAIN_SETUP
    skin = ""

    # 1. DONE: automatically set paths and resources - through theme
    # 2. DONE: Multiple sliders per page without interference
    #       issue with checking if an element is up-to-date.
    #       check is for of images. Need to be different if
    #       to add the same element.
    # 3. DONE: Make sure images are packed into report
    # 4. DONE: get dimensions from rst directive to set size (width, height)
    # 5. DONE: Refactor boiler plate code - use factory
    # 6. implement different slideshows
    #    1. implement captions
    #    2. implement thumbnails
    # 7. Implement a non-html view

    # JS option: true if slide show should autoplay
    autoplay = "false"

    group_level = "all"
    nlevels = 1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)

        if "autoplay" in kwargs:
            self.autoplay = "true"
        else:
            self.autoplay = "false"

        self.thumbnail_display = kwargs.get("thumbnail-display", 4)
        self.thumbnail_lanes = kwargs.get("thumbnail-lanes", 1)
        self.thumbnail_width = kwargs.get("thumbnail-width", 200)

    def import_image(self, filename):
        '''import image into report. The image is hard-linked.

        returns path to image for use in html.
        '''

        mangled_filename = re.sub("/", "_", filename)
        filename = os.path.abspath(filename)

        # directory in which to store images and thumbnails
        outdir = Utils.getOutputDirectory()
        image_filename = os.path.join(outdir,
                                      mangled_filename)

        # filenames to use in html - must take document hierarchy
        # into account
        rst2srcdir = os.path.join(
            os.path.relpath(self.src_dir, start=self.rst_dir),
            outdir)
        html_image_filename = os.path.join(rst2srcdir,
                                           mangled_filename)

        try:
            os.link(filename, image_filename)
        except OSError:
            # file exists
            pass

        return html_image_filename

    def import_thumbnail(self, filename, thumbnail_size):
        '''import image in *filename* as a thumbnail.

        thumbnail_size is a tuple of (height, width) of the thumbnail
        in pixels.

        '''

        mangled_filename = re.sub("/", "_", filename)

        # directory in which to store images and thumbnails
        outdir = Utils.getOutputDirectory()
        thumb_filename = os.path.join(outdir,
                                      "thumb-%s.png" % mangled_filename)

        image = PIL.Image.open(filename)
        image.thumbnail(thumbnail_size)
        image.save(thumb_filename)

        # filenames to use in html - must take document hierarchy
        # into account
        rst2srcdir = os.path.join(
            os.path.relpath(self.src_dir, start=self.rst_dir),
            outdir)
        html_thumb_filename = os.path.join(rst2srcdir,
                                           "thumb-%s.png" % mangled_filename)

        return html_thumb_filename

    def add_image(self, filename, title, description):

        html_image_filename = self.import_image(filename)

        return [
            """<div><img u="image" src="%(html_image_filename)s" /></div>
            """ % locals()]

    def get_slideshow_options(self):

        self.width = int(self.display_options.get("width", 300))
        self.height = int(self.display_options.get("height", 300))
        return {'name': "SlideShowPlot_%09i" % random.randint(0, 1000000000),
                'width': self.width,
                'height': self.height,
                'autoplay': self.autoplay}

    def render(self, dataframe, path):

        blocks = ResultBlocks()

        options = self.get_slideshow_options()
        lines = [self.prefix % options]

        for title, row in dataframe.iterrows():
            row = row[row.notnull()]
            values = row.tolist()
            headers = list(row.index)

            dataseries = dict(list(zip(headers, values)))
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

            description, title = os.path.split(name)

            lines.extend(self.add_image(filename, title, description))

        lines.append("""</div>""")

        lines.append(self.skin % options)

        lines.append("""</div>""")

        lines = "\n".join(lines).split("\n")
        lines = [".. only::html\n"] +\
            ["   .. raw:: html\n"] +\
            ["      " + x for x in lines]

        lines = "\n".join(lines)

        blocks.append(ResultBlock(text=lines,
                                  title=path2str(path)))
        return blocks


class CaptionSlideShow(PlainSlideShow):
    """A slide show with captions underneath the images."""
    
    def add_image(self, filename, title, description):

        html_image_filename = self.import_image(filename)

        width = self.width
        top = self.height - 50

        return [
            """<div>
                  <img u="image" src="%(html_image_filename)s"/>
                  <div style="position: absolute;
                       top: %(top)ipx; left: 0px;
                       width: %(width)ipx; height: 50px;
                       text-align:center;line-height:50px;
                       opacity: 0.5; filter: alpha(opacity=50);
                       background:#fff;">
                       %(title)s %(description)s
                  </div>
               </div>
            """ % locals()]


class ThumbnailSlideShow(PlainSlideShow):
    '''A slide show with column of thumbnails on the side.'''

    prefix = LIST_SETUP
    skin = LIST_SKIN

    def get_slideshow_options(self):
        options = PlainSlideShow.get_slideshow_options(self)
        options.update({
            "thumbnail_lanes": self.thumbnail_lanes,
            "thumbnail_display": self.thumbnail_display,
            "thumbnail_width": self.thumbnail_width,
            "lane_width": (self.thumbnail_width / self.thumbnail_lanes) - 3})
        return options

    def add_image(self, filename, title, description):

        thumbnail_size = self.height / self.thumbnail_display

        html_image_filename = self.import_image(filename)
        html_thumb_filename = self.import_thumbnail(
            filename,
            (thumbnail_size,
             thumbnail_size))

        return [
            """
            <div>
              <img u="image" src="%(html_image_filename)s" />
                <div u="thumb">
                  <abbr title="%(title)s %(description)s">
                     <img class="i" src="%(html_thumb_filename)s" />
                  </abbr>
                  <div class="c">%(title)s</div>
                  <div class="t">%(description)s</div>
                </div>
            </div>
            """ % locals()]

