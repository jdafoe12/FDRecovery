
from src import common
from src.FAT.structures import disks

class BootSector:
    def __init__(self, diskO: disks.Disk):

        decoder = common.decode.Decoder()

        disk = open(diskO.diskPath, "rb")
        data = disk.read(512)
        disk.close

        if diskO.diskType == "EXFA":
            self.fatOffset = decoder.leBytesToDecimal(data, 0x50, 0x53)
            self.clusterHeapOffset = decoder.leBytesToDecimal(data, 0x58, 0x5B)
            self.rootDirectoryCluster = decoder.leBytesToDecimal(data, 0x60, 0x63)
            self.bytesPerSector = pow(2, decoder.leBytesToDecimal(data, 0x6C, 0x6C))
            self.sectorsPerCluster = pow(2, decoder.leBytesToDecimal(data, 0x6D, 0x6D))
        elif diskO.diskType == "FAT32":
            self.bytesPerSector = decoder.leBytesToDecimal(data, 0x0B, 0x0C)
            self.sectorsPerCluster = decoder.leBytesToDecimal(data, 0x0D, 0x0D)
            self.reservedSectors = decoder.leBytesToDecimal(data, 0x0E, 0x0F)
            self.numFATs = decoder.leBytesToDecimal(data, 0x10, 0x10)
            self.sectorsPerFAT = decoder.leBytesToDecimal(data, 0x24, 0x27)
            self.rootDirectoryCluster = 2