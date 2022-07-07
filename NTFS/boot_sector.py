import decode

class BootSector:

    def __init__(self, diskName):
        
        decoder = decode.Decoder()

        disk = open(diskName, "rb")
        data = disk.read(512)
        disk.close

        self.sectorSize = decoder.leBytesToDecimal(data, 0x0B, 0x0C)
        self.sectorsPerCluster = decoder.leBytesToDecimal(data, 0x0D, 0x0E)
        self.MFTClusterNum = decoder.leBytesToDecimal(data, 0x30, 0x37)