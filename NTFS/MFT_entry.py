
import NTFS.boot_sector
import NTFS.MFT_attributes
import decode

class MFTEntry:

    def __init__(self, clusterNum, diskName, bootSector: NTFS.boot_sector.BootSector):

        offSet = (bootSector.sectorsPerCluster * clusterNum) * bootSector.sectorSize
        disk = open(diskName, "rb")
        disk.seek(offSet)
        data = disk.read(1024)

        self.header = MFTHeader(data)

        self.data
        self.fileName

        # I am not 100% sure it is indeed 56
        self.readAttributes(data[56:])


    def readAttributes(self, data: bytes):
        decoder = decode.Decoder()

        currentByte = 0
        while currentByte < len(data):
            attributeType = decoder.leBytesToDecimal(data, currentByte, currentByte + 3)
            if attributeType == 48:
                self.fileName = NTFS.MFT_attributes.FileName()
                # this line below may be wrong
                currentByte += 65 + self.fileName.lenName
            elif attributeType == 128:
                self.data = NTFS.MFT_attributes.Data()
                # this 0 is a placeholder until I figure out what this increment shall be
                currentByte += 0

class MFTHeader:

    def __init__(self, data: bytes):
        decoder = decode.Decoder()
        self.isDeleted = False
        statusFlag = decoder.leBytesToDecimal(data, 22, 23)
        if statusFlag == 0:
            self.isDeleted = True
