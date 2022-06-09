
from Decoder import Decoder
from SuperBlock import SuperBlock


class GroupDescriptor:

    def __init__(self, diskName, groupNum, superBlock: SuperBlock):

        groupDescriptorTableOffSet = (superBlock.blockSize * (superBlock.blocksPerGroup + 1))
        groupOffSet = groupNum * superBlock.groupDescriptorSize

        disk = open(diskName, "rb")
        disk.seek(groupDescriptorTableOffSet + groupOffSet)
        data = disk.read(superBlock.groupDescriptorSize)

        decoder = Decoder()

        # set group descriptor data fields
        self.inodeTableLoc = decoder.leBytesToDecimalLowerAndUpper(data, 8, 11, 40, 43)
        self.inodeBitMapLoc = decoder.leBytesToDecimalLowerAndUpper(data, 4, 7, 36, 39)
        self.blockBitMapLoc = decoder.leBytesToDecimalLowerAndUpper(data, 0, 3, 32, 35)

