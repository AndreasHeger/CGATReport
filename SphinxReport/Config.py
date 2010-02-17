from SphinxReport import Transformer, Renderer

from docutils.parsers.rst import directives
try:
    # docutils 0.4
    from docutils.parsers.rst.directives.images import align
except ImportError:
    # docutils 0.5
    from docutils.parsers.rst.directives.images import Image
    align = Image.align

# Map transformer names to their implementations.
MAP_TRANSFORMER = { 
    'stats' : Transformer.TransformerStats, 
    'correlation' : Transformer.TransformerCorrelationPearson,
    'pearson' : Transformer.TransformerCorrelationPearson,
    'spearman' : Transformer.TransformerCorrelationSpearman, 
    'histogram' : Transformer.TransformerHistogram,
    'filter' : Transformer.TransformerFilter,
    'select' : Transformer.TransformerSelect,
    'combinations': Transformer.TransformerCombinations,
    'combine': Transformer.TransformerCombinations,
    }

# Map renderer names to their implemenations
MAP_RENDERER= { 
    'debug' : Renderer.RendererDebug,
    'line-plot': Renderer.RendererLinePlot,
    'histogram-plot' : Renderer.RendererHistogramPlot,
    'pie-plot': Renderer.RendererPiePlot,
    'scatter-plot': Renderer.RendererScatterPlot,
    'scatter-rainbow-plot': Renderer.RendererScatterPlotWithColor,
    'table': Renderer.RendererTable,
    'matrix': Renderer.RendererMatrix,
    'matrix-plot': Renderer.RendererMatrixPlot,
    'hinton-plot': Renderer.RendererHintonPlot,
    'bar-plot': Renderer.RendererBarPlot,
    'stacked-bar-plot': Renderer.RendererStackedBarPlot,
    'interleaved-bar-plot': Renderer.RendererInterleavedBarPlot,
    'box-plot': Renderer.RendererBoxPlot,
    'glossary' : Renderer.RendererGlossary 
}

DISPLAY_OPTIONS = {
    'alt': directives.unchanged,
    'height': directives.length_or_unitless,
    'width': directives.length_or_percentage_or_unitless,
    'scale': directives.nonnegative_int,
    'align': align,
    'class': directives.class_option,
    'render' : directives.unchanged,
    'transform' : directives.unchanged,
    'include-source': directives.flag 
    }

DISPATCHER_OPTIONS = {
    'groupby' : directives.unchanged,
    'tracks': directives.unchanged,
    'slices': directives.unchanged,
    }

RENDER_OPTIONS = { 
    'layout' : directives.unchanged,
    'error' : directives.unchanged,
    'label' : directives.unchanged,
    'logscale' : directives.unchanged,
    'title' : directives.unchanged,
    'add-title' : directives.flag,
    'xtitle' : directives.unchanged,
    'ytitle' : directives.unchanged,
    'xrange' : directives.unchanged,
    'yrange' : directives.unchanged,
    'zrange' : directives.unchanged,
    'palette' : directives.unchanged,
    'reverse-palette' : directives.flag,
    'transpose' : directives.flag,
    'transform-matrix' : directives.unchanged,
    'as-lines': directives.flag,  
    'format' : directives.unchanged,
    'colorbar-format' : directives.unchanged,
    'filename' : directives.unchanged,
    'pie-min-percentage' : directives.unchanged,
    'max-rows' : directives.unchanged,
    'max-cols' : directives.unchanged,
    'mpl-figure' : directives.unchanged,
    'mpl-legend' : directives.unchanged,
    'mpl-subplot' : directives.unchanged,
    'mpl-rc' : directives.unchanged, 
}

TRANSFORM_OPTIONS = {
    'tf-fields' : directives.unchanged,
    'tf-level' : directives.length_or_unitless,
    'tf-bins' : directives.unchanged,
    'tf-range' : directives.unchanged,
    'tf-aggregate': directives.unchanged,
    }

SEPARATOR="@"

HTML_IMAGE_FORMAT = ('main', 'png', 80)
LATEX_IMAGE_FORMAT = () # ('pdf', 'pdf' 50)

ADDITIONAL_FORMATS = [
    ('hires', 'hires.png', 200 ),
    # ('pdf', 'pdf', 50 ),
    ]

