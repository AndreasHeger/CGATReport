import sys

import matplotlib
matplotlib.use(sys.argv[1])
import pandas
import numpy
import matplotlib.pyplot as plt
from matplotlib import _pylab_helpers
import timeit

datapoints = int(sys.argv[2])
figures = 10

backend = matplotlib.get_backend()

for figure in range(figures):
    df = pandas.DataFrame(numpy.random.rand(datapoints, 2),
                          columns=['a', 'b'])

    df.plot.scatter(x='a', y='b')

def write_png(dpi):

    fig_managers = _pylab_helpers.Gcf.get_all_fig_managers()

    # create all required images
    for figman in fig_managers:

        # create all images
        figid = figman.num

        # select the correct figure
        figure = plt.figure(figid)

        outpath = "test_writing_%i.jpg" % figid
        figman.canvas.figure.savefig(outpath, dpi=dpi)


if __name__ == '__main__':
    import timeit
    for dpi in [50, 100, 200, 300, 400]:
        print(("\t".join(map(
            str,
            (backend, dpi, timeit.timeit(
            "write_png(dpi={})".format(dpi),
            setup="from __main__ import write_png",
                number=3))))))
