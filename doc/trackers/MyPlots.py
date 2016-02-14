
import numpy as np
import matplotlib.pyplot as plt
from CGATReport.ResultBlock import ResultBlock, ResultBlocks
from collections import OrderedDict as odict

def ExampleWithoutData():
    '''example taken from matplotlib gallery.'''
    N = 5
    menMeans = (20, 35, 30, 35, 27)
    womenMeans = (25, 32, 34, 20, 25)
    menStd = (2, 3, 4, 1, 2)
    womenStd = (3, 5, 2, 3, 3)
    ind = np.arange(N)    # the x locations for the groups
    width = 0.35       # the width of the bars: can also be len(x) sequence

    p1 = plt.bar(ind, menMeans,   width, color='r', yerr=womenStd)
    p2 = plt.bar(ind, womenMeans, width, color='y',
                 bottom=menMeans, yerr=menStd)

    plt.ylabel('Scores')
    plt.title('Scores by group and gender')
    plt.xticks(ind + width / 2., ('G1', 'G2', 'G3', 'G4', 'G5'))
    plt.yticks(np.arange(0, 81, 10))
    plt.legend((p1[0], p2[0]), ('Men', 'Women'))

    # return a place holder for this figure
    return ResultBlocks(
        ResultBlock("#$mpl 1$#\n", ""),
        title="MyTitle")


def ExampleData1():
    return odict((
        ("menMeans", (20, 35, 30, 35, 27),),
        ("womenMeans", (25, 32, 34, 20, 25),),
        ("menStd", (2, 3, 4, 1, 2),),
        ("womenStd", (3, 5, 2, 3, 3)),))


def ExampleData2():
    return odict((
        ("menMeans", (30, 25, 20, 25, 17),),
        ("womenMeans", (15, 12, 24, 10, 15),),
        ("menStd", (2, 1, 2, 1, 2),),
        ("womenStd", (1, 2, 2, 4, 3)),))


def ExampleWithData(data, path):
    '''modified example from matplotlib gallery.'''

    # skip the uppermost levels as we have no
    # tracks or slices
    N = 5
    ind = np.arange(N)    # the x locations for the groups
    width = 0.35       # the width of the bars: can also be len(x) sequence
    
    ax = plt.figure()
    p1 = plt.bar(ind,
                 data["menMeans"],
                 width,
                 color='r',
                 yerr=data["womenStd"])
    p2 = plt.bar(ind,
                 data["womenMeans"],
                 width,
                 color='y',
                 bottom=data["menMeans"],
                 yerr=data["menStd"])

    plt.ylabel('Scores')
    plt.title('Scores by group and gender')
    plt.xticks(ind + width / 2., ('G1', 'G2', 'G3', 'G4', 'G5'))
    plt.yticks(np.arange(0, 81, 10))
    plt.legend((p1[0], p2[0]), ('Men', 'Women'))

    # return a place holder for this figure
    return ResultBlocks(
        ResultBlock("#$mpl 1$#\n", ""),
        title="MyTitle")
