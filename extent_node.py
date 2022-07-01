

import decode


class ExtentNode:

    """
    Contains data associated with nodes in the ext4 extent tree.

    Attributes
    ----------
    header : ExtentHeader
        The extent header object associated with the node.
    entries : list[ExtentEntry]
        A list of the extent entry objects contained within the node.
        This list will only be populated if header.extentDepth == 0.
    indices : list[ExtentIndex]
        A list of the extent index objects contained within the node.
        This list will only be populated if header.extentDepth > 0.
    """


    def __init__(self, data: bytes):

        """
        Parameters
        ----------
        data : bytes
            The bytes in the extent node.
            This data is decoded and interpreted to initialize all data.
        """

        self.header: ExtentHeader = ExtentHeader(data[0:12])

        self.entries: list[ExtentEntry] = list()
        self.indices: list[ExtentIndex] = list()

        # if node depth in the extent tree is > 0, the entries in this node are struct ext4_extent_idx.
        if self.header.extentDepth > 0:
            for i in range(0, self.header.numEntriesInExtent):
                self.indices.append(ExtentIndex(data[12 + (12 * i):(12 + (12 * i)) + 12]))
        
        # if node depth in the extent tree is 0, the entries in this node are struct ext4_extent.
        elif self.header.extentDepth == 0:
            for i in range(0, self.header.numEntriesInExtent):
                self.entries.append(ExtentEntry(data[12 + (12 * i):(12 + (12 * i)) + 12]))

        
class ExtentHeader:

    """
    Contains data associated with extent node headers in the ext4 extent tree.
    Represents struct ext4_extent_header.

    Attributes
    ----------
    numEntriesInExtent : int
        The number of entries in the extent node.
    maxEntries : int
        The maximum number of entries which fit in the extent node.
    extentDepth : int
        An integer value indicating the depth of this extent node in the extent tree.
    """


    def __init__(self, data: bytes):

        """
        Parameters
        ----------
        data : bytes
            The bytes in the extent header.
            The bytes are decoded and interpreted to initialize all data.
        """

        decoder = decode.Decoder()

        self.numEntriesInExtent: int = decoder.leBytesToDecimal(data, 2, 3)
        self.maxEntries: int = decoder.leBytesToDecimal(data, 4, 5)
        self.extentDepth: int = decoder.leBytesToDecimal(data, 6, 7)


class ExtentEntry:

    """
    Contains data associated with an extent entry within an extent node in the ext4 extent tree.
    Represents struct ext4_extent.

    Attributes
    ----------
    fileBlockNum : int
        The block number which the first block pointer is associated with,
        relative to the beginning of the file.
    numBlocks : int
        The number of blocks which this extent entry refers to.
    blockNum : int
        The first block number in a contiguous
        run of blocks (with length numBlocks) which this extent entry refers to.
    """


    def __init__(self, data: bytes):

        """
        Parameters
        ----------
        data : bytes
            The bytes in the extent header.
            The bytes are decoded and interpreted to initialize all data.
        """

        decoder = decode.Decoder()

        self.fileBlockNum: int = decoder.leBytesToDecimal(data, 0, 3)
        self.numBlocks: int = decoder.leBytesToDecimal(data, 4, 5)
        self.blockNum: int = decoder.leBytesToDecimalLowerAndUpper(data, 8, 11, 6, 7)


class ExtentIndex:

    """
    Contains data associated with an extent index within an extent node in the ext4 extent tree.
    Represents struct ext4_extent_idx

    Attributes
    ----------
    fileBlockNum : int
        The block number which the first block pointer is associated with,
        relative to the beginning of the file.
    nextNodeBlockNum : int
        The block number which this index points to.
        This block contains another extent node.
    """


    def __init__(self, data: bytes):

        """
        Parameters
        ----------
        data : bytes
            The bytes in the extent header.
            The bytes are decoded and interpreted to initialize all data.
        """

        decoder = decode.Decoder()

        self.fileBlockNum: int = decoder.leBytesToDecimal(data, 0, 3)
        self.nextNodeBlockNum: int = decoder.leBytesToDecimalLowerAndUpper(data, 4, 7, 8, 9)

        