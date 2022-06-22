
import decode
import super_block


class GroupDescriptor:

    def __init__(self, diskO, groupNum, superBlock: super_block.SuperBlock):

        groupDescriptorTableOffSet = (superBlock.blockSize * (superBlock.blocksPerGroup + 1))
        groupOffSet = groupNum * superBlock.groupDescriptorSize

        disk = open(diskO.diskPath, "rb")
        disk.seek(groupDescriptorTableOffSet + groupOffSet)
        data = disk.read(superBlock.groupDescriptorSize)

        decoder = decode.Decoder()


        # set group descriptor data fields

        if diskO.diskType == "ext4":
            self.inodeTableLoc = decoder.leBytesToDecimalLowerAndUpper(data, 8, 11, 40, 43)
            self.inodeBitMapLoc = decoder.leBytesToDecimalLowerAndUpper(data, 4, 7, 36, 39)
            self.blockBitMapLoc = decoder.leBytesToDecimalLowerAndUpper(data, 0, 3, 32, 35)
            
        elif diskO.diskType == "ext3" or diskO.diskType == "ext2":
            self.inodeTableLoc = decoder.leBytesToDecimal(data, 8, 11)
            self.inodeBitMapLoc = decoder.leBytesToDecimal(data, 4, 7)
            self.blockBitMapLoc = decoder.leBytesToDecimal(data, 0, 3)

