

from src import common

class BootSector:

    """
    Reads the metadata from the bootSector in a NTFS drive

    Attributes
    ----------
    sectorSize : int
        The size in bytes per sector.
    sectorsPerCluster : int
        The number of sectors in each NTFS cluster.
    MFTClusterNum : int
        The cluster number of the MFT.
        Note that the first cluster is actually number 2
        meaning that this must be accounted for when using this value.
    """

    def __init__(self, diskPath):

        """
        Parameters
        ----------
        diskPath : str
            The path of the disk in use.
        """

        decoder = common.decode.Decoder()

        disk = open(diskPath, "rb")
        data = disk.read(512)
        disk.close

        self.sectorSize: int = decoder.leBytesToDecimal(data, 0x0B, 0x0C)
        self.sectorsPerCluster: int = decoder.leBytesToDecimal(data, 0x0D, 0x0E)
        self.MFTClusterNum: int = decoder.leBytesToDecimal(data, 0x30, 0x37)
