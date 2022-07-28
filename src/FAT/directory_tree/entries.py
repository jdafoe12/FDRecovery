
from src import common

class FileDirEntry:
    def __init__(self, data):

        decoder = common.decode.Decoder

        if data[0] == 0x85:
            self.isInUse = True
        elif data[0] == 0x05:
            self.isInUse = False

        self.numSeconds = decoder.leBytesToDecimal(self, data, 1, 1)

        attributes = data[4:6]

        self.isDir: bool = attributes[0] & 0b00010000 == 0b00010000
        print(self.isDir)

class StreamExtEntry:

    def __init__(self, data):
        
        decoder = common.decode.Decoder

        flags = data[1]
        self.hasFatChain = flags & 0b01 != 0b01
        self.nameLen = decoder.leBytesToDecimal(self, data, 3, 3)
        self.firstCluster = decoder.leBytesToDecimal(self, data, 20, 23)
        self.dataLen = decoder.leBytesToDecimal(self, data, 24, 31)


class NameEntry:

    def __init__(self, data: bytes, nameLen):
        if nameLen == 30:
            self.name = bytes(data[2:]).decode(encoding="utf-16", errors="strict")
        else:
            self.name = bytes(data[2:(nameLen * 2) + 2]).decode(encoding="utf-16", errors="strict")