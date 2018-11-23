from docutils.parsers.rst import directives

import pandas
import seaborn
import numpy
import matplotlib.pyplot as plt
from CGATReport.Plugins.Renderer import Renderer
from CGATReport.Plugins.Plotter import Plotter
from CGATReport.Plugins.Plotter import TableMatrixPlot, DataSeriesPlot


class SeabornPlot(Renderer, Plotter):

    """Use the seaborn libary for plotting.
    """
    options = (
        ('statement', directives.unchanged),
        ('kwargs', directives.unchanged),
        ('kind', directives.unchanged),
    ) + Renderer.options + Plotter.options

    group_level = 0

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)

        # statement is synonym for kwargs. The latter takes precedence
        self.kwargs = kwargs.get('kwargs', kwargs.get('statement'))
        self.plot_kind = kwargs.get('kind', None)
        if self.plot_kind is None:
            raise ValueError("seaborn-plot requires :kind: setting")

    def render(self, dataframe, path):

        # Used to call reset_index() here in order to add
        # the index as a column, but now let caller do this.
        self.startPlot()
        p = None
        s = "p = seaborn.{}(data=dataframe.reset_index(), {}, ax=plt.gca())".format(
            self.plot_kind, self.kwargs)

        try:
            exec(s, globals(), locals())
        except Exception as msg:
            raise Exception(
                "seaborn.{}() raised error for statement '{}': msg={}".format(
                    self.plot_kind, s, msg))

        if self.title:
            plt.title(self.title)
        plts = [p]

        return self.endPlot(plts, None, path)


class SeabornIndirectPlot(object):

    options = (
        ('kwargs', directives.unchanged),
    )

    kwargs = ""

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs.get("kwargs", "")

    def execute(self, statement, g, l):
        """execute seaborn statement. Inserts kwargs."""
        statement = statement.strip()
        assert statement.endswith(")")
        if self.kwargs:
            statement = statement[:-1] + ", %s)" % self.kwargs

        plot = None
        try:
            exec("plot = %s" % statement, g, l)
        except Exception as msg:
            raise Exception(
                "seaborn raised error for statement '%s': msg=%s" %
                (statement, msg))
        return plot

    def build_kwargs_dict():
        pass


class PairPlot(Renderer, Plotter, SeabornIndirectPlot):

    options = Renderer.options +\
              Plotter.options +\
              SeabornIndirectPlot.options

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)
        SeabornIndirectPlot.__init__(self, *args, **kwargs)

    def render(self, dataframe, path):

        statement = ("seaborn.pairplot(dataframe)")
        plot = self.execute(statement, globals(), locals())

        return self.endPlot([plot], [], path)


class BoxPlot(DataSeriesPlot, SeabornIndirectPlot):

    """Write a set of box plots.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """

    options = DataSeriesPlot.options +\
              SeabornIndirectPlot.options

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornIndirectPlot.__init__(self, *args, **kwargs)

    def plotData(self, data, melted):
        if melted:
            return [seaborn.boxplot(data.value,
                                    hue=data.label)]
        else:
            return [seaborn.boxplot(data)]


class BarPlot(DataSeriesPlot, SeabornIndirectPlot):

    """Write a set of bar plots.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """

    options = DataSeriesPlot.options +\
              SeabornIndirectPlot.options

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornIndirectPlot.__init__(self, *args, **kwargs)

    def plotData(self, data, melted):
        if melted:
            return [seaborn.barplot(data.value,
                                    hue=data.label)]
        return [seaborn.barplot(data)]


class ViolinPlot(BoxPlot):

    """Write a set of violin plots.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """

    options = BoxPlot.options

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        BoxPlot.__init__(self, *args, **kwargs)

    def plotData(self, data, melted):
        if melted:
            return [seaborn.violinplot(data.value,
                                       groupby=data.label)]
        else:
            return [seaborn.violinplot(data)]


