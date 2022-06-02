
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

        self.__journalInode = decoder.leBytesToDecimal(data, 224, 227)
        self.__groupDescriptorSize = decoder.leBytesToDecimal(data, 254, 255)
        self.__inodeSize = decoder.leBytesToDecimal(data, 88, 89)
        self.__inodesPerGroup = decoder.leBytesToDecimal(data, 40, 43)
        self.__blocksPerGroup = decoder.leBytesToDecimal(data, 32, 35)
        self.__blockSize = pow(2, (10 + decoder.leBytesToDecimal(data, 24, 27)))
        self.__numBlocks = decoder.leBytesToDecimal(data, 4, 7)
        self.__numInodes = decoder.leBytesToDecimal(data, 0, 3)
    

    # getters
    def getJournalInode(self):
        return self.__journalInode

    def getGroupDescriptorSize(self):
        return self.__groupDescriptorSize

    def getInodeSize(self):
        return self.__inodeSize
    
    def getInodesPerGroup(self):
        return self.__inodesPerGroup
    
    def getBlocksPerGroup(self):
        return self.__blocksPerGroup
    
    def getBlockSize(self):
        return self.__blockSize

    def getNumBlocks(self):
        return self.__numBlocks
    
    def getNumInodes(self):
        return self.__numInodes