
from Decoder import Decoder


class SuperBlock:   

    def __init__(self, diskName):

        # read the data
        disk = open(diskName, "rb")
        disk.seek(1024)
        data = disk.read(1024)
        disk.close

        # interpret the data
        decoder = Decoder()

        self.journalInode = decoder.leBytesToDecimal(data, 224, 227)
        self.groupDescriptorSize = decoder.leBytesToDecimal(data, 254, 255)
        self.inodeSize = decoder.leBytesToDecimal(data, 88, 89)
        self.inodesPerGroup = decoder.leBytesToDecimal(data, 40, 43)
        self.blocksPerGroup = decoder.leBytesToDecimal(data, 32, 35)
        self.blockSize = pow(2, (10 + decoder.leBytesToDecimal(data, 24, 27)))
        self.numBlocks = decoder.leBytesToDecimal(data, 4, 7)
        self.numInodes = decoder.leBytesToDecimal(data, 0, 3)