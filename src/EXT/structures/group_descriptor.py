

from src import common
from src.EXT.structures import disks, super_block


class GroupDescriptor:

    """
    Contains data associated with a group descriptor. Represents struct group_desc

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
        # A byte offset from the start of disk to the first block (in group 1) containing group descriptors.
        groupDescriptorTableOffSet = (superBlock.blockSize * (superBlock.blocksPerGroup + 1))

        groupOffSet = groupNum * superBlock.groupDescriptorSize

        disk = open(diskO.diskPath, "rb")
        disk.seek(groupDescriptorTableOffSet + groupOffSet)
        data = disk.read(superBlock.groupDescriptorSize)

        decoder = common.decode.Decoder()

        # set group descriptor data fields.

        # In ext4, there are two fields for each of these values, lower order and higher order bytes.
        if diskO.diskType == "ext4" and superBlock.groupDescriptorSize == 64:
            self.inodeTableLoc: int = decoder.leBytesToDecimalLowerAndUpper(data, 8, 11, 40, 43)
            self.inodeBitMapLoc: int = decoder.leBytesToDecimalLowerAndUpper(data, 4, 7, 36, 39)
            self.blockBitMapLoc: int = decoder.leBytesToDecimalLowerAndUpper(data, 0, 3, 32, 35)

        # In ext2/3, there is only one field for each of these values
        elif diskO.diskType == "ext3" or diskO.diskType == "ext2" or (diskO.diskType == "ext4" and not superBlock.bit64):
            self.inodeTableLoc: int = decoder.leBytesToDecimal(data, 8, 11)
            self.inodeBitMapLoc: int = decoder.leBytesToDecimal(data, 4, 7)
            self.blockBitMapLoc: int = decoder.leBytesToDecimal(data, 0, 3)
