

from src import common


class Data:

    def __init__(self, data: bytes, startByte, attributeSize):
        decoder = common.decode.Decoder()
        self.isResident = False
        if decoder.leBytesToDecimal(data, startByte + 8, startByte + 8) == 0:
            self.isResident = True

        self.dataRuns = []
        currentIndex = decoder.leBytesToDecimal(data, startByte + 32, startByte + 32) + startByte
        while currentIndex - startByte < attributeSize:
            self.dataRuns.append(DataRun(data, currentIndex))
            if self.dataRuns[-1].byteSize > 1:
                currentIndex += self.dataRuns[-1].byteSize
            else:
                self.dataRuns.pop()
                break




class DataRun:

    def __init__(self, data, index):
        decoder = common.decode.Decoder()
        numClustBytes = (data[index] & 0xF0) >> 4
        numLenBytes = data[index] & 0x0F
        self.byteSize = numClustBytes + numLenBytes + 1

        self.numClusters = decoder.leBytesToDecimal(data, index + 1, index + numLenBytes)
        self.startingCluster = int.from_bytes(bytes=data[index + 1 + numLenBytes : index + numLenBytes + numClustBytes + 1], byteorder="little", signed=True)


class FileName:

    def __init__(self, data: bytes, startByte):

        decoder = common.decode.Decoder()

        header = AttributeHeader(data, startByte)


        self.name = ""

        self.lenName = data[startByte + (header.offSetToAttribute + 0x40)]
        try:
            self.name = data[startByte + (header.offSetToAttribute + 0x42) : startByte + (header.offSetToAttribute + 0x42) + (self.lenName * 2)].decode(encoding="utf-16", errors="strict")
        except UnicodeDecodeError:
            self.name = False

class AttributeHeader:

    def __init__(self, data: bytes, startByte):

        decoder = common.decode.Decoder()

        isResident = data[startByte + 8] == 0

        self.length = decoder.leBytesToDecimal(data, startByte + 4, startByte + 5)
        if isResident:
            self.offSetToAttribute = decoder.leBytesToDecimal(data, startByte + 0x14, startByte + 0x15)

        elif not isResident:
            self.offSetToAttribute = decoder.leBytesToDecimal(data, startByte + 0x20, startByte + 0x21)
