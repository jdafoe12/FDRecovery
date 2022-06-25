

import time
from math import floor
import disks

import read_inode
import super_block
import journal
import read_journal


class FileRecoveryJournaled:

    """
    Contains methods directly related to file recovery in journaled filesystems (ext3, ext4).

    Methods
    -------
    recoverFiles(self, diskO: disks.Disk, transactions: list, deletedInodes: list, numToRecover: int, filePath: str)
        Attempts to recover the files that the user has selected.
    getDeletedInodes(self, diskO: disks.Disk, transactions: list)
        Gets a list of all deleted inodes, as recorded in journal deletion transactions.
    readInodeTableBlock(self, diskO: disks.Disk, block: bytes, blockNum: int, superBlock: super_block.SuperBlock)
        Given data from a block, reads all inodes in that
        block and returns a list of the ones which have been deleted.
    """


    #TODO: this method is a bit messy, maybe split into more functions?
    def recoverFiles(self, diskO: disks.Disk, transactions: list[journal.Transaction], deletedInodes: list[tuple], numToRecover: int, outputPath: str):

        """
        Attempts to recover the files that the user has selected.

        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem.
        transactions : list[journal.Transaction]
            List of all transactions in the journal represented as journal.Transaction objects.
            Used to find old versions of the inode which is being recovered.
        deletedInodes : list[tuple]
            List of the inodes which the user selected for recovery.
            inodes in this case are stored as a tuple of the form
            (block num of inode table, offset within inode table, deletion time).
        numToRecover : int
            The number of files in deletedInodes which the user wishes to recover.
        outputPath: str
            The path of the output directory.

        Returns
        -------
        Explicit:
        numRecovered : int
            The number of successfully recovered files.

        Implicit:
        Writes recovered files to outputPath/recoveredFile_%s.
        """

        superBlock: super_block.SuperBlock = super_block.SuperBlock(diskO)
        readJournal: read_journal.ReadJournal = read_journal.ReadJournal(diskO)

        toRecover: list[tuple] = deletedInodes[0:numToRecover]


        numRecovered = 0
        for deletedInode in toRecover:
            for transaction in transactions:

                # if Transaction is not useful, move on
                if transaction.transactionType == 2:
                    continue

                journalBlockNum = transaction.journalBlockNum + 1

                breakFlag = False
                for dataBlock in transaction.dataBlocks:

                    if dataBlock[0] == deletedInode[0]:

                        iTableBlock = readJournal.readJournalBlock(journalBlockNum)
                        inode = read_inode.Inode(diskO, deletedInode[1], superBlock, iTableBlock, True)

                        if inode.hasBlockPointers:

                            numRecovered += 1

                            recoveredFile = open("%s/recoveredFile_%s" % (outputPath, (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(deletedInode[2])) + f"_num_{numRecovered}")), "ab")

                            for entry in inode.entries:
                                disk = open(diskO.diskPath, "rb")
                                disk.seek(superBlock.blockSize * entry.blockNum)

                                for i in range(0, entry.numBlocks):
                                    recoveredFile.write(disk.read(superBlock.blockSize))
                                
                                disk.close
                            recoveredFile.close

                            breakFlag = True
                            break

                    journalBlockNum += 1

                if breakFlag:
                    break

        return numRecovered

    def getDeletedInodes(self, diskO: disks.Disk, transactions: list[journal.Transaction]):

        """
        Gets a list of all deleted inodes, as recorded in journal deletion transactions.

        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem.
        transactions : list[journal.Transaction]
            Used to look at each deletion transaction for the inodes which were deleted.

        Returns
        -------
        Explicit:
        deletedInodes : list[tuple]
            List of the deleted inodes in journal deletion transactions.
            inodes in this case are stored as a tuple of the form
            (block num of inode table, offset within inode table, deletion time).

        Implicit:
        None
        """

        superBlock = super_block.SuperBlock(diskO)
        readJournal = read_journal.ReadJournal(diskO)

        deletionTransactions: list[journal.Transaction] = []

        for transaction in transactions:
            if transaction.transactionType == 0:
                deletionTransactions.append(transaction)

        deletedInodes: list = []

        for transaction in deletionTransactions:

            blockBuffer = 1
            for block in transaction.dataBlocks:

                if block[1] == "iTableBlock":

                    blockData = readJournal.readJournalBlock(transaction.journalBlockNum + blockBuffer)

                    for inode in self.readInodeTableBlock(diskO, blockData, block[0], superBlock):
                        # gather data to make this number make more sense. average difference + 1 standard deviation
                        if transaction.commitTime - inode[2] < 12:
                            deletedInodes.append(inode)

                blockBuffer += 1

        deletedInodes.sort(key=lambda inode: -inode[2])

        return deletedInodes


    def readInodeTableBlock(self, diskO: disks.Disk, block: bytes, blockNum: int, superBlock: super_block.SuperBlock):

        """
        Given data from a block, reads all inodes in that
        block and returns a list of the ones which have been deleted.
        Is a helper function for getDeletedInodes.

        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem.
        block : bytes
            The bytes in the inode table block which will be read.
        blockNum : int
            The block number of the block contained in block.
        superBlock : super_block.SuperBlock
            The super block associated with the filesystem.

        Returns
        -------
        Explicit:
        deletedInodes : list[tuple]
            List of all deleted inodes in this inode table block.
             inodes in this case are stored as a tuple of the form
            (block num of inode table, offset within inode table, deletion time).

        Implicit:
        None
        """

        deletedInodes: list = []

        numInodesInBlock = floor(superBlock.blockSize / superBlock.inodeSize)

        for inodeNum in range(0, numInodesInBlock):

            inode = read_inode.Inode(diskO, inodeNum, superBlock, block, False)


            if inode.deletionTime > 0 and not inode.hasBlockPointers:
                # each deleted inode is represented as a tuple(inode table block num, inode number within the table block starting at 0, inode deletion time)
                deletedInodes.append((blockNum, inodeNum, inode.deletionTime))

        return deletedInodes
        
