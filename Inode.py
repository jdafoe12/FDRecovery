

from email.policy import strict
from typing import Any
from ExtentNode import ExtentNode, ExtentIndex, ExtentEntry, ExtentHeader
from Decoder import Decoder
from GroupDescriptor import GroupDescriptor
from SuperBlock import SuperBlock


class Inode:
    def __init__(self, diskName, inodeNum, superBlock: SuperBlock, blockData):
        
        if type(blockData) is bool and blockData == False:
            groupNum: int = int(inodeNum / superBlock.getInodesPerGroup())

            groupDescriptor = GroupDescriptor(diskName, groupNum, superBlock)

            inodeOffSet = ((inodeNum % superBlock.getInodesPerGroup()) - 1)
            inodesPerBlock = int(superBlock.getBlockSize() / superBlock.getInodeSize())

            inodeBlockNum = int(inodeOffSet / inodesPerBlock) + groupDescriptor.getInodeTableLoc()
            inodeByteOffSet = (inodeOffSet * superBlock.getInodeSize()) + (inodeBlockNum * superBlock.getBlockSize())

            disk = open(diskName, "rb")
            disk.seek(inodeByteOffSet)
            inodeData = disk.read(superBlock.getInodeSize())
            disk.close

        # if inode data is type bytes, it will be an inode table block. inodeNum will be the inode num within that block, starting at 0
        elif type(blockData) is bytes:
            inodeData = blockData[(inodeNum * superBlock.getInodeSize()): (inodeNum + 1) * superBlock.getInodeSize()]

        decoder = Decoder()
        self.deletionTime = decoder.leBytesToDecimal(inodeData, 20, 23)

        self.hasExtentTree = (decoder.leBytesToDecimal(inodeData, 40, 41) == 62218) and (decoder.leBytesToDecimal(inodeData, 42, 43) > 0)
        self.entries: list[int] = list

        if self.hasExtentTree and type(diskName) is not bool:
            self.entries = self.readExtentTree(diskName, inodeData, list(), superBlock)


    def readExtentTree(self, diskName, data, nodes: list, superBlock: SuperBlock):

        if len(nodes) == 0:
            nodes.append(ExtentNode(data[40:100]))

        entries: list[ExtentEntry] = list()

        while len(nodes) != 0:
            currentNode = nodes.pop(0)

            if currentNode.header.extentDepth > 0:
                for index in currentNode.indices:
                    disk = open(diskName, "rb")
                    disk.seek(superBlock.getBlockSize() * index.nextNodeBlockNum)
                    nodeData = disk.read(superBlock.getBlockSize())
                    disk.close
                    nodes.append(ExtentNode(nodeData))
            
            else:
                entries.extend(currentNode.entries)

        newEntries: list[(int, int , int)] = list()

        for entry in entries:
            newEntries.append((entry.fileBlockNum, entry.numBlocks, entry.blockNum))

        return sorted(newEntries, key=lambda entry: entry[0])

    




