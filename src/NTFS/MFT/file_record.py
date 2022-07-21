

from src.NTFS import structures
from src.NTFS import MFT
from src import common

class FileRecord:

    def __init__(self, data: bytes, bootSector: structures.boot_sector.BootSector, readPointers: bool, readAllAttr: bool):

        self.header = RecordHeader(data)
        self.data: MFT.record_attributes.Data = False
        self.fileName: MFT.record_attributes.FileName = False

        if self.header.isDeleted or readAllAttr:
            self.readAttributes(data[self.header.length:], readPointers)


    def readAttributes(self, data: bytes, readPointers: bool):
        decoder = common.decode.Decoder()

        currentByte = 0
        while currentByte + 7 < len(data):
            attributeType = decoder.leBytesToDecimal(data, currentByte, currentByte + 3)
            attributeSize = decoder.leBytesToDecimal(data, currentByte + 4, currentByte + 7)
            if attributeType == 48:
                self.fileName = MFT.record_attributes.FileName(data, currentByte)
                if self.fileName.name == False:
                    self.fileName = False
            elif attributeType == 128 and readPointers:
                self.data = MFT.record_attributes.Data(data, currentByte, attributeSize)
            elif attributeType > 256:
                break
            elif self.fileName is not False and readPointers is False:
                break
            elif self.data is not False and self.fileName is not False:
                break
            if attributeSize == 0:
                break
            currentByte += attributeSize

class RecordHeader:

    def __init__(self, data: bytes):
        decoder = common.decode.Decoder()

        self.length = decoder.leBytesToDecimal(data, 20, 20)
        self.isDeleted = False
        flags = []
        
        flags.extend(data[22:24])
        flags = flags[0]
        if (data[22]) == 0:
            self.isDeleted = True



