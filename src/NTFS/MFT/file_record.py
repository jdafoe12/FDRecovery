

from src.NTFS import structures
from src.NTFS import MFT
from src import common

class FileRecord:

    """
    Reads and stores necessary metadata in the file record.

    Attributes
    ----------
    header : RecordHeader
        The header associated with the file record.
        Contains useful flags about the file.
    data : MFT.record_attributes.Data
        The object associated with the $DATA attribute for the file.
        Contains all of the data pointers for the file.
    fileName : MFT.record_attributes.FileName
        The object associated with the $FILE_NAME attribute for the file.
        Contains the file name of the file.

    Methods
    -------
    readAttributes(self, data: bytes, readPointers: bool)
        reads the $DATA and $FILE_NAME attributes in the MFT file record.
    """

    def __init__(self, data: bytes, bootSector: structures.boot_sector.BootSector, readPointers: bool, readAllAttr: bool):

        """
        Parameters
        ----------
        data : bytes
            The data bytes for the MFT file record.
        bootSector : structures.boot_sector.BootSector
            The bootSector associated with the disk being used.
        readPointers : bool
            Indicates whether the data pointers should be read.
        readAllAttr : bool
            Indicates whether to read all of the attributes or not.
            If thiis is false, or the file is not deleted, then only the header is read.
        """

        self.header: RecordHeader = RecordHeader(data)
        self.data: MFT.record_attributes.Data = False
        self.fileName: MFT.record_attributes.FileName = False

        if self.header.isDeleted or readAllAttr:
            self.readAttributes(data[self.header.length:], readPointers)


    def readAttributes(self, data: bytes, readPointers: bool):
        decoder = common.decode.Decoder()

        currentByte = 0
        while currentByte + 7 < len(data):
            attributeType = decoder.leBytesToDecimal(data, currentByte, currentByte + 3)
            attributeSize = decoder.leBytesToDecimal(data, currentByte + 4, currentByte + 7)
            if attributeType == 48:
                self.fileName = MFT.record_attributes.FileName(data, currentByte)
                if self.fileName.name == False:
                    self.fileName = False
            elif attributeType == 128 and readPointers:
                self.data = MFT.record_attributes.Data(data, currentByte, attributeSize)
            elif attributeType > 256:
                break
            elif self.fileName is not False and readPointers is False:
                break
            elif self.data is not False and self.fileName is not False:
                break
            if attributeSize == 0:
                break
            currentByte += attributeSize

class RecordHeader:

    """
    Reads data associated with a file record header.

    Attributes
    ----------
    length : int
        The length in bytes of the header.
    isDeleted : bool
        A flag indicating whether the record entry is associated with a deleted file, or not.
    """

    def __init__(self, data: bytes):

        """
        Parameters
        ----------
        data : bytes
        The data bytes associated with the record header.
        """

        decoder = common.decode.Decoder()

        self.length: int = decoder.leBytesToDecimal(data, 20, 20)
        self.isDeleted: bool = False
        flags = []

        flags.extend(data[22:24])
        flags = flags[0]
        if (data[22]) == 0:
            self.isDeleted = True
