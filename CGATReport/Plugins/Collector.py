from CGATReport.Component import Component


class Collector(Component):

    capabilities = ['collect']

    def __init__(self, *args, **kwargs):
        Component.__init__(self, *args, **kwargs)

        self.template_name = kwargs.get("template_name")
        self.outdir = kwargs.get("outdir")
        self.rstdir = kwargs.get("rstdir")
        self.builddir = kwargs.get("builddir")
        self.srcdir = kwargs.get("srcdir")
        self.content = kwargs.get("content")
        self.display_options = kwargs.get("display_options")
        self.tracker_id = kwargs.get("tracker_id")
        self.links = kwargs.get("links")