class KdePlot(DataSeriesPlot, SeabornIndirectPlot):

    """Write a set of density plots.

    The data series is converted to a kernel density
    estimate.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """
    options = DataSeriesPlot.options +\
              SeabornIndirectPlot.options

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornIndirectPlot.__init__(self, *args, **kwargs)

    def plotData(self, dataframe, melted):
        plts = []
        if melted:
            for key, group in dataframe.groupby(dataframe.label):
                plot = self.execute(
                    "seaborn.kdeplot( "
                    "numpy.array(dataframe.value, dtype=numpy.float), "
                    "label=key)", globals(), locals())
                plts.append(plot)
        else:
            for column in dataframe.columns:
                plot = self.execute(
                    "seaborn.kdeplot( "
                    "numpy.array(dataframe[column], dtype=numpy.float), "
                    "label=column)", globals(), locals())
        return plts


class DistPlot(DataSeriesPlot, SeabornIndirectPlot):
    """Write a set of density plots.

    The data series is converted to a kernel density
    estimate.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """

    options = DataSeriesPlot.options + SeabornIndirectPlot.options

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornIndirectPlot.__init__(self, *args, **kwargs)

    def plotData(self, dataframe, melted):
        plts = []
        if melted:
            for key, group in dataframe.groupby(dataframe.label):
                plot = self.execute(
                    "seaborn.distplot( "
                    "numpy.array(dataframe.value, dtype=numpy.float), "
                    "label=key)", globals(), locals())
                plts.append(plot)
        else:
            for column in dataframe.columns:
                plot = self.execute(
                    "seaborn.distplot( "
                    "numpy.array(dataframe[column], dtype=numpy.float), "
                    "label=column)", globals(), locals())
                plts.append(plot)
        return plts


class SeabornMatrixPlot(TableMatrixPlot, SeabornIndirectPlot):

    options = TableMatrixPlot.options + SeabornIndirectPlot.options

    def __init__(self, *args, **kwargs):
        TableMatrixPlot.__init__(self, *args, **kwargs)
        SeabornIndirectPlot.__init__(self, *args, **kwargs)

    def addColourBar(self):
        pass

    def startPlot(self, **kwargs):

        # seaborn will create figure, so do not create one.
        self.mFigure += 1

    def plotMatrix(self, matrix, row_headers, col_headers,
                   vmin, vmax, colorscheme=None):

        self.debug("plot matrix started")
        data = pandas.DataFrame(matrix,
                                columns=col_headers,
                                index=row_headers)
        statement = self.buildStatement(data)
        self.debug("seaborn: executing statement '%s'" % statement)
        plot = self.execute(statement, globals(), locals())
        self.debug("plot matrix finished")
        return plot


class HeatmapPlot(SeabornMatrixPlot):
    """Render a matrix as a heatmap using seaborn.
    """

    def buildStatement(self, data):
        return("plot = seaborn.heatmap(data)")


class ClustermapPlot(SeabornMatrixPlot):
    """Render a matrix as a heatmap using seaborn.
    """

    options = (('row-regex', directives.unchanged),
               ('col-regex', directives.unchanged),
               ) + SeabornMatrixPlot.options

    row_regex = None
    col_regex = None

    def __init__(self, *args, **kwargs):
        SeabornMatrixPlot.__init__(self, *args, **kwargs)
        self.row_regex = kwargs.get("row-regex", None)
        self.col_regex = kwargs.get("col-regex", None)

    def buildStatement(self, data):

        if data.isnull().any().any():
            raise ValueError("dataframe contains NaN")

        extra_options = []
        if self.row_regex:
            row_names = data.index.str.extract(self.row_regex)
            factors = list(set(row_names))
            colors = matplotlib.cm.rainbow(numpy.linspace(0, 1, len(factors)))
            factor2color = dict([(y, x) for x, y in enumerate(factors)])
            row_colors = [colors[factor2color[x]] for x in row_names]

            extra_options.append(
                "row_colors={}".format(str(row_colors)))

        if extra_options:
            extra_options = "," + ",".join(extra_options)
        else:
            extra_options = ""

        return("plot = seaborn.clustermap(data {})".format(extra_options))
