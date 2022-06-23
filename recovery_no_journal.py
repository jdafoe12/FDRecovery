
from math import ceil, floor

import time

import group_descriptor
import super_block
import decode
import read_inode

class FileRecoveryNoJournal:

    def recoverFiles(self, diskO, deletedInodes, numToRecover, filePath):

        superBlock = super_block.SuperBlock(diskO)

        toRecover = deletedInodes[0, numToRecover]

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

        superBlock = super_block.SuperBlock(diskO)

        inodesToCheck = self.readInodeBitmaps(diskO, superBlock)
        deletedInodes = []

        for inodeNum in inodesToCheck:
            inode = read_inode.Inode(diskO, inodeNum, superBlock, False, False)
            if inode.deletionTime == 0:
                break


            deletedInodes.append((inodeNum, inode.deletionTime))

        deletedInodes.sort(key=lambda inode: -inode[1])

        return deletedInodes

    # returns a list of inode numbers to check
    def readInodeBitmaps(self, diskO, superBlock: super_block.SuperBlock):

        blockSize = superBlock.blockSize
        blocksPerGroup = superBlock.blocksPerGroup
        inodesPerGroup = superBlock.inodesPerGroup

        iBitmaps = []
        inodesToCheck = []

        for descriptorNum in range(0, int(superBlock.numBlocks / blocksPerGroup)):
            groupDescriptor = group_descriptor.GroupDescriptor(diskO, descriptorNum, superBlock)


            for iBitmapBlockNum in range(groupDescriptor.inodeBitMapLoc, groupDescriptor.inodeBitMapLoc + ceil(inodesPerGroup / (blockSize * 8))):
                iBitmaps.append(iBitmapBlockNum)


        decoder = decode.Decoder

        for iBitmapBlockNum in iBitmaps:

            firstInodeNum = (descriptorNum * superBlock.inodesPerGroup) + 1



            disk = open(diskO.diskPath, "rb")
            disk.seek(superBlock.blockSize * iBitmapBlockNum)
            bytes = disk.read(ceil(superBlock.inodesPerGroup / 8))
            disk.close

            bits = decoder.leBytesToBitArray(self, bytes)

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
                    inodesToCheck.extend(list(range(firstInodeNum + (prevPosition[1] + 1), position[1])))



        return inodesToCheck
        