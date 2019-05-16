import re

from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from CGATReport.Plugins.Renderer import Renderer
from CGATReport.DataTree import path2str
from docutils.parsers.rst import directives

try:
    import holoviews as hv
    from holoviews.plotting import mpl
    HAS_HOLOVIEW = True
except ImportError:
    HAS_HOLOVIEW = False


class HoloviewsPlot(Renderer):

    options = Renderer.options + \
              (('statement', directives.unchanged),)

    statement = None
    engine = "bokeh"
    
    def __init__(self, *args, **kwargs):
        self.statement = kwargs.get("statement", "")
        if self.statement is None:
            raise ValueError("HoloviewPlot requires 'statement' to be given")

        if not HAS_HOLOVIEW:
            raise ValueError("Holoview can not be imported")
        
    def render(self, data, path):
        """execute holoview statements."""
        statement = self.statement.strip()
        assert statement.endswith(")")

        g, l = globals(), locals()
        layout = None
        try:
            exec("layout = %s" % statement, g, l)
        except Exception as msg:
            raise Exception(
                "holoviews raised error for statement '%s': msg=%s" %
                (statement, msg))

        return self.endPlot(l["layout"], None, path)

    def endPlot(self, layout, legend, path):
        title = path2str(path)
        r = ResultBlock(
            text="#$hv {}$#".format(title),
            title=title)
        r.hv = layout
        
        return ResultBlocks(r)
        
