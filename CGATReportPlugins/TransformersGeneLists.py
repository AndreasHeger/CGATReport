from CGATReportPlugins.Transformer import Transformer
from scipy.stats import *
from collections import OrderedDict as odict
from docutils.parsers.rst import directives
from CGATReport import Stats, DataTree, Utils
import itertools
import math


class TransformerHypergeometric(Transformer):

    '''Takes in lists of items (genes) and computes a hypergeometric p
    value and fold enrichment on the overlap between the lists.

    Takes bottom level of the data tree, which is expects to be a
    dictionary of lists, one of which should be named background. It
    will check if all the items in the other lists are also in the
    background list.

    If the dictionary contains more than 2 lists in addition to
    background, all pairwise overlaps are calculated.

    '''

    nlevels = 1

    def transform(self, data, path):

        keys = data.keys()
        if len(keys) < 3 or "background" not in data.keys():
            raise ValueError("Expected at least 3 lists, with one called background, instead got %i lists called %s" % (
                len(keys), ", ".join(keys)))

        keys = [x for x in keys if x != "background"]

        missing = {
            y: [str(x) for x in data[y] if x not in data["background"]] for y in keys}

        if any([len(missing[x]) > 0 for x in missing]):
            missing_items = "\n\t".join(
                ["%s:\t%s" % (x, ",".join(missing[x])) for x in missing])
            raise ValueError(
                "Found items in lists not in background. Missing items:\n\t %s" % missing_items)

        M = len(set(data["background"]))
        if len(keys) == 2:

            n = len(set(data[keys[1]]))
            N = len(set(data[keys[0]]))
            x = len(set(data[keys[0]]) & set(data[keys[1]]))

            p = hypergeom.sf(x, M, n, N)

            fc = ((x + 0.0) / N) / ((n + 0.0) / M)

            return odict([("Enrichment", fc), ("P-value", p)])
        else:
            enrichments = []
            pvals = []
            As = []
            Bs = []
            for a, b in itertools.combinations(keys, 2):
                N = len(set(data[a]))
                n = len(set(data[b]))
                x = len(set(data[a]) & set(data[b]))

                p = hypergeom.sf(x, M, n, N)

                fc = ((x + 0.0) / N) / ((n + 0.0) / M)

                As.append(a)
                Bs.append(b)
                pvals.append(p)
                enrichments.append(fc)

            return odict([("ListA", As),
                          ("ListB", Bs),
                          ("Enrichment", enrichments),
                          ("P-value", pvals)])


class TransformerOddsRatio(Transformer):

    ''' Takes in lists of items (genes) and computes a hypergeometric p value and fold enrichment
    on the overlap between the lists.

    Takes bottom level of the data tree, which is expects to be a dictionary of lists, one of which
    should be named background. It will check if all the items in the other lists are also in
    the background list.

    If the dictionary contains more than 2 lists in addition to background, all pairwise overlaps
    are calculated. '''

    nlevels = 1

    def transform(self, data):

        keys = data.keys()
        if len(keys) < 3 or "background" not in data.keys():
            raise ValueError("Expected at least 3 lists, with one called background, instead got %i lists called %s" % (
                len(keys), ", ".join(keys)))

        keys = [x for x in keys if x != "background"]

        missing = {
            y: [str(x) for x in data[y] if x not in data["background"]] for y in keys}

        if any([len(missing[x]) > 0 for x in missing]):

            missing_items = "\n\t".join(
                ["%s:\t%s" % (x, ",".join(missing[x])) for x in missing])

            raise ValueError(
                "Found items in lists not in background. Missing items:\n\t %s" % missing_items)

        if len(keys) == 2:

            a = len(set(data[keys[0]]) & set(data[keys[1]]))
            b = len(set(data[keys[0]]) - set(data[keys[1]]))
            c = len(set(data[keys[1]]) - set(data[keys[0]]))
            d = len(
                set(data["background"]) - set(data[keys[0]]) - set(data[keys[1]]))

            table = [[a, b], [c, d]]

            OR, p = fisher_exact(table)

            sigma = math.sqrt((1.0 / a) + (1.0 / b) + (1.0 / c) + (1.0 / d))

            CI95_hi = OR * math.exp(1.96 * sigma)
            CI95_low = OR * math.exp(-1.96 * sigma)

            return odict([("OddRatio", OR), ("CI95_hi", CI95_hi), ("CI95_low", CI95_low), ("P-value", p)])

        else:
            ORs = []
            pvals = []
            CIhis = []
            CIlos = []
            As = []
            Bs = []
            for x, z in itertools.combinations(keys, 2):

                a = len(set(data[x]) & set(data[z]))
                b = len(set(data[x]) - set(data[z]))
                c = len(set(data[z]) - set(data[x]))
                d = len(set(data["background"]) - set(data[x]) - set(data[z]))

                table = [[a, b], [c, d]]

                OR, p = fisher_exact(table)

                sigma = math.sqrt(
                    (1.0 / a) + (1.0 / b) + (1.0 / c) + (1.0 / d))

                CI95_hi = OR * math.exp(1.96 * sigma)
                CI95_low = OR * math.exp(-1.96 * sigma)

                As.append(x)
                Bs.append(z)
                pvals.append(p)
                ORs.append(OR)
                CIhis.append(CI95_hi)
                CIlos.append(CI95_low)

            return odict([("ListA", As),
                          ("ListB", Bs),
                          ("OddsRatio", ORs),
                          ("CI95_hi", CIhis),
                          ("CI95_low", CIlos),
                          ("P-value", pvals)])


