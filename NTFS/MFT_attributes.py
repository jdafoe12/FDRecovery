

import sys

sys.path.insert(0, "C:/Users/jwdaf/Data_Recovery/DataRecovery/Common")
import decode


class Data:

    def __init__(self, data: bytes, startByte, attributeSize):
        decoder = decode.Decoder()
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
        decoder = decode.Decoder()
        numClustBytes = (data[index] & 0xF0) >> 4
        numLenBytes = data[index] & 0x0F
        self.byteSize = numClustBytes + numLenBytes + 1

        self.numClusters = decoder.leBytesToDecimal(data, index + 1, index + numLenBytes)
        self.startingCluster = int.from_bytes(bytes=data[index + 1 + numLenBytes : index + numLenBytes + numClustBytes + 1], byteorder="little", signed=True)


class FileName:

    def __init__(self, data: bytes, startByte):
        self.name: str = ""

        # I should verify this number
        self.lenName = data[startByte + 88]

        self.name = self.name + data[startByte + 90 : startByte + 90 + (self.lenName * 2)].decode("utf-16", "strict")
