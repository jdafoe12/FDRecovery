
from Decoder import Decoder
from SuperBlock import SuperBlock


class GroupDescriptor:

    def __init__(self, diskName, groupNum, superBlock: SuperBlock):

        groupDescriptorTableOffSet = (superBlock.getBlockSize() * (superBlock.getBlocksPerGroup() + 1))
        groupOffSet = groupNum * superBlock.getGroupDescriptorSize()

        disk = open(diskName, "rb")
        disk.seek(groupDescriptorTableOffSet + groupOffSet)
        data = disk.read(superBlock.getGroupDescriptorSize())

        decoder = Decoder()

        # set group descriptor data fields
        self.__inodeTableLoc = decoder.leBytesToDecimalLowerAndUpper(data, 8, 11, 40, 43)
        self.__inodeBitMapLoc = decoder.leBytesToDecimalLowerAndUpper(data, 4, 7, 36, 39)
        self.__blockBitMapLoc = decoder.leBytesToDecimalLowerAndUpper(data, 0, 3, 32, 35)

    def getInodeTableLoc(self):
        return self.__inodeTableLoc

    def getInodeBitMapLoc(self):
        return self.__inodeBitMapLoc

    def getBlockBitMapLoc(self):
        return self.__blockBitMapLoc
