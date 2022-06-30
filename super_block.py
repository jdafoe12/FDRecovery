
import decode
import disks


class SuperBlock:

    """
    Contains data associated with the super block for the filesystem

    Attributes
    ----------
    inodeSize : int
        The size in bytes of the inode metadata structure in the filesystem
    inodesPerGroup : int
        The number of inodes per group in the filesystem
    blocksPerGroup : int
        The number of blocks per group in the filesystem
    blockSize : int
        The size in bytes of blocks in the filesystem
    numBlocks : int
        The number of blocks in the filesystem
    numInodes : int
        The number of inodes in the filesystem
    hasExtent : boolean
        If the filesystem type is ext4, the extent feature needs to be checked
        to understand whether to read extents or block pointers
    bit64 : boolean
        Indicates whether the 64bit flag is set
    """

    def __init__(self, diskO: disks.Disk):

        """
        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem
        """

        # read the data
        disk = open(diskO.diskPath, "rb")
        disk.seek(1024)
        data = disk.read(1024)
        disk.close

        # interpret the data
        decoder = decode.Decoder()

        if diskO.diskType == "ext4" or diskO.diskType == "ext3":
            self.journalInode: int = decoder.leBytesToDecimal(data, 224, 227)
            self.bit64 = data[0x60] & 0b00010000 == 0b00010000

        if diskO.diskType == "ext4":
            self.hasExtent = (data[0x60] & 0b00000010) == 0b00000010
            self.groupDescriptorSize: int = decoder.leBytesToDecimal(data, 254, 255)

        elif diskO.diskType == "ext3" or diskO.diskType == "ext2":
            self.groupDescriptorSize: int = 32

        self.inodeSize: int = decoder.leBytesToDecimal(data, 88, 89)
        self.inodesPerGroup: int = decoder.leBytesToDecimal(data, 40, 43)
        self.blocksPerGroup: int = decoder.leBytesToDecimal(data, 32, 35)
        self.blockSize: int = pow(2, (10 + decoder.leBytesToDecimal(data, 24, 27)))
        self.numBlocks: int = decoder.leBytesToDecimal(data, 4, 7)
        self.numInodes: int = decoder.leBytesToDecimal(data, 0, 3)

        if self.inodeSize != 256:
            self.inodeSize == 128