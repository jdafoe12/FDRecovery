

from math import ceil
import os

from src import common
from src.EXT import structures
from src.EXT import journal


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


    def __init__(self, diskO: structures.disks.Disk):

        """
        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem on which the journal being read from is contained.
        """
        self.diskO = diskO


    def readFileSystemJournal(self) -> list:

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

        # Flush filesystem cache.
        os.sync()
        drop_caches = open("/proc/sys/vm/drop_caches", "w")
        drop_caches.write("3")
        drop_caches.close()

        superBlock = structures.super_block.SuperBlock(self.diskO)
        decoder = common.decode.Decoder()

        blockTypeMap = self.getBlockTypeMap(superBlock)

        fileSystemJournalInode = structures.read_inode.Inode(self.diskO, superBlock.journalInode, superBlock, False, True)

        # Read Journal Super Block.
        disk = open(self.diskO.diskPath, "rb")
        disk.seek(fileSystemJournalInode.entries[0].blockNum * superBlock.blockSize)
        jSuperData = disk.read(1024)
        journalSuperBlock = journal.JournalSuperBlock(jSuperData)
        disk.close

        transactionList = []

        journalBlockNum = 0
        deleteLast = False
        hasCommitBlock = True
        # An entry specifies the block numbers of the journal.
        for entry in fileSystemJournalInode.entries:

            disk = open(self.diskO.diskPath, "rb")
            disk.seek(superBlock.blockSize * entry.blockNum)

            for i in range(0, entry.numBlocks):
                block = disk.read(superBlock.blockSize)

                # Bytes 0-3 are a magic number indicating a journal transaction metadata block.
                # The number in bytes 4-7 indicates the metadata block type. 1 is a descriptor block, 2 is a commit block.
                if (decoder.beBytesToDecimal(block, 0, 3) == 3225106840) and (decoder.beBytesToDecimal(block, 4, 7) == 1):
                    if deleteLast or not hasCommitBlock:
                        transactionList.pop()
                        deleteLast = False
                    
                    hasCommitBlock = False

                    transactionList.append(journal.Transaction(block, journalBlockNum, blockTypeMap, journalSuperBlock, superBlock))

                elif len(transactionList) > 0:
                    # if this block in the journal is the commit block for the current transaction, set the commit time.
                    if ((decoder.beBytesToDecimal(block, 0, 3) == 3225106840) and (decoder.beBytesToDecimal(block, 4, 7) == 2)
                    and (decoder.beBytesToDecimal(block, 8, 11) == transactionList[-1].transactionNum)):
                        transactionList[-1].commitTime = decoder.beBytesToDecimal(block, 48, 55)
                        hasCommitBlock = True

                    # if this block in the journal is a commit block, but not for the current transaction, remove the transaction.
                    elif (decoder.beBytesToDecimal(block, 0, 3) == 3225106840) and (decoder.beBytesToDecimal(block, 4, 7) == 2) and (decoder.beBytesToDecimal(block, 8, 11) != transactionList[-1].transactionNum):
                        if not hasCommitBlock:
                            deleteLast = True

                journalBlockNum += 1

            disk.close

        return transactionList


    def getBlockTypeMap(self, superBlock: structures.super_block.SuperBlock) -> dict:

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
        blockTypeMap : dict[int, str]
            A dictionary associating block numbers with metadata block type.
        """

        blockSize = superBlock.blockSize
        blocksPerGroup = superBlock.blocksPerGroup
        inodesPerGroup = superBlock.inodesPerGroup
        inodeSize = superBlock.inodeSize
        numDescriptorsPerBlock = (blockSize / superBlock.groupDescriptorSize)

        blockTypeMap = {}

        descriptorBlockNum = 1
        descriptorNumInBlock = 0

        # numBlocks / blocksPerGroup represents the number of groups.
        for descriptorNum in range(0, int(superBlock.numBlocks / blocksPerGroup)):

            groupDescriptor = structures.group_descriptor.GroupDescriptor(self.diskO, descriptorNum, superBlock)

            inodeTableLoc = groupDescriptor.inodeTableLoc

            for iTableBlockNum in range(inodeTableLoc, inodeTableLoc + ceil((inodesPerGroup * inodeSize) / blockSize)):
                blockTypeMap.update({iTableBlockNum:"iTableBlock"})

            for dBitmapBlockNum in range(groupDescriptor.blockBitMapLoc, groupDescriptor.blockBitMapLoc + ceil(blocksPerGroup / (blockSize * 8))):
                blockTypeMap.update({dBitmapBlockNum:"dBitmapBlock"})

            for iBitmapBlockNum in range(groupDescriptor.inodeBitMapLoc, groupDescriptor.inodeBitMapLoc + ceil(inodesPerGroup / (blockSize * 8))):
                blockTypeMap.update({iBitmapBlockNum:"iBitmapBlock"})

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
            data : bytes
                The bytes contained on the journal block which was read.
        """

        superBlock = structures.super_block.SuperBlock(self.diskO)
        fileSystemJournalInode = structures.read_inode.Inode(self.diskO, superBlock.journalInode, superBlock, False, True)

        # (fileSystemJournalInode.entries[-1].fileBlockNum + fileSystemJournalInode.entries[-1].numBlocks) - 1 is the 
        # last block number in the journal. journalBlockNum is modded with it in order to allow wraparound
        # to the beginning of the journal, incase the journal has wrapped around.
        journalBlockNum = (journalBlockNum % 
            ((fileSystemJournalInode.entries[-1].fileBlockNum + fileSystemJournalInode.entries[-1].numBlocks) - 1))

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

