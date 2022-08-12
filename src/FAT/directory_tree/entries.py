
from src import common


class FileDirEntry:

    """
    Reads metadata from the first directory entry in a directory entry set.

    Attributes
    ----------
    isInUse : bool
        Indicates whether the file/directory is currently in use.
        If it is not currently in use, it is assumed that is has been deleted.
    numSeconds : int
        The number of secondary entries following this one in the file/dir entry set.
    isDir : bool
        A boolean flag indicating whether this entry set is associated with a directory.
        If false, it is assumed that the entry set is associated with a file.
    """

    def __init__(self, data: bytes):

        """
        Parameters
        ----------
        data : bytes
            The data associated with the first directory entry in this directory entry set.
        """

        decoder = common.decode.Decoder

        if data[0] == 0x85:
            self.isInUse: bool = True
        elif data[0] == 0x05:
            self.isInUse: bool = False

        self.numSeconds: int = decoder.leBytesToDecimal(self, data, 1, 1)

        attributes = data[4:6]

        self.isDir: bool = attributes[0] & 0b00010000 == 0b0001000

class StreamExtEntry:

    """
    Reads metadata associated with a stream extension directory entry.

    Attributes
    ----------
    hasFatChain : bool
        A boolean value indicating whether the file/dir associated with
        this stream extension entry has a FAT chain in the FAT.
        If this is true then the file is fragmented and the FAT must be
        read to get all of it's data.
    nameLen : int
        The length in chars of the file/dir name.
    firstCluster : int
        The cluster number of the first cluster associated with the file/dir.
    dataLen : int
        The length in bytes of the file/dir.
    """

    def __init__(self, data: bytes):

        """
        Parameters
        ----------
        data : bytes
            The data associated with the stream extension directory entry.
        """

        decoder = common.decode.Decoder

        flags = data[1]
        # TODO: test whether FAT entries are zeroed out when file is deleted
        self.hasFatChain: bool = flags & 0b01 != 0b01
        self.nameLen: int = decoder.leBytesToDecimal(self, data, 3, 3)
        self.firstCluster: int = decoder.leBytesToDecimal(self, data, 20, 23)
        self.dataLen: int = decoder.leBytesToDecimal(self, data, 24, 31)


class NameEntry:

    """
    Reads the file/dir name from the file name directory entry.

    Attributes
    ----------
    name : str
        The file/dir name.
    """

    def __init__(self, data: bytes, nameLen: int):

        """
        Parameters
        ----------
        data : bytes
            The data associated with the file name directory entry.
        nameLen : int
            The length in chars of the file/dir name within this file name entry.
        """

        if nameLen == 30:
            self.name: str = bytes(data[2:]).decode(encoding="utf-16", errors="strict")
        else:
            self.name: str = bytes(data[2:(nameLen * 2) + 2]).decode(encoding="utf-16", errors="strict")


class FAT32Entry:

    """
    Reads and stores the metadata associated with FAT32 long name and short name directory entries.

    Attributes
    ----------
    isLongName : bool
        Indicates whether this entry is a long or short name directory entry.
        This determines what data the entry will contain.
    name : str
        The name data associated with this directory entry.
    isDeleted : bool
        Indicates whether the file/dir has been deleted.
    isDir : bool
        Indicates whether the file/dir is a directory or file.
    volLabelFlag : bool
        Indicates whether the file/dir is a volume label.
    dataLen : int
        The length in bytes of the file/dir.
    startingClust : int
        The starting cluster number of the file/dir.
    """

    def __init__(self, data: bytes):

        """
        Parameters
        ----------
        data : bytes
            The data associated with the FAT32 entry.
        """

        self.isLongName: bool = data[0x0B] & 0b00001111 == 0b00001111
        self.name: str = ""
        if self.isLongName:
            try:
                self.name = data[0x01 : 0x0B].decode(encoding="utf-16", errors="strict")
                self.name = self.name + data[0x0E : 0x1A].decode(encoding="utf-16", errors="strict")
                self.name = self.name + data[0x1C : ].decode(encoding="utf-16", errors="strict")
            except UnicodeDecodeError:
                self.name = "Name"
        else:
            decoder = common.decode.Decoder

            self.isDeleted: bool = data[0] == 0xE5
            attributes = data[0x0B]
            self.isDir: bool = attributes & 0b00010000 == 0b00010000
            self.volLabelFlag: bool = attributes & 0b00001000 == 0b00001000
            self.dataLen: int = decoder.leBytesToDecimal(self, data, 0x1C, 0x1F)
            self.startingClust: int = decoder.leBytesToDecimalLowerAndUpper(self, data, 0x1A, 0x1B, 0x14, 0x15)
            try:
                self.name = data[0x01 : 0x0B].decode()
            except UnicodeDecodeError:
                self.name = "Name"
