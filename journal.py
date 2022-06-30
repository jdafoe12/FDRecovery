

import time

import decode
import disks
import super_block


class JournalSuperBlock:
    
    """
    Contains journal metadata

    Attributes
    ----------
    blockSize : int
        The size of blocks within the journal
    hasCSumv3 : bool
        Indicates whether the journal has the JBD2_FEATURE_INCOMPAT_CSUM_V3 feature
        The structure of block tags is determined by this feature
    """

    def __init__(self, data: bytes):
        decoder = decode.Decoder()

        self.blockSize: int = decoder.beBytesToDecimal(data, 12, 15)
        self.hasCSumV3: bool = data[0x2B] & 0b00010000 == 16


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

    Methods 
    -------
    getBlocks(self, blockTypeMap: dict, data: bytes, journalSuperBlock: JournalSuperBlock, superBlock: super_block.SuperBlock) -> list
        Gets a list of all the blocks, stored as a tuple (blockNum, blockType).
    getTransactionType(dataBlocks: list) -> int
        Given the list of data blocks, determines the transaction type. Returns an int 0-2 indicating this transaction type:
        Transaction type 0 is deletion, 1 is useful, 2 is not useful.


    """

    def __init__(self, descriptorData: bytes, journalBlockNum: int, blockTypeMap: dict, diskO: disks.Disk, journalSuperBlock: JournalSuperBlock, superBlock: super_block.SuperBlock):

        """
        Parameters
        ----------
        descriptorData : bytes
            This is the bytes in which the descriptor block for the transaction is contained
            This is the data which all transaction data is derived from
        journalBlockNum : int
            This is the block number of the descriptor block, relative to the beginning of the journal
        blockTypeMap : dict
            The dictionary which has block numbers associated with metadata block type
            Used to map blocks in the transaction to block types in order to identify the transaction type
        diskO : disks.Disk
            The disk object associated with the filesystem
        journalSuperBlock : JournalSuperBlock
            The super block associated with the journal
        superBlock : super_block.SuperBlock
            The super block associated with the filesystem
        """

        decoder = decode.Decoder()

        # initialize transaction data fields
        self.transactionNum: int = decoder.beBytesToDecimal(descriptorData, 8, 11)
        # this is the journal block num of the descriptor block
        self.journalBlockNum: int = journalBlockNum
        self.commitTime: int = 0
        
        self.dataBlocks: list = self.getBlocks(blockTypeMap, descriptorData[12:], journalSuperBlock, superBlock)

        # Transaction type 0 is deletion, 1 is useful, 2 is not useful
        self.transactionType = self.getTransactionType(self.dataBlocks)

        

    def getTransactionType(self, dataBlocks: list) -> int:

        """
        Given the list of data blocks, determines the transaction type. Returns an int 0-2 indicating this transaction type:
        Transaction type 0 is deletion, 1 is useful, 2 is not useful.

        Parameters
        ----------
        dataBlocks : list
            The list of data blocks in the transaction.
            This algorithm looks at the type of block and the order they are in
            in order to determine transaction type.
        
        Returns
        -------
        transactionType : int
            An int 0-2 indicating this transaction type:
            Transaction type 0 is deletion, 1 is useful, 2 is not useful.
        """

        transactionType: int = 2

        # determine the transaction type
        blockTypesInOrder: list = []
        numITableBlock = 0
        for block in dataBlocks:
            if block[1] == "iTableBlock":
                numITableBlock += 1
            blockTypesInOrder.append(block[1])

        if blockTypesInOrder[0:3] == ["unknownBlock", "iTableBlock", "unknownBlock"]:
            transactionType = 0
        elif numITableBlock > 1 and (blockTypesInOrder[0] == "unknownBlock" or blockTypesInOrder[0] == "iTableBlock") and "dBitmapBlock" in blockTypesInOrder:
            transactionType = 0
        elif numITableBlock > 0:
            transactionType = 1

        return transactionType
    

    def getBlocks(self, blockTypeMap: dict, data: bytes, journalSuperBlock: JournalSuperBlock, superBlock: super_block.SuperBlock) -> list:

        """
        gets a list of all the blocks, stored as a tuple (blockNum, blockType)

        Parameters
        ----------
        blockTypeMap : dict
            The dictionary which has block numbers associated with metadata block type
            Used to map blocks in the transaction to block types in order to identify the transaction type
        data : bytes
            This is the bytes in which the descriptor block for the transaction is contained
            Read in order to get block numbers
        journalSuperBlock : JournalSuperBlock
            The super block associated with the journal
        superBlock : super_block.SuperBlock
            The super block associated with the filesystem

        Returns
        -------
        blocks
            A list of blocks involved in the transaction
        """

        decoder = decode.Decoder()

        blocks: list = []

        if journalSuperBlock.hasCSumV3:
            modifier: int = 32
        elif not journalSuperBlock.hasCSumV3 and not superBlock.bit64:
            modifier: int = 24
        elif not journalSuperBlock.hasCSumV3 and superBlock.bit64:
            modifier: int = 28

        offSet: int = 0
        while True:

            if superBlock.bit64:
                blockNum: int = decoder.beBytesToDecimal(data, offSet, offSet + 3) + (decoder.beBytesToDecimal(data, offSet + 8, offSet + 11) * pow(2, 32))
            else:
                blockNum: int = decoder.beBytesToDecimal(data, offSet, offSet + 3)

            if blockNum in blockTypeMap:
                blocks.append((blockNum, blockTypeMap.get(blockNum)))

            else:
                blocks.append((blockNum, "unknownBlock"))

            UUIDFlag: bool = data[offSet + 7] & 0b00000010 == 0b00000010
            endFlag: bool = data[offSet + 7] & 0b00001000 == 0b00001000
                
            if endFlag:
                break

            offSet += modifier

            if UUIDFlag:
                offSet -= 16

        return blocks


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

