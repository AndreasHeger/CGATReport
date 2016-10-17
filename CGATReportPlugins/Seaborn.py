from docutils.parsers.rst import directives

from .Plotter import TableMatrixPlot, DataSeriesPlot
import pandas
import seaborn
import numpy
from CGATReportPlugins.Renderer import Renderer
from CGATReportPlugins.Plotter import Plotter


class SeabornPlot(object):

    options = (('kwargs', directives.unchanged),)
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


class PairPlot(Renderer, Plotter, SeabornPlot):

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

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornPlot.__init__(self, *args, **kwargs)

    def plotData(self, data, melted):
        if melted:
            return [seaborn.boxplot(data.value,
                                    groupby=data.label)]
        else:
            return [seaborn.boxplot(data)]


class ViolinPlot(BoxPlot):

    """Write a set of violin plots.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """

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
        (('shade', directives.flag),
         ('vertical', directives.flag),
         ('kernel', directives.unchanged),
         ('bw', directives.unchanged),
         ('gridsize', directives.unchanged),
         ('cut', directives.unchanged),
         ('clip', directives.unchanged),
         )

    def __init__(self, *args, **kwargs):
        DataSeriesPlot.__init__(self, *args, **kwargs)
        SeabornPlot.__init__(self, *args, **kwargs)

        self.shade = kwargs.get('shade', False)
        self.vertical = kwargs.get('shade', False)
        self.kernel = kwargs.get('kernel', 'gau')
        self.bw = kwargs.get('bw', 'scott')
        self.gridsize = int(kwargs.get('gridsize', 100))
        self.cut = int(kwargs.get('cut', 3))
        if 'clip' in kwargs:
            self.clip = list(map(int, kwargs['clip'].split(',')))

    def plotData(self, dataframe, melted):
        plts = []
        if melted:
            for key, group in dataframe.groupby(dataframe.label):
                plts.append(seaborn.kdeplot(
                    numpy.array(dataframe.value, dtype=numpy.float),
                    label=key,
                    shade=self.shade,
                    vertical=self.vertical,
                    kernel=self.kernel))
        else:
            for column in dataframe.columns:
                plts.append(seaborn.kdeplot(
                    numpy.array(dataframe[column], dtype=numpy.float),
                    label=column,
                    shade=self.shade,
                    vertical=self.vertical,
                    kernel=self.kernel))
        return plts


class DistPlot(DataSeriesPlot, SeabornPlot):
    """Write a set of density plots.

    The data series is converted to a kernel density
    estimate.

    This:class:`Renderer` requires two levels.

    labels[dict] / data[array]
    """

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

    def __init__(self, *args, **kwargs):
        TableMatrixPlot.__init__(self, *args, **kwargs)
        SeabornPlot.__init__(self, *args, **kwargs)

    def addColourBar(self):
        pass

    def startPlot(self, **kwargs):

        # seaborn will create figure, so do not create one.
        self.mFigure += 1

    def plotMatrix(self, matrix, row_headers, col_headers,
                   vmin, vmax,
                   color_scheme=None):

        self.debug("plot matrix started")
        data = pandas.DataFrame(matrix,
                                columns=col_headers,
                                index=row_headers)
        statement = self.buildStatement(data, color_scheme)
        self.debug("seaborn: executing statement '%s'" % statement)
        plot = self.execute(statement, globals(), locals())
        self.debug("plot matrix finished")
        return plot


class HeatmapPlot(SeabornMatrixPlot):
    """Render a matrix as a heatmap using seaborn.
    """

    def buildStatement(self, data, color_scheme):
        return("plot = seaborn.heatmap(data, "
               "cmap=color_scheme)")


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

    def buildStatement(self, data, color_scheme):

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

        return("plot = seaborn.clustermap(data, "
               "cmap=color_scheme "
               "{})".format(extra_options))
