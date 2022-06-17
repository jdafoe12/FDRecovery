

import time
from math import floor

import read_inode
import super_block
import journal
import read_journal


class FileRecovery:


    def recoverFiles(self, diskO, transactions: list, deletedInodes: list, numToRecover, filePath):

        superBlock = super_block.SuperBlock(diskO)
        readJournal = read_journal.ReadJournal(diskO)

        toRecover = deletedInodes[0:numToRecover]


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
                        inode = inode(diskO, deletedInode[1], superBlock, iTableBlock)

                        if inode.hasBlockPointers:

                            numRecovered += 1

                            recoveredFile = open("%s/recoveredFile_%s" % (filePath, (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(deletedInode[2])) + f"_num_{numRecovered}")), "ab")

                            for entry in inode.entries:
                                disk = open(diskO.diskPath, "rb")
                                disk.seek(superBlock.blockSize * entry.blockNum)

                                for i in range(0, entry.numBlocks):
                                    recoveredFile.write(disk.read(superBlock.blockSize))

                            breakFlag = True
                            break

                    journalBlockNum += 1

                if breakFlag:
                    break

        return numRecovered

    def getDeletedInodes(self, diskO, transactions: list):

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
                        if transaction.commitTime - inode[2] < 12:
                            deletedInodes.append(inode)

                blockBuffer += 1

        deletedInodes.sort(key=lambda inode: -inode[2])

        return deletedInodes


    def readInodeTableBlock(self, diskO, block: bytes, blockNum, superBlock: super_block.SuperBlock):

        deletedInodes: list = []

        numInodesInBlock = floor(superBlock.blockSize / superBlock.inodeSize)

        for inodeNum in range(0, numInodesInBlock):

            inode = read_inode.Inode(diskO, inodeNum, superBlock, block)


            if inode.deletionTime > 0 and not inode.hasBlockPointers:
                # each deleted inode is represented as a tuple(inode table block num, inode number within the table block starting at 0, inode deletion time)
                deletedInodes.append((blockNum, inodeNum, inode.deletionTime))

        return deletedInodes
        
