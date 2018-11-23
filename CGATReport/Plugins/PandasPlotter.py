'''Plotting using the ggplot module.'''

from CGATReport.Plugins.Renderer import Renderer
from CGATReport.Plugins.Plotter import Plotter
from docutils.parsers.rst import directives

import matplotlib.pyplot as plt
import pandas


class PandasPlot(Renderer, Plotter):

    """Use the pandas libary for plotting.
    """
    options = (
        ('statement',  directives.unchanged),
        ('kwargs', directives.unchanged)
    ) + Renderer.options + Plotter.options

    group_level = 0

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

        # statement is synonym for kwargs. The latter takes precedence
        self.kwargs = kwargs.get('kwargs', kwargs.get('statement'))

    def render(self, dataframe, path):

        # Used to call reset_index() here in order to add
        # the index as a column, but now let caller do this.
        self.startPlot()
        p = None
        s = "p = dataframe.plot(%s, ax=plt.gca())" % self.kwargs

        try:
            exec(s, globals(), locals())
        except Exception as msg:
            raise Exception(
                "pandas.plot() raised error for statement '%s': msg=%s" %
                (s, msg))

        if self.title:
            plt.title(self.title)
        plts = [p]

        return self.endPlot(plts, None, path)
