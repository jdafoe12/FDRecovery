

import decode
import disks
import super_block


class GroupDescriptor:

    """
    Contains data associated with a group descriptor.

    Attributes
    ----------
    inodeTableLoc : int
        The block number containing the first block in the inode table for the
        filesystem group associated with the group descriptor.
    inodeBitMapLoc : int
        The block number containing the block for the inode bitmap for the
        filesystem group associated with the group descriptor.
    """


    def __init__(self, diskO: disks.Disk, groupNum: int, superBlock: super_block.SuperBlock):

        """
        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem
            which contains the group descriptor being read
        groupNum : int
            The filesystem group number associated with the group descriptor
            This is necessary to locate the correct group descriptor
        superBlock : super_block.SuperBlock
            The super block associated with the filesystem
            This is necessary to locate the location of the group descriptor on disk
        """

        groupDescriptorTableOffSet = (superBlock.blockSize * (superBlock.blocksPerGroup + 1))
        groupOffSet = groupNum * superBlock.groupDescriptorSize

        disk = open(diskO.diskPath, "rb")
        disk.seek(groupDescriptorTableOffSet + groupOffSet)
        data = disk.read(superBlock.groupDescriptorSize)

        decoder = decode.Decoder()


        # set group descriptor data fields

        if diskO.diskType == "ext4":
            self.inodeTableLoc: int = decoder.leBytesToDecimalLowerAndUpper(data, 8, 11, 40, 43)
            self.inodeBitMapLoc: int = decoder.leBytesToDecimalLowerAndUpper(data, 4, 7, 36, 39)
            self.blockBitMapLoc: int = decoder.leBytesToDecimalLowerAndUpper(data, 0, 3, 32, 35)
            
        elif diskO.diskType == "ext3" or diskO.diskType == "ext2":
            self.inodeTableLoc: int = decoder.leBytesToDecimal(data, 8, 11)
            self.inodeBitMapLoc: int = decoder.leBytesToDecimal(data, 4, 7)
            self.blockBitMapLoc: int = decoder.leBytesToDecimal(data, 0, 3)

