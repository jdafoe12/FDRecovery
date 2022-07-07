
import sys

sys.path.insert(0, "C:/Users/jwdaf/Data_Recovery/DataRecovery/Common")

import boot_sector
import MFT_attributes
import decode
import disks

class MFTEntry:

    def __init__(self, clusterNum, sectorOffset, diskName, bootSector: boot_sector.BootSector, readPointers: bool):

        offSet = ((bootSector.sectorsPerCluster * clusterNum) + sectorOffset) * bootSector.sectorSize
        disk = open(diskName, "rb")
        disk.seek(offSet)
        data = disk.read(1024)

        self.header = MFTHeader(data)

        self.data = ""
        self.fileName = ""

        # I am not 100% sure it is indeed 56
        self.readAttributes(data[self.header.length:], readPointers)


    def readAttributes(self, data: bytes, readPointers: bool):
        decoder = decode.Decoder()

        currentByte = 0
        while currentByte + 3 < len(data):
            attributeType = decoder.leBytesToDecimal(data, currentByte, currentByte + 3)
            attributeSize = decoder.leBytesToDecimal(data, currentByte + 4, currentByte + 7)
            if attributeType == 48:
                self.fileName = MFT_attributes.FileName(data, currentByte)
            elif attributeType == 128 and readPointers:
                self.data = MFT_attributes.Data(data, currentByte, attributeSize)
            elif attributeType > 256:
                break
            currentByte += attributeSize

class MFTHeader:

    def __init__(self, data: bytes):
        decoder = decode.Decoder()

        self.length = decoder.leBytesToDecimal(data, 20, 20)
        self.isDeleted = False
        statusFlag = decoder.leBytesToDecimal(data, 22, 23)
        if statusFlag == 0:
            self.isDeleted = True



