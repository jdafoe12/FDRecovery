

from math import ceil
import os

import disks
import group_descriptor
import read_inode
import super_block
import decode
import journal


class ReadJournal:

    """
    Reads data from the filesystem journal.

    Attributes
    ----------
    diskO : disks.Disk
        The disk object associated with the filesystem on which the journal being read from is contained.

    Methods
    -------
    readFileSystemJournal(self) -> list[journal.Transaction]
        Reads the filesystem journal, encapsulating its data in journal.Transaction objects.
    getBlockTypeMap(self, superBlock: super_block.SuperBlock) -> dict[int, str]
        Reads through filesystem metadata to create a dictionary associating block numbers with metadata block type.
        These block types can be inode table blocks, data bitmap blocks, inode bitmap blocks, and group descriptor Blocks.
        This is a helper method for readFileSystemJournal.
    readJournalBlock(self, journalBlockNum: int) -> bytes
        Given a block number relative to the beginning of the journal, returns the bytes of that block.
    """


    def __init__(self, diskO: disks.Disk):

        """
        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem on which the journal being read from is contained.
        """
        self.diskO = diskO


    def readFileSystemJournal(self) -> list[journal.Transaction]:

        """
        Reads the filesystem journal, encapsulating its data in journal.Transaction objects.

        Returns
        -------
        Explicit:
        transactionList : list[journal.Transaction]
            A list of the transactions in the journal represented as journal.Transaction objects.

        Implicit:
        None
        """

        # flush filesystem cache
        os.sync()
        drop_caches = open("/proc/sys/vm/drop_caches", "w")
        drop_caches.write("3")
        drop_caches.close()


        superBlock = super_block.SuperBlock(self.diskO)
        decoder = decode.Decoder()

        blockTypeMap = self.getBlockTypeMap(superBlock)

        fileSystemJournalInode = read_inode.Inode(self.diskO, superBlock.journalInode, superBlock, False, True)

        
        transactionList = []

        journalBlockNum = 0
        deleteLast = False
        hasCommitBlock = True
        # an entry is a extent entry which specify the block numbers of the journal
        for entry in fileSystemJournalInode.entries:

            disk = open(self.diskO.diskPath, "rb")
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
                    transactionList.append(journal.Transaction(block, journalBlockNum, blockTypeMap, self.diskO))

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


    def getBlockTypeMap(self, superBlock: super_block.SuperBlock) -> dict[int, str]:

        """
        Reads through filesystem metadata to create a dictionary associating block numbers with metadata block type.
        These block types can be inode table blocks, data bitmap blocks, inode bitmap blocks, and group descriptor Blocks.
        This is a helper method for readFileSystemJournal.

        Parameters
        ----------
        superBlock : super_block.SuperBlock
            Contains metadata necessary for positioning correctly on disk.

        Returns
        -------
        Explicit:
        blockTypeMap : dict[int, str]
            A dictionary associating block numbers with metadata block type.

        Implicit:
        None
        """

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

            groupDescriptor = group_descriptor.GroupDescriptor(self.diskO, descriptorNum, superBlock)

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


    def readJournalBlock(self, journalBlockNum: int) -> bytes:

        """
        Given a block number relative to the beginning of the journal, returns the bytes of that block.
        Parameters
        ----------
        journalBlockNum : int
            The block number to be read, relative to the beginning of the journal.

        Returns
        -------
        Explicit:
        data : bytes
            The bytes contained on the journal block which was read.

        Implicit:
        None
        """

        superBlock = super_block.SuperBlock(self.diskO)
        fileSystemJournalInode = read_inode.Inode(self.diskO, superBlock.journalInode, superBlock, False, True)

        journalBlockNum = journalBlockNum % ((fileSystemJournalInode.entries[-1].fileBlockNum + fileSystemJournalInode.entries[-1].numBlocks) - 1)

        if journalBlockNum == 0:
            journalBlockNum = fileSystemJournalInode.entries[-1].fileBlockNum + fileSystemJournalInode.entries[-1].numBlocks


        blockEntry = ()
        for entry in fileSystemJournalInode.entries:
            if entry.fileBlockNum + entry.numBlocks >= journalBlockNum:
                blockEntry = entry
                break


        disk = open(self.diskO.diskPath, "rb")
        disk.seek(superBlock.blockSize * (blockEntry.blockNum + (journalBlockNum - blockEntry.fileBlockNum)))
        data = disk.read(superBlock.blockSize)
        disk.close()

        return data

