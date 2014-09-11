from CGATReport.Tracker import Tracker
from CGATReport.DataTypes import returnLabeledData, returnSingleColumnData, returnMultipleColumnData, returnMultipleColumns


class SingleColumnDataExample(Tracker):
    mData = (1, 2, 3)

    def getTracks(self):
        return "track1", "track2"

    @returnSingleColumnData
    def __call__(self, track, slice=None):
        if track == "track1":
            return self.mData * 1
        elif track == "track2":
            return self.mData * 2


class SingleColumnDataExample2(SingleColumnDataExample):
    mData = (10, 20, 30)


@returnSingleColumnData
def FunctionExample1():
    return (1, 2, 3)


@returnSingleColumnData
def FunctionExample2():
    return (4, 5, 6)

if __name__ == "__main__":

    print (list(SingleColumnDataExample()("track1")))
    print (list(SingleColumnDataExample()("track2")))
    print (list(SingleColumnDataExample()("track1")))

    a = SingleColumnDataExample()
    print (list(a("track1")))
    print (list(a("track2")))
    print (list(a("track1")))

    print (list(SingleColumnDataExample2()("track1")))
    print (list(SingleColumnDataExample2()("track2")))
    print (list(SingleColumnDataExample2()("track1")))

    a = SingleColumnDataExample2()
    print (list(a("track1")))
    print (list(a("track2")))
    print (list(a("track1")))

    print (list(FunctionExample1()))

    print (list(FunctionExample2()))
