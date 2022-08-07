

from src import common


class Data:

    """
    Reads and stores the the pointers contained within the $DATA attribute.
    The pointers are stores as DataRun objects.

    Attributes
    ----------
    isResident : bool
        Indicates whether the data for this file is contained within the $DATA attribute itself,
        Or if it is somewhere else on disk.
    dataRuns : list
        Contains the pointers to the file's data, stored as DataRun objects.
    """

    def __init__(self, data: bytes, startByte: int, attributeSize: int):

        """
        Parameters
        ----------
        data : bytes
            The data associated with all attributes in the MFT entry.
        startByte : int
            The offset where the $DATA attribute begins
        """

        decoder = common.decode.Decoder()
        self.isResident: bool = False
        if decoder.leBytesToDecimal(data, startByte + 8, startByte + 8) == 0:
            self.isResident = True

        self.dataRuns = []
        currentIndex = decoder.leBytesToDecimal(data, startByte + 32, startByte + 32) + startByte
        while currentIndex - startByte < attributeSize:
            self.dataRuns.append(DataRun(data, currentIndex))
            if self.dataRuns[-1].byteSize > 1:
                currentIndex += self.dataRuns[-1].byteSize
            else:
                self.dataRuns.pop()
                break


class DataRun:

    """
    Reads data runs within the $DATA attribute.

    Attributes
    ----------
    byteSize : int
        The size in bytes of the data run itself.
    numClusters : int
        The number of clusters, starting at startingCluster, that the file data is stored within
    startingCluster : int
        The first cluster number of the file's data.
    """

    def __init__(self, data: bytes, index: int):

        """
        Parameters
        ----------
        data : bytes
            The data associated with the $DATA attribute which contains the data run.
        index : int
            The index within the $DATA attribute of the first byte in the data run.
        """

        decoder = common.decode.Decoder()
        numClustBytes = (data[index] & 0xF0) >> 4
        numLenBytes = data[index] & 0x0F
        self.byteSize: int = numClustBytes + numLenBytes + 1

        self.numClusters: int = decoder.leBytesToDecimal(data, index + 1, index + numLenBytes)
        self.startingCluster: int = int.from_bytes(bytes=data[index + 1 + numLenBytes : index + numLenBytes + numClustBytes + 1], byteorder="little", signed=True)


class FileName:

    """
    Reads and stores the file name stored within the $FILE_NAME attribute.

    Attributes
    ----------
    name: str
        The name of the file.
    lenName : int
        The length in bytes of the fileName.
    """

    def __init__(self, data: bytes, startByte: int):

        """
        Parameters
        ----------

        """

        decoder = common.decode.Decoder()

        header = AttributeHeader(data, startByte)

        tempName = ""

        self.lenName = data[startByte + (header.offSetToAttribute + 0x40)]
        try:
            tempName = data[startByte + (header.offSetToAttribute + 0x42) : startByte + (header.offSetToAttribute + 0x42) + (self.lenName * 2)].decode(encoding="utf-16", errors="strict")
        except UnicodeDecodeError:
            tempName = False

        if type(tempName) is not bool:
            for char in tempName:
                if ord(char) >= 20 and ord(char) <= 128:
                    self.name = self.name + char
        else:
            self.name = False


class AttributeHeader:

    def __init__(self, data: bytes, startByte):

        decoder = common.decode.Decoder()

        isResident = data[startByte + 8] == 0

        self.length = decoder.leBytesToDecimal(data, startByte + 4, startByte + 5)
        if isResident:
            self.offSetToAttribute = decoder.leBytesToDecimal(data, startByte + 0x14, startByte + 0x15)

        elif not isResident:
            self.offSetToAttribute = decoder.leBytesToDecimal(data, startByte + 0x20, startByte + 0x21)
