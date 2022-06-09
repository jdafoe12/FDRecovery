# class JournalSuperBlock contains journalBlockSize, numBlocks, firstLogBlock
from Decoder import *


class JournalSuperBlock:
    print()


class Transaction:

    def __init__(self, descriptorData, journalBlockNum, blockTypeMap: dict):

        decoder = Decoder()

        # initialize transaction data fields
        self.transactionNum = decoder.beBytesToDecimal(descriptorData, 8, 11)
        # this is the journal block num of the descriptor block
        self.journalBlockNum = journalBlockNum
        self.commitTime = 0
        # Transaction type 0 is deletion, 1 is useful, 2 is not useful
        self.transactionType = 2
        self.dataBlocks: list = []


        # a few things are assumed in this code. the sizes of the block tags, and the journal block size
        offset = 12
        distance = 28
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
                offset += 16

            else:
                offset += 32

            distance = (offset + 16)
            numBlocks += 1


        # determine the transaction type
        # this is very basic right now. This algorithm only works when the number of files deleted within the transaction is not too large
        blockTypesInOrder: list = []

        for block in self.dataBlocks:
            blockTypesInOrder.append(block[1])


        if blockTypesInOrder[0:3] == ["unknownBlock", "iTableBlock", "unknownBlock"]:
            self.transactionType = 0

        elif "iTableBlock" in blockTypesInOrder:
            self.transactionType = 1