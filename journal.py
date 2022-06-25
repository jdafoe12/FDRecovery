# class JournalSuperBlock contains journalBlockSize, numBlocks, firstLogBlock
import time
import decode

import disks


class JournalSuperBlock:
    print()


class Transaction:

    """
    Contains the data associated with a journal transaction.

    Attributes
    ----------
    transactionNum : int
        The transaction number associated with the transaction.
    journalBlockNum : int
        The block number of the transaction descriptor block relative to the beginning of the journal.
    commitTime : int
        The time in UNIX time that the transaction was commited to journal.
    transactionType : int
        The type associated with the transaction.
        If this value is 0, then it was a deletion transaction.
        If this value is 1, then this transaction is useful in the file recovery process.
        If this value is 2, then this transaction is not useful in the file recovery process.
    dataBlocks : list
        This is a list of the data blocks associated with the transaction.
        dataBlocks[0] is an int - the block number.
        dataBlocks[1] is a string - the block type.

    """

    def __init__(self, descriptorData: bytes, journalBlockNum: int, blockTypeMap: dict, diskO: disks.Disk):

        decoder = decode.Decoder()

        # initialize transaction data fields
        self.transactionNum: int = decoder.beBytesToDecimal(descriptorData, 8, 11)
        # this is the journal block num of the descriptor block
        self.journalBlockNum: int = journalBlockNum
        self.commitTime: int = 0
        # Transaction type 0 is deletion, 1 is useful, 2 is not useful
        self.transactionType: int = 2
        self.dataBlocks: list = []


        # a few things are assumed in this code. the sizes of the block tags, and the journal block size
        offset = 12
        if diskO.diskType == "ext4":
            distance = 28
        elif diskO.diskType == "ext3":
            distance = 20
        numBlocks = 0
        # loop goes through all block tags within the descriptor
        while (distance < len(descriptorData)) and (decoder.beBytesToDecimal(descriptorData, offset, distance) != 0):
            
            blockNum = decoder.beBytesToDecimal(descriptorData, offset, offset + 3)

            # populate the list of data blocks with all of the data blocks represented by the group descriptor
            if blockNum in blockTypeMap:
                self.dataBlocks.append((blockNum, blockTypeMap.get(blockNum)))

            else:
                self.dataBlocks.append((blockNum, "unknownBlock"))


            # update offset values
            if numBlocks >= 1:
                if diskO.diskType == "ext4":
                    offset += 16
                elif diskO.diskType == "ext3":
                    offset += 8

            else:
                if diskO.diskType == "ext4":
                    offset += 32
                elif diskO.diskType == "ext3":
                    offset += 24

            distance = (offset + 16)
            numBlocks += 1


        # determine the transaction type
        # this is very basic right now. This algorithm only works when the number of files deleted within the transaction is not too large
        blockTypesInOrder: list = []
        numITableBlock = 0
        for block in self.dataBlocks:
            if block[1] == "iTableBlock":
                numITableBlock += 1
            blockTypesInOrder.append(block[1])


        if blockTypesInOrder[0:3] == ["unknownBlock", "iTableBlock", "unknownBlock"]:
            self.transactionType = 0
            
        elif numITableBlock > 1 and (blockTypesInOrder[0] == "unknownBlock" or blockTypesInOrder[0] == "iTableBlock") and "dBitmapBlock" in blockTypesInOrder:
            self.transactionType = 0

        elif numITableBlock > 0:
            self.transactionType = 1


    def __str__(self):
        transactionAsString = f"Transaction Number: {self.transactionNum}\n"

        if self.transactionType == 0:
            transactionAsString += "Transaction Type: Deletion\n\n"
        elif self.transactionType == 1:
            transactionAsString += "Transaction Type: Other Useful (contains an inode table)\n\n"
        elif self.transactionType == 2:
            transactionAsString += "Transaction Type: Not Useful (does not contain an inode table)\n\n"
        
        transactionAsString += "Transaction Data Block(s):\n"
        iteration = 0
        for block in self.dataBlocks:
            if iteration < 2:
                transactionAsString += f"Block Num: {block[0]} Block Type: {block[1]} | "
            elif iteration == 2:
                transactionAsString += f"Block Num: {block[0]} Block Type: {block[1]}"
                transactionAsString += "\n"
            iteration = (iteration + 1) % 3

        if iteration - 1 < 2:
            transactionAsString += "\n\n"

        transactionAsString += f"Commit Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.commitTime))}\n"

        return transactionAsString
