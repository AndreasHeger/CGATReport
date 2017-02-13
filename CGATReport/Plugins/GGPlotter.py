'''Plotting using the ggplot module.'''
import sys

from CGATReport.Plugins.Renderer import Renderer
from CGATReport.Plugins.Plotter import Plotter
from docutils.parsers.rst import directives

import matplotlib.pyplot as plt
import pandas
import copy


SHAPES = [
    'o',  # circle
    '^',  # triangle up
    '<',
    '>',
    'D',  # diamond
    'v',  # triangle down
    's',  # square
    '*',  # star
    'p',  # pentagon
    '*',  # octagon
    'h',
    'H',
    'd',
]

# ggplot > 0.9
try:
    import ggplot.discretemappers
    ggplot.discretemappers.SHAPES = SHAPES
except ImportError:
    pass

# import all into namespace for eval
from ggplot import *


class GGPlot(Renderer, Plotter):

    """Use the python ggplot libary for plotting.
    """
    options = (
        ('aes',  directives.unchanged),
        ('geom', directives.unchanged),
    ) + Renderer.options + Plotter.options

    group_level = 0

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

        if len(dataframe.dropna()) == 0:
            return []

        s = "plot = ggplot(aes(%s), data=dataframe) + %s" % (self.aes, self.geom)
        ll = copy.copy(locals())
        gl = copy.copy(globals())
        try:
            exec(s, gl, ll)
        except Exception as msg:
            raise Exception(
                "ggplot raised error for statement '%s': msg=%s" %
                (s, msg))
        plot = ll["plot"]

        self.mFigure += 1
        if self.title:
            plt.title(self.title)

        # plot.make() calls plt.close() command, so create a dummy to be
        # closed.
        plt.figure()
        try:
            plts = [plot.make()]
        except Exception as msg:
            raise Exception(
                "ggplot raised error on rendering for statement '%s': msg=%s" %
                (s, msg))

        return self.endPlot(plts, None, path)
