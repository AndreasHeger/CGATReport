'''Plotting using the ggplot module.'''

from CGATReportPlugins.Renderer import Renderer
from CGATReportPlugins.Plotter import Plotter
from docutils.parsers.rst import directives

import matplotlib.pyplot as plt
import pandas

# import all into namespace for eval
from ggplot import *


class GGPlot(Renderer, Plotter):

    """Write a set of box plots.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """
    options = (
        ('aes',  directives.unchanged),
        ('geom', directives.unchanged),
    ) + Renderer.options + Plotter.options

    nlevels = -1

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

        if "aes" not in kwargs:
            raise ValueError("ggplot renderer requires an aesthetics option")

        if "geom" not in kwargs:
            raise ValueError("ggplot renderer requires a geom option")

        self.aes = kwargs.get('aes')
        self.geom = kwargs.get('geom')

    def render(self, dataframe, path):

        # the index in the dataframe is reset in order
        # to add the index as a column.

        # Currently, ggplot is not using hierarchical indices, but
        # see this thread: https://github.com/yhat/ggplot/issues/285

        dataframe.reset_index(inplace=True)

        s = "p = ggplot(aes(%s), data=dataframe) + %s" % (self.aes, self.geom)

        try:
            exec s in globals(), locals()
        except Exception, msg:
            raise Exception(
                "ggplot raised error for statement '%s': msg=%s" %
                (s, msg))

        # p.draw() calls figure() command, so do not call self.startPlot()
        self.mFigure += 1
        if self.title:
            plt.title(self.title)
        plts = [p.draw()]
        return self.endPlot(plts, None, path)
