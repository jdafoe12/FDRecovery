
import decode
import extent_node
import group_descriptor
import super_block


class Inode:

    def __init__(self, diskO, inodeNum, superBlock: super_block.SuperBlock, blockData):
        
        # if blockData is false, read from disk. inodeNum will be the inode number of the inode
        if type(blockData) is bool and blockData == False:

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


        # if inodeData is type bytes, it will be an inode table block. inodeNum will be the inode num within that block, starting at 0
        elif type(blockData) is bytes:
            inodeData = blockData[(inodeNum * superBlock.inodeSize): (inodeNum + 1) * superBlock.inodeSize]


        decoder = decode.Decoder()

        # initialize inode data
        self.deletionTime = decoder.leBytesToDecimal(inodeData, 20, 23)
        self.hasExtentTree = (decoder.leBytesToDecimal(inodeData, 40, 41) == 62218) and (decoder.leBytesToDecimal(inodeData, 42, 43) > 0)
        self.entries: list[int] = list

        if self.hasExtentTree and type(diskO) is not bool:

            if diskO.diskType == "ext4":
                self.entries = self.readExtentTree(diskO.diskPath, inodeData, list(), superBlock)
            elif diskO.diskType == "ext3":
                self.entries = self.readBlockPointers(diskO.diskPath, inodeData, superBlock)


    def readExtentTree(self, diskName, data, nodes: list, superBlock: super_block.SuperBlock):

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

        # Makes entries from the list of blocks
        entry = self.BlockPointerEntry(0, 0, 0)
        prevBlock = 0
        numBlocksInEntry = 0
        fileBlockNum = 0
        for block in blocks:
            # If this block number is directly after the last one, keep it in the same entry
            if block == prevBlock + 1 and entry.blockNum == 0:

                if entry.blockNum == 0:
                    entry.blockNum = prevBlock
                    entry.fileBlockNum = fileBlockNum - 1

            # If block number is not directly after last one, Make a new entry
            elif block != prevBlock + 1:

                if entry.blockNum != 0:
                    entry.numBlocks = numBlocksInEntry

                entries.append(entry)
                entry = self.BlockPointerEntry(0, 0, 0)
                numBlocksInEntry = 0

            # Increment counters
            prevBlock = block
            numBlocksInEntry += 1
            fileBlockNum += 1


        return sorted(entries, key=lambda entry: entry.fileBlockNum)

    
    def readPointers(self, data):
        
        decoder = decode.Decoder
        pointers = []

        offSet = 0
        while offSet < len(data):
            blockNum = decoder.leBytesToDecimal(data, offSet, offSet + 3)
            if blockNum != 0:
                pointers.append(blockNum)
            offSet += 4

        return pointers

    def readIndirectPointers(self, diskName, data, depth, superBlock: super_block.SuperBlock):

        pointers = []

        pointers = self.readPointers(data)

        for i in range(0, depth - 1):
            numPointers = len(pointers)
            for indirectPointerBlockNum in pointers:
                disk = open(diskName, "rb")
                disk.seek(superBlock.blockSize * indirectPointerBlockNum)
                indirectPointerData = disk.read(superBlock.blockSize)
                disk.close
                pointers.extend(self.readPointers(indirectPointerData))
            
            for index in range(0, numPointers):
                pointers.pop(index)

        return pointers


class BlockPointerEntry:

    def __init__(self, fileBlockNum, numBlocks, blockNum):
        self.fileBlockNum = fileBlockNum
        self.numBlocks = numBlocks
        self.blockNum = blockNum

    