from Decoder import Decoder

class ExtentNode:
    def __init__(self, data):

        self.header = ExtentHeader(data[0:12])

        self.entries: list[ExtentEntry] = list()
        self.indices: list[ExtentIndex] = list()

        if self.header.extentDepth > 0:
            for i in range(0, self.header.numEntriesInExtent):
                
                self.indices.append(ExtentIndex(data[12 + (12 * i):(12 + (12 * i)) + 12]))
                
        else:
            for i in range(0, self.header.numEntriesInExtent):
                self.entries.append(ExtentEntry(data[12 + (12 * i):(12 + (12 * i)) + 12]))

        
class ExtentHeader:
    def __init__(self, data):

        decoder = Decoder()

        self.numEntriesInExtent = decoder.leBytesToDecimal(data, 2, 3)
        self.maxEntries = decoder.leBytesToDecimal(data, 4, 5)
        self.extentDepth = decoder.leBytesToDecimal(data, 6, 7)


class ExtentEntry:
    def __init__(self, data):

        decoder = Decoder()

        self.fileBlockNum = decoder.leBytesToDecimal(data, 0, 3)
        self.numBlocks = decoder.leBytesToDecimal(data, 4, 5)
        self.blockNum = decoder.leBytesToDecimalLowerAndUpper(data, 8, 11, 6, 7) 


class ExtentIndex:
    def __init__(self, data):

        decoder = Decoder()

        self.fileBlockNum = decoder.leBytesToDecimal(data, 0, 3)
        self.nextNodeBlockNum = decoder.leBytesToDecimalLowerAndUpper(data, 4, 7, 8, 9)