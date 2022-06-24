

import decode
import disks
import extent_node
import group_descriptor
import super_block


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
    readExtentTree(diskName, data, nodes: list, superBlock: super_block.SuperBlock)
        Reads the ext4 extent tree. An extent tree is a data structure containing block pointers.
    readBlockPointers(diskName, data, superBlock: super_block.SuperBlock)
        Reads the direct and indirect block pointers contained in ext3 and ext2 inodes.
    readPointers(data)
        Reads all direct block pointers in the given byte list
    readIndirectPointers(diskName, data, depth, superBlock: super_block.SuperBlock)
        Reads indirect block pointers in the given byte list, to the specified depth
    """

    def __init__(self, diskO: disks.Disk, inodeNum: int, superBlock: super_block.SuperBlock, blockData, readPointers: bool):

        """
        Reads and stores the necessary inode metadata

        Parameters
        ----------
        diskO : disks.Disk
            The disk object of the currently selected disk
        inodeNum : int
            This may be an explicit inode number, or relative inode within the provided blockData
        superBlock : super_block.SuperBlock
            The super block object associated with the disk
        blockData : bool || bytes
            If this is a bool, it should be false, indicating whether the inode table data was provided
            and inodeNum is an explicit inode number
            If this is type bytes, then the block data was provided and inodeNum is relative inode within blockData
        readPointers : bool
            A boolean value indicating whether the block pointers should be read
        """
        
        # if blockData is false, read from disk. inodeNum will be the inode number of the inode
        if type(blockData) is bool:

            # initialize data needed to read the inode from disk
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


        decoder = decode.Decoder()

        # initialize inode data
        self.deletionTime: int = decoder.leBytesToDecimal(inodeData, 20, 23)

        if diskO.diskType == "ext4":
            self.hasBlockPointers = (decoder.leBytesToDecimal(inodeData, 40, 41) == 62218) and (decoder.leBytesToDecimal(inodeData, 42, 43) > 0)
        elif diskO.diskType == "ext3" or diskO.diskType == "ext2":
            self.hasBlockPointers = (decoder.leBytesToDecimal(inodeData, 40, 43) > 0)

        self.entries: list[int] = []

        if readPointers and self.hasBlockPointers and diskO.diskType == "ext4":
            self.entries = self.readExtentTree(diskO.diskPath, inodeData, list(), superBlock)

        elif readPointers and self.hasBlockPointers and (diskO.diskType == "ext3" or diskO.diskType == "ext2"):
            self.entries = self.readBlockPointers(diskO.diskPath, inodeData, superBlock)


    def readExtentTree(self, diskName, data, nodes: list, superBlock: super_block.SuperBlock) -> list:

        # the list nodes is treated as a queue in this algorithm
        nodes.append(extent_node.ExtentNode(data[40:100]))

        entries: list[extent_node.ExtentEntry] = list()


        while len(nodes) != 0:
            currentNode = nodes.pop(0)

            # if the node is an index node, add all of the nodes it points to to the list nodes
            if currentNode.header.extentDepth > 0:
                for index in currentNode.indices:
                    disk = open(diskName, "rb")
                    disk.seek(superBlock.blockSize * index.nextNodeBlockNum)
                    nodeData = disk.read(superBlock.blockSize)
                    disk.close
                    nodes.append(extent_node.ExtentNode(nodeData))
            
            else:
                entries.extend(currentNode.entries)


        return sorted(entries, key=lambda entry: entry.fileBlockNum)

    def readBlockPointers(self, diskName, data, superBlock: super_block.SuperBlock):

        blocks = []
        entries = []

        # Read the 12 direct block pointers
        blocks.extend(self.readPointers(data[40:88]))

        # Read the indirect pointers
        blocks.extend(self.readIndirectPointers(diskName, data[88:92], 1, superBlock))
        blocks.extend(self.readIndirectPointers(diskName, data[92:96], 2, superBlock))
        blocks.extend(self.readIndirectPointers(diskName, data[96:100], 3, superBlock))


        fileBlockNum = 0
        prevBlock = blocks[0]
        numBlocksInEntry = 0
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

    
    def readPointers(self, data):
        
        decoder = decode.Decoder
        pointers = []

        offSet = 0
        while offSet < len(data):
            blockNum = decoder.leBytesToDecimal(self, data, offSet, offSet + 3)
            if blockNum != 0:
                pointers.append(blockNum)
            offSet += 4

        return pointers

    def readIndirectPointers(self, diskName, data, depth, superBlock: super_block.SuperBlock):

        pointers = []
        tempPointers = []

        pointers = self.readPointers(data)

        for i in range(0, depth):
            for indirectPointerBlockNum in pointers:
                disk = open(diskName, "rb")
                disk.seek(superBlock.blockSize * indirectPointerBlockNum)
                indirectPointerData = disk.read(superBlock.blockSize)
                disk.close
                tempPointers.extend(self.readPointers(indirectPointerData))
            
            pointers = tempPointers
            tempPointers = []

        return pointers


class BlockPointerEntry:

    def __init__(self, fileBlockNum, numBlocks, blockNum):
        self.fileBlockNum = fileBlockNum
        self.numBlocks = numBlocks
        self.blockNum = blockNum

    