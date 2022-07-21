


from src import common

from src.EXT import structures


class SuperBlock:

    """
    Contains data associated with the super block for the filesystem.
    Represents struct super_block

    Attributes
    ----------
    inodeSize : int
        The size in bytes of the inode metadata structure in the filesystem.
    inodesPerGroup : int
        The number of inodes per group in the filesystem.
    blocksPerGroup : int
        The number of blocks per group in the filesystem.
    blockSize : int
        The size in bytes of blocks in the filesystem.
    numBlocks : int
        The number of blocks in the filesystem.
    numInodes : int
        The number of inodes in the filesystem.
    hasExtent : boolean
        If the filesystem type is ext4, the extent feature needs to be checked
        to understand whether to read extents or block pointers.
    bit64 : boolean
        Indicates whether the 64bit flag is set.
    """

    def __init__(self, diskO: structures.disks.Disk):

        """
        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem.
        """

        disk = open(diskO.diskPath, "rb")
        disk.seek(1024)
        data = disk.read(1024)
        disk.close

        decoder = common.decode.Decoder()

        # ext3/4 Both have journals (therefore a journalInode field), and the 64bit feature flag .
        # used when reading journal descriptor blocks.
        if diskO.diskType == "ext4" or diskO.diskType == "ext3":
            self.journalInode: int = decoder.leBytesToDecimal(data, 224, 227)
            self.bit64 = data[0x60] & 0b00010000 == 0b00010000

        # ext4 has a group descriptor size specified in the super block.
        if diskO.diskType == "ext4":
            self.hasExtent = (data[0x60] & 0b00000010) == 0b00000010
            self.groupDescriptorSize: int = decoder.leBytesToDecimal(data, 254, 255)
        # the group descriptor size for ext2 is always 32 bytes.
        elif diskO.diskType == "ext3" or diskO.diskType == "ext2":
            self.groupDescriptorSize: int = 32

        self.inodeSize: int = decoder.leBytesToDecimal(data, 88, 89)
        self.inodesPerGroup: int = decoder.leBytesToDecimal(data, 40, 43)
        self.blocksPerGroup: int = decoder.leBytesToDecimal(data, 32, 35)
        self.blockSize: int = pow(2, (10 + decoder.leBytesToDecimal(data, 24, 27)))
        self.numBlocks: int = decoder.leBytesToDecimal(data, 4, 7)
        self.numInodes: int = decoder.leBytesToDecimal(data, 0, 3)

        # 256 and 128 are the only possible inode sizes. 
        # Sometimes, this field may not be set in the super block. In that case it is 128.
        if self.inodeSize != 256:
            self.inodeSize == 128

        