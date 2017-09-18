from docutils.parsers.rst import directives

from .Plotter import TableMatrixPlot, DataSeriesPlot
import pandas
import seaborn
import numpy
from CGATReport.Plugins.Renderer import Renderer
from CGATReport.Plugins.Plotter import Plotter


class SeabornPlot(object):

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

class PairPlot(Renderer, Plotter, SeabornPlot):

    options = Renderer.options +\
              Plotter.options +\
              SeabornPlot.options

    def __init__(self, *args, **kwargs):
        Renderer.__init__(self, *args, **kwargs)
        Plotter.__init__(self, *args, **kwargs)
        SeabornPlot.__init__(self, *args, **kwargs)

    def render(self, dataframe, path):

        statement = ("seaborn.pairplot(dataframe)")
        plot = self.execute(statement, globals(), locals())

        return self.endPlot([plot], [], path)


class BoxPlot(DataSeriesPlot, SeabornPlot):

    """Write a set of box plots.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """

    options = DataSeriesPlot.options +\
              SeabornPlot.options

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornPlot.__init__(self, *args, **kwargs)

    def plotData(self, data, melted):
        if melted:
            return [seaborn.boxplot(data.value,
                                    hue=data.label)]
        else:
            return [seaborn.boxplot(data)]


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


class KdePlot(DataSeriesPlot, SeabornPlot):

    """Write a set of density plots.

    The data series is converted to a kernel density
    estimate.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """
    options = DataSeriesPlot.options +\
              SeabornPlot.options

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornPlot.__init__(self, *args, **kwargs)

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


class DistPlot(DataSeriesPlot, SeabornPlot):
    """Write a set of density plots.

    The data series is converted to a kernel density
    estimate.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """

    options = DataSeriesPlot.options + SeabornPlot.options

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornPlot.__init__(self, *args, **kwargs)

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


class SeabornMatrixPlot(TableMatrixPlot, SeabornPlot):

    options = TableMatrixPlot.options + SeabornPlot.options

    def __init__(self, *args, **kwargs):
        TableMatrixPlot.__init__(self, *args, **kwargs)
        SeabornPlot.__init__(self, *args, **kwargs)

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