class TransformerVenn(Transformer):
    '''Takes dictionarys of lists and transforms the data into the correct
    format for use with the venn renderer. If the dictionary contains
    a background entry and all other entries are subsets of the
    background, then it is removed, unless the keep-background options
    is specified.

    e.g.

    This:                           Becomes:
    a/x/[1,2,3]                     a/01/1
    a/y/[2,3,4]                     a/10/1
    a/background/[1,2,3,4,5]        a/11/2
    b/x/[5,6,7]                     b/01/1
    b/y/[6,7,8]                     b/10/1
                                    b/11/2

    Currently handles 2 or 3 way overlaps

    '''

    nlevels = 0

    options = Transformer.options + (
        ('keep-background', directives.flag),)

    background = False

    def __init__self(*args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        self.background = "keep-background" in kwargs

    def transform(self, data):

        if "background" in data and not self.background:
            del(data["background"])

        if len(data) == 2:
            results = dict()
            a = set(data[data.keys()[0]])
            b = set(data[data.keys()[1]])

            results["10"] = len(a - b)
            results["01"] = len(b - a)
            results["11"] = len(a & b)
            results["labels"] = data.keys()
            return results
        elif len(data) == 3:
            results = dict()
            a = set(data[data.keys()[0]])
            b = set(data[data.keys()[1]])
            c = set(data[data.keys()[2]])

            results["100"] = len(a - b - c)
            results["010"] = len(b - a - c)
            results["001"] = len(c - a - b)
            results["110"] = len((a & b) - c)
            results["101"] = len((a & c) - b)
            results["011"] = len((b & c) - a)
            results["111"] = len((a & b) & c)

            results["labels"] = data.keys()
            return results
        else:
            raise ValueError(
                "Can currently only cope with 2 or 3 way intersections")


class TransformerMultiTest(Transformer):

    ''' This transformer performs multiple testing correction. By default, it looks for a P-value entry at
    the lowest level and takes the P-values from there. This can be set with the p-value option. By default all
    p-values from all levels are corrected together. In order to change this behavoir use the adj-levels option.
    The original data tree is returned with an added P-adjust entry. The defualt method for correction is BH,
    but other R style correction methods can be specified with adj-method.

    NOTE: The order that items are grouped in the datatree are not the same as the grouping in rendering as default
    if adj-level is set to 2, then all values from each track are adjusted together, but rendering normally put all
    data of the same slice together.'''

    options = Transformer.options + (
        ('adj-level', directives.unchanged),
        ('adj-method', directives.unchanged),
        ('p-value', directives.unchanged),)

    def __init__(self, *args, **kwargs):
        Transformer.__init__(self, *args, **kwargs)

        self.nlevels = int(kwargs.get("adj-level", 0))

        self.method = kwargs.get("adj-method", "BH")
        self.pval = kwargs.get("p-value", "P-value")

    def __call__(self, data):

        if self.nlevels == 0:
            self.nlevels = len(DataTree.getPaths(data))

        return Transformer.__call__(self, data)

    def transform(self, data, path):

        from rpy2.robjects import r as R

        paths, lengths, values = [], [], []

        labels = DataTree.getPaths(data)
        paths = list(itertools.product(*labels[:-1]))

        for path in paths:

            work = DataTree.getLeaf(data, path)
            try:
                lengths.append(len(work[self.pval]))
                values.extend(work[self.pval])

            except TypeError:
                lengths.append(0)
                values.append(work[self.pval])

        padj = R["p.adjust"](values, method=self.method)

        padj = [x for x in padj]

        for path in paths:

            num = lengths.pop(0)

            if num > 0:
                new_values = padj[0:num]
                padj = padj[num:]
            else:
                new_values = padj[0]
                padj = padj[1:]

            if path:
                work = odict(DataTree.getLeaf(data, path))
                work["P-adjust"] = new_values
                DataTree.setLeaf(data, path, work)
            else:
                data["P-adjust"] = new_values

        return data
