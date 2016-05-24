'''Plotting using the ggplot module.'''

from CGATReportPlugins.Renderer import Renderer
from CGATReportPlugins.Plotter import Plotter
from docutils.parsers.rst import directives

import matplotlib.pyplot as plt
import pandas


class PandasPlot(Renderer, Plotter):

    """Use the python ggplot libary for plotting.
    """
    options = (
        ('statement',  directives.unchanged),
    ) + Renderer.options + Plotter.options

    group_level = 0

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

        self.statement = kwargs.get('statement')

    def render(self, dataframe, path):

        # the index in the dataframe is reset in order
        # to add the index as a column.

        # Currently, ggplot is not using hierarchical indices, but
        # see this thread: https://github.com/yhat/ggplot/issues/285

        dataframe.reset_index(inplace=True)

        p = None
        s = "p = dataframe.plot(%s)" % self.statement

        try:
            exec s in globals(), locals()
        except Exception, msg:
            raise Exception(
                "pandas.plot() raised error for statement '%s': msg=%s" %
                (s, msg))

        self.mFigure += 1
        if self.title:
            plt.title(self.title)
        plts = [p]
        return self.endPlot(plts, None, path)
