
from src import common

class BootSector:
    def __init__(self, diskName):

        decoder = common.decode.Decoder()

        disk = open(diskName, "rb")
        data = disk.read(512)
        disk.close

        self.fatOffset = decoder.leBytesToDecimal(data, 0x50, 0x53)
        self.clusterHeapOffset = decoder.leBytesToDecimal(data, 0x58, 0x5B)
        self.rootDirectoryCluster = decoder.leBytesToDecimal(data, 0x60, 0x63)
        self.bytesPerSector = pow(2, decoder.leBytesToDecimal(data, 0x6C, 0x6C))
        self.sectorsPerCluster = pow(2, decoder.leBytesToDecimal(data, 0x6D, 0x6D))