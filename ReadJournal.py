from math import ceil, floor
import os
from GroupDescriptor import GroupDescriptor
from Inode import Inode
from SuperBlock import SuperBlock
from Decoder import *
from Journal import *


class ReadJournal:

    def __init__(self, diskName):
        self.diskName = diskName


    def getBlockTypeMap(self, superBlock: SuperBlock):

        # initialize constant variables
        blockSize = superBlock.blockSize
        blocksPerGroup = superBlock.blocksPerGroup
        inodesPerGroup = superBlock.inodesPerGroup
        inodeSize = superBlock.inodeSize
        numDescriptorsPerBlock = (blockSize / superBlock.groupDescriptorSize)


        blockTypeMap = {}


        # initialize counter variables
        descriptorBlockNum = 1
        descriptorNumInBlock = 0

        for descriptorNum in range(0, int(superBlock.numBlocks / blocksPerGroup)):

            groupDescriptor = GroupDescriptor(self.diskName, descriptorNum, superBlock)

            inodeTableLoc = groupDescriptor.inodeTableLoc


            # block range of inode table is ((inodesPerGroup * InodeSize) / blockSize) rounded up
            for iTableBlockNum in range(inodeTableLoc, inodeTableLoc + ceil((inodesPerGroup * inodeSize) / blockSize)):
                blockTypeMap.update({iTableBlockNum:"iTableBlock"})

            # block range of data bitmap is (NumBlocksPerGroup / (BlockSize * 8)) rounded up
            for dBitmapBlockNum in range(groupDescriptor.blockBitMapLoc, groupDescriptor.blockBitMapLoc + ceil(blocksPerGroup / (blockSize * 8))):
                blockTypeMap.update({dBitmapBlockNum:"dBitmapBlock"})

            # block range of inode bitmap is (NumInodesPerGroup / (BlockSize * 8)) rounded up
            for iBitmapBlockNum in range(groupDescriptor.inodeBitMapLoc, groupDescriptor.inodeBitMapLoc + ceil(inodesPerGroup / (blockSize * 8))):
                blockTypeMap.update({iBitmapBlockNum:"iBitmapBlock"})

            # block group descriptors start at block 1 and go to block ((numBlocks / BlocksPerGroup) / (BlockSize / GroupDescriptorSize))
            if descriptorNumInBlock == 1:
                blockTypeMap.update({descriptorBlockNum:"GroupDescriptorBlock"})


            elif descriptorNumInBlock == numDescriptorsPerBlock:
                descriptorBlockNum += 1
            descriptorNumInBlock = (descriptorNumInBlock % numDescriptorsPerBlock) + 1


        return blockTypeMap


    def readFileSystemJournal(self):

        # flush filesystem cache
        os.sync()
        drop_caches = open("/proc/sys/vm/drop_caches", "w")
        drop_caches.write("3")
        drop_caches.close()


        superBlock = SuperBlock(self.diskName)
        decoder = Decoder()

        blockTypeMap = self.getBlockTypeMap(superBlock)

        fileSystemJournalInode = Inode(self.diskName, superBlock.journalInode, superBlock, False)

        
        transactionList = []

        journalBlockNum = 0
        deleteLast = False
        hasCommitBlock = True
        # an entry is a extent entry which specify the block numbers of the journal
        for entry in fileSystemJournalInode.entries:

            disk = open(self.diskName, "rb")
            disk.seek(superBlock.blockSize * entry.blockNum)

            # for each block in entry
            for i in range(0, entry.numBlocks):
                block = disk.read(superBlock.blockSize)

                # if this block in the journal is a descriptor block
                if (decoder.beBytesToDecimal(block, 0, 3) == 3225106840) and (decoder.beBytesToDecimal(block, 4, 7) == 1):

                    if deleteLast or not hasCommitBlock:
                        transactionList.pop()
                        deleteLast = False
                    
                    # reset values for new transaction
                    hasCommitBlock = False

                    # add a new transaction
                    transactionList.append(Transaction(block, journalBlockNum, blockTypeMap))

                # if this block in the journal is the commit block for the current transaction, set the commit time
                elif len(transactionList) > 0:
                    if (decoder.beBytesToDecimal(block, 0, 3) == 3225106840) and (decoder.beBytesToDecimal(block, 4, 7) == 2) and (decoder.beBytesToDecimal(block, 8, 11) == transactionList[-1].transactionNum):
                        transactionList[-1].commitTime = decoder.beBytesToDecimal(block, 48, 55)
                        hasCommitBlock = True

                    # if this block in the journal is a commit block, but not for the current transaction, remove the transaction
                    elif (decoder.beBytesToDecimal(block, 0, 3) == 3225106840) and (decoder.beBytesToDecimal(block, 4, 7) == 2) and (decoder.beBytesToDecimal(block, 8, 11) != transactionList[-1].transactionNum):
                        if not hasCommitBlock:
                            deleteLast = True

                journalBlockNum += 1


            disk.close

        return transactionList


    def readJournalBlock(self, journalBlockNum):

        superBlock = SuperBlock(self.diskName)
        fileSystemJournalInode = Inode(self.diskName, superBlock.journalInode, superBlock, False)

        blockEntry = ()
        for entry in fileSystemJournalInode.entries:
            if entry.fileBlockNum + entry.numBlocks > journalBlockNum:
                blockEntry = entry


        disk = open(self.diskName, "rb")
        disk.seek(superBlock.blockSize * (blockEntry.blockNum + (journalBlockNum - blockEntry.fileBlockNum)))

        data = disk.read(superBlock.blockSize)

        disk.close()


        return data

