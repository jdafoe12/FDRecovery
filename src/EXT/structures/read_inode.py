

from src import common
from src.EXT.structures import super_block, disks, group_descriptor, extent_node


class Inode:

    """
    Reads and stores all necessary inode metadata.

    Attributes
    ----------
    deletionTime : int
        The time that the inode was deleted. If not deleted this will be 0.
    hasBlockPointers : bool
        Boolean value indicating whether the inode contains block pointers
    entries : list
        List containing Entry objects, which are ranges of block numbers
        in which the data for the associated file is contained

    Methods
    -------
    readExtentTree(self, diskPath: str, data: bytes, superBlock: super_block.SuperBlock) -> list
        Reads the ext4 extent tree. An extent tree is a data structure containing block pointers.
    readBlockPointers(self, diskPath: str, data: bytes, superBlock: super_block.SuperBlock) -> list
        Reads the direct and indirect block pointers contained in ext3 and ext2 inodes.
    readPointers(self, data: bytes) -> list[int]
        Reads all direct block pointers in the given byte list
    readIndirectPointers(self, diskPath: str, data: bytes, depth: int, superBlock: super_block.SuperBlock) -> list[int]
        Reads indirect block pointers in the given byte list, to the specified depth
    blockNumListToEntries(self, blocks: list[int]) -> list
        Given a list of block numbers, compresses them down to a list of entries
    """


    def __init__(self, diskO: disks.Disk, inodeNum: int, superBlock: super_block.SuperBlock, blockData, readPointers: bool):

        """
        Reads and stores the necessary inode metadata

        Parameters
        ----------
        diskO : disks.Disk
            The disk object of the currently selected disk.
            Used to read inode data and indirect block pointers from disk.
        inodeNum : int
            This may be an explicit inode number, or relative inode within the provided blockData.
            Used to calculate the location of the inode on disk.
        superBlock : super_block.SuperBlock
            The super block object associated with the disk.
            Used in calculating inode location on disk.
            Provides necessary metadata for reading block pointers.
        blockData : bool || bytes
            If this is a bool, it should be false, indicating whether the inode table data was provided
            and inodeNum is an explicit inode number.
            If this is type bytes, then the block data was provided and inodeNum is relative inode within blockData
        readPointers : bool
            A boolean value indicating whether the block pointers should be read
        """

        # if blockData is false, read from disk. inodeNum will be the inode number of the inode.
        if type(blockData) is bool:

            # initialize data needed to read the inode from disk.
            groupNum: int = int(inodeNum / superBlock.inodesPerGroup)

            groupDescriptor = group_descriptor.GroupDescriptor(diskO, groupNum, superBlock)

            inodeOffSet = ((inodeNum % superBlock.inodesPerGroup) - 1)
            inodesPerBlock = int(superBlock.blockSize / superBlock.inodeSize)

            inodeBlockNum = int(inodeOffSet / inodesPerBlock) + groupDescriptor.inodeTableLoc
            inodeByteOffSet = (inodeOffSet * superBlock.inodeSize) + (inodeBlockNum * superBlock.blockSize)

            # read inode from disk
            disk = open(diskO.diskPath, "rb")
            disk.seek(inodeByteOffSet)
            inodeData = disk.read(superBlock.inodeSize)
            disk.close


        # if inodeData is type bytes, it will be an inode table block.
        # inodeNum will be the inode num within that block, starting at 0.
        elif type(blockData) is bytes:
            inodeData = blockData[(inodeNum * superBlock.inodeSize): (inodeNum + 1) * superBlock.inodeSize]


        decoder = common.decode.Decoder()

        self.deletionTime: int = decoder.leBytesToDecimal(inodeData, 20, 23)

        if diskO.diskType == "ext4":
            # 0xF30A (62218) is the magic number indicating an ext4 extent node.
            # If the following bytes are not empty, then there are block pointers.
            self.hasBlockPointers = ((decoder.leBytesToDecimal(inodeData, 40, 41) == 62218)
            and (decoder.leBytesToDecimal(inodeData, 42, 43) > 0))
        elif diskO.diskType == "ext3" or diskO.diskType == "ext2":
            # The first block pointer (in ext2/3) is located in bytes 40-43 of the inode structure
            self.hasBlockPointers = (decoder.leBytesToDecimal(inodeData, 40, 43) > 0)

        self.entries: list[int] = []

        if readPointers and self.hasBlockPointers:
            if diskO.diskType == "ext4" and superBlock.hasExtent:
                self.entries = self.readExtentTree(diskO.diskPath, inodeData, superBlock)

            elif diskO.diskType == "ext3" or diskO.diskType == "ext2" or (diskO.diskType == "ext4" and not superBlock.hasExtent):
                self.entries = self.readBlockPointers(diskO.diskPath, inodeData, superBlock)


    def readExtentTree(self, diskPath: str, data: bytes, superBlock: super_block.SuperBlock) -> list:

        """
         Reads the ext4 extent tree. An extent tree is a data structure containing block pointers.

        Parameters
        ----------
        diskPath : str
            The path of the disk which contains the inode.
            This is necessary to read indirect block pointers.
        data : bytes
            The inodes byte data
            This contains the extent tree data.
        superBlock : super_block.SuperBlock
            The super block associated with the disk.
            Contains metadata necessary for reading specific block numbers


        Returns
        -------
            List containing Entry objects, which are ranges of block numbers
            in which the data for the associated file is contained
        """

        # nodes is treated as a queue in this algorithm
        nodes: list = []

        nodes.append(extent_node.ExtentNode(data[40:100]))

        entries: list[extent_node.ExtentEntry] = list()


        while len(nodes) != 0:
            currentNode = nodes.pop(0)

            # if the node is an index node, add all the nodes it points to to the list nodes
            if currentNode.header.extentDepth > 0:
                for index in currentNode.indices:
                    disk = open(diskPath, "rb")
                    disk.seek(superBlock.blockSize * index.nextNodeBlockNum)
                    nodeData = disk.read(superBlock.blockSize)
                    disk.close
                    nodes.append(extent_node.ExtentNode(nodeData))

            else:
                entries.extend(currentNode.entries)


        return sorted(entries, key=lambda entry: entry.fileBlockNum)


    def readBlockPointers(self, diskPath: str, data: bytes, superBlock: super_block.SuperBlock) -> list:

        """
        Reads the direct and indirect block pointers contained in ext3 and ext2 inodes.

        Parameters
        ----------
        diskPath : str
            The path of the disk which contains the inode.
            This is necessary to read indirect block pointers.
        data : bytes
            The inodes byte data.
            This contains the direct and indirect block pointers.
        superBlock : super_block.SuperBlock
            The super block associated with the disk.
            Contains metadata necessary for reading specific block numbers.

        Returns
        -------
        entries : list
            List containing Entry objects, which are ranges of block numbers
            in which the data for the associated file is contained
        """

        blocks: list[int] = []

        # Read the 12 direct block pointers
        blocks.extend(self.readPointers(data[40:88]))

        # Read the indirect pointers
        blocks.extend(self.readIndirectPointers(diskPath, data[88:92], 1, superBlock))
        blocks.extend(self.readIndirectPointers(diskPath, data[92:96], 2, superBlock))
        blocks.extend(self.readIndirectPointers(diskPath, data[96:100], 3, superBlock))

        entries = self.blockNumListToEntries(blocks)

        return entries


    def readPointers(self, data: bytes) -> list:

        """
        Given a byte list containing 4 byte block pointers, decodes them and returns a list of block numbers.
        Is a helper method for both readBlockPointers and readIndirectPointers.

        Parameters
        ----------
        data : bytes
            A byte list containing 4 byte block pointers.
            Is read from in order to decode the block pointers

        Returns
        -------
        pointers : list[int]
            A list containing block numbers of the pointers in data
        """

        decoder: common.decode.Decoder = common.decode.Decoder
        pointers: list[int] = []

        offSet: int = 0
        while offSet < len(data):
            blockNum: int = decoder.leBytesToDecimal(self, data, offSet, offSet + 3)
            if blockNum != 0:
                pointers.append(blockNum)
            offSet += 4

        return pointers


    def readIndirectPointers(self, diskPath: str, data: bytes, depth: int, superBlock: super_block.SuperBlock) -> list:

        """
        Reads indirect block pointers in the given byte list, to the specified depth.
        Is a helper method for readBlockPointers

        Parameters
        ----------
        diskPath : str
        data : bytes
            The byte list containing the indirect pointers
            Is read from in order to follow the block pointers
        depth : int
            The depth to which the pointers are indirect
        superBlock : super_block.SuperBlock
            The super block associated with the disk.
            Contains metadata necessary for reading specific block numbers.

        Returns
        -------
        pointers : list[int]
            A list containing the pointers which were read
        """

        pointers: list[int] = self.readPointers(data)
        tempPointers: list[int] = []

        for i in range(0, depth):
            for indirectPointerBlockNum in pointers:
                disk = open(diskPath, "rb")
                disk.seek(superBlock.blockSize * indirectPointerBlockNum)
                indirectPointerData = disk.read(superBlock.blockSize)
                disk.close
                tempPointers.extend(self.readPointers(indirectPointerData))

            pointers = tempPointers
            tempPointers = []

        return pointers


    def blockNumListToEntries(self, blocks: list) -> list:

        """
        Given a list of block numbers, compresses them down to a list of entries.
        Is a helper method for readBlockPointers

        Parameters
        ----------
        blocks : list[int]
            A list of block numbers
            These are converted into a list of entries

        Returns
        -------
        entries
            List containing Entry objects, which are ranges of block numbers
            in which the data for the associated file is contained.
        """

        entries: list = []

        fileBlockNum: int = 0
        prevBlock: int = blocks[0]
        numBlocksInEntry: int = 0
        entry: BlockPointerEntry = BlockPointerEntry(fileBlockNum, 0, blocks[0])
        for block in blocks:

            if block != prevBlock + 1:
                entry.numBlocks = numBlocksInEntry
                entries.append(entry)
                numBlocksInEntry = 0
                entry = BlockPointerEntry(fileBlockNum, 0, block)

            numBlocksInEntry += 1
            fileBlockNum += 1
            prevBlock = block

        entry.numBlocks = numBlocksInEntry
        entries.append(entry)

        return sorted(entries, key=lambda entry: entry.fileBlockNum)


class BlockPointerEntry:
    """
    An entry, containing data on a contigous block which contain the files data

    Attributes
    ----------
    fileBlockNum : int
        The block number which the first block pointer is associated with,
        relative to the beginning of the file.
    numBlocks : int
        The number of blocks which this extent entry refers to.
    blockNum : int
        The first block number in a contiguous
        run of blocks (with length numBlocks) which this extent entry refers to.
    """

    def __init__(self, fileBlockNum, numBlocks, blockNum):
        self.fileBlockNum = fileBlockNum
        self.numBlocks = numBlocks
        self.blockNum = blockNum
