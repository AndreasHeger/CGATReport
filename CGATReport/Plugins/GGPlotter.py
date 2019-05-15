'''Plotting using the ggplot module.'''
import sys

from CGATReport.Plugins.Renderer import Renderer
from CGATReport.Plugins.Plotter import Plotter
from docutils.parsers.rst import directives

import matplotlib.pyplot as plt
import pandas
import copy
import warnings

try:
    from plotnine import *
except ImportError:
    pass


class GGPlot(Renderer, Plotter):
    """Use the python plotnine libary for plotting.
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

        # the index in the dataframe is reset in order to add the
        # index as a column so that it is available for plotting.
        dataframe.reset_index(inplace=True)
        
        if len(dataframe.dropna()) == 0:
            warnings.warn("dataframe is empty after dropping all NA columns")
            return None

        s = "plot = ggplot(aes(%s), data=dataframe) + %s" % (self.aes, self.geom)
        ll = copy.copy(locals())
        gl = copy.copy(globals())
        try:
            exec(s, gl, ll)
        except Exception as msg:
            raise Exception(
                "plotnine raised error for statement '{}': msg={}".format(s, msg))
        plot = ll["plot"]

        if self.title:
            plt.title(self.title)

        try:
            plts = [plot.draw()]
        except Exception as msg:
            raise Exception(
                "ggplot raised error on rendering for statement '{}': msg={}".format(
                s, msg))
        return self.endPlot(plts, None, path)
