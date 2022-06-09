
from ExtentNode import *
from Decoder import Decoder
from GroupDescriptor import GroupDescriptor
from SuperBlock import SuperBlock


class Inode:

    def __init__(self, diskName, inodeNum, superBlock: SuperBlock, blockData):
        
        # if blockData is false, read from disk. inodeNum will be the inode number of the inode
        if type(blockData) is bool and blockData == False:

            # initialize data needed to read the inode from disk
            groupNum: int = int(inodeNum / superBlock.inodesPerGroup)

            groupDescriptor = GroupDescriptor(diskName, groupNum, superBlock)

            inodeOffSet = ((inodeNum % superBlock.inodesPerGroup) - 1)
            inodesPerBlock = int(superBlock.blockSize / superBlock.inodeSize)

            inodeBlockNum = int(inodeOffSet / inodesPerBlock) + groupDescriptor.inodeTableLoc
            inodeByteOffSet = (inodeOffSet * superBlock.inodeSize) + (inodeBlockNum * superBlock.blockSize)

            # read inode from disk
            disk = open(diskName, "rb")
            disk.seek(inodeByteOffSet)
            inodeData = disk.read(superBlock.inodeSize)
            disk.close


        # if inodeData is type bytes, it will be an inode table block. inodeNum will be the inode num within that block, starting at 0
        elif type(blockData) is bytes:
            inodeData = blockData[(inodeNum * superBlock.inodeSize): (inodeNum + 1) * superBlock.inodeSize]


        decoder = Decoder()

        # initialize inode data
        self.deletionTime = decoder.leBytesToDecimal(inodeData, 20, 23)
        self.hasExtentTree = (decoder.leBytesToDecimal(inodeData, 40, 41) == 62218) and (decoder.leBytesToDecimal(inodeData, 42, 43) > 0)
        self.entries: list[int] = list

        if self.hasExtentTree and type(diskName) is not bool:
            self.entries = self.readExtentTree(diskName, inodeData, list(), superBlock)


    def readExtentTree(self, diskName, data, nodes: list, superBlock: SuperBlock):

        # the list nodes is treated as a queue in this algorithm
        nodes.append(ExtentNode(data[40:100]))

        entries: list[ExtentEntry] = list()


        while len(nodes) != 0:
            currentNode = nodes.pop(0)

            # if the node is an index node, add all of the nodes it points to to the list nodes
            if currentNode.header.extentDepth > 0:
                for index in currentNode.indices:
                    disk = open(diskName, "rb")
                    disk.seek(superBlock.blockSize * index.nextNodeBlockNum)
                    nodeData = disk.read(superBlock.blockSize)
                    disk.close
                    nodes.append(ExtentNode(nodeData))
            
            else:
                entries.extend(currentNode.entries)


        return sorted(entries, key=lambda entry: entry.fileBlockNum)

    