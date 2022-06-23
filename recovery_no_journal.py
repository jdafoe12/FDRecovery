
from math import ceil, floor

import time
import os

import group_descriptor
import super_block
import decode
import read_inode

class FileRecoveryNoJournal:

    def recoverFiles(self, diskO, deletedInodes, numToRecover, filePath):

        superBlock = super_block.SuperBlock(diskO)

        toRecover = deletedInodes[0 : numToRecover]

        numRecovered = 0
        for deletedInode in toRecover:

            inode = read_inode.Inode(diskO, deletedInode[0], superBlock, False, True)

            numRecovered += 1

            recoveredFile = open("%s/recoveredFile_%s" % (filePath, (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(deletedInode[1])) + f"_num_{numRecovered}")), "ab")

            for entry in inode.entries:
                disk = open(diskO.diskPath, "rb")
                disk.seek(superBlock.blockSize * entry.blockNum)

                for i in range(0, entry.numBlocks):
                    recoveredFile.write(disk.read(superBlock.blockSize))
                                
                disk.close
            recoveredFile.close



        return numRecovered

    # returns a list of deleted inodes as tuple (inode num, inode deletion time)
    def getDeletedInodes(self, diskO):
        # need to add cache flushing somewhere. Maybe write a seperate function for it at this point.
        deletedInodes = []

        superBlock = super_block.SuperBlock(diskO)

        inodeBitmaps = self.getInodeBitmaps(diskO, superBlock)

        for iBitmap in inodeBitmaps:
            holes = self.findHoles(diskO,iBitmap, superBlock)

            for inodeNum in holes[0]:
                inode = read_inode.Inode(diskO, inodeNum, superBlock, False, False)

                if inode.deletionTime != 0:
                    deletedInodes.append((inodeNum, inode.deletionTime))

            for inodeNum in range(holes[1], (((iBitmap[1] * superBlock.inodesPerGroup) + 1) + superBlock.inodesPerGroup)):
                
                inode = read_inode.Inode(diskO, inodeNum, superBlock, False, False)

                if inode.deletionTime != 0:
                    deletedInodes.append((inodeNum, inode.deletionTime))
                elif inode.deletionTime == 0:
                    break
        
        deletedInodes.sort(key=lambda inode: -inode[1])

        return deletedInodes

    # returns a list of inode bitmaps which are tuple(iBitmapBlockNum, descriptorNum)
    def getInodeBitmaps(self, diskO, superBlock):
        blockSize = superBlock.blockSize
        blocksPerGroup = superBlock.blocksPerGroup
        inodesPerGroup = superBlock.inodesPerGroup

        iBitmaps = [()]

        for descriptorNum in range(0, int(superBlock.numBlocks / blocksPerGroup)):
            groupDescriptor = group_descriptor.GroupDescriptor(diskO, descriptorNum, superBlock)


            for iBitmapBlockNum in range(groupDescriptor.inodeBitMapLoc, groupDescriptor.inodeBitMapLoc + ceil(inodesPerGroup / (blockSize * 8))):
                iBitmaps.append((iBitmapBlockNum, descriptorNum))
        
        return iBitmaps





    # returns a tuple (list of hole inodes, first end inode)
    def findHoles(self, diskO, iBitmap, superBlock):

        firstInodeNum = (iBitmap[1] * superBlock.inodesPerGroup) + 1

        holeInodes = ([], int)

        disk = open(diskO.diskPath, "rb")
        disk.seek(superBlock.blockSize * iBitmap[0])
        bytes = disk.read(ceil(superBlock.inodesPerGroup / 8))
        disk.close

        decoder = decode.Decoder

        bits = decoder.leBytesToBitArray(bytes)
        
        # list of tuple(position of 1 bit, relative position of 0 bit(0 for left, 1 for right))
        gapRanges = []

        prevBit = 1
        for i in range(0, len(bits)):
            if bits[i] == 1 and prevBit == 0:
                gapRanges.append((i, 0))
            elif bits[i] == 0 and prevBit == 1:
                gapRanges.append((i - 1, 1))

            prevBit = bits[i]


        prevPosition = (-1, 1)
        for position in gapRanges:
            if prevPosition[1] == 1 and position[1] == 0:
                holeInodes[0].extend(list(range(firstInodeNum + (prevPosition[1] + 1), position[1])))
            elif prevPosition[1] == 0 and position[1] == 1:
                holeInodes[1] = position[0] + 1
            prevPosition = position
            
        return holeInodes