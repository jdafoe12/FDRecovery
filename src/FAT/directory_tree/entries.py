
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

        self.isDir: bool = attributes[0] & 0b00010000 == 0b0001000

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


class FAT32Entry:
    def __init__(self, data: bytes):
        self.isLongName = data[0x0B] & 0b00001111 == 0b00001111
        self.name = ""
        if self.isLongName:
            self.name = data[0x01 : 0x0B].decode(encoding="utf-16", errors="strict")
            self.name = self.name + data[0x0E : 0x1A].decode(encoding="utf-16", errors="strict")
            self.name = self.name + data[0x1C : ].decode(encoding="utf-16", errors="strict")
        else:
            # read all important short name stuffs
            decoder = common.decode.Decoder

            self.isDeleted = data[0] == 0xE5
            attributes = data[0x0B]
            self.isDir = attributes & 0b00010000 == 0b00010000
            self.volLabelFlag = attributes & 0b00001000 == 0b00001000
            self.dataLen = decoder.leBytesToDecimal(self, data, 0x1C, 0x1F)
            self.startingClust = decoder.leBytesToDecimalLowerAndUpper(self, data, 0x1A, 0x1B, 0x14, 0x15)
            self.name = data[0x01 : 0x0B].decode()
