
from src import common
from src.FAT.structures import disks

class BootSector:

    """
    Reads the metadata from the bootSector in a FAT32 or exFAT drive.
    The data is different for FAT32 and exFAT filesystems.

    Atributes
    ---------
    fatOffset : int
        The number of sectors by which the FAT is offset in exFAT.
    clusterHeapOffset : int
        The number of sectors by which the data heap is offset in exFAT.
    rootDirectoryCluster : int
        The cluster number of the root directory.
    bytesPerSector : int
        The number of bytes in each disk sector.
    sectorsPerCluster : int
        The number of sectors in each cluster.
    reservedSectors : int
        The number of sectors reseved for system information in FAT32.
    numFATs : int
        The number of FATs in FAT32. There are typically 2, for redundancy.
    sectorsPerFAT : int
        The number of sectors in each FAT in FAT32.
    """

    def __init__(self, diskO: disks.Disk):

        """
        Parameters
        ----------
        diskO : disks.Disk
            The disk associated with the boot sector being read.
        """

        decoder = common.decode.Decoder()

        disk = open(diskO.diskPath, "rb")
        data = disk.read(512)
        disk.close

        if diskO.diskType == "EXFA":
            self.fatOffset: int = decoder.leBytesToDecimal(data, 0x50, 0x53)
            self.clusterHeapOffset: int = decoder.leBytesToDecimal(data, 0x58, 0x5B)
            self.rootDirectoryCluster: int = decoder.leBytesToDecimal(data, 0x60, 0x63)
            self.bytesPerSecter: int = pow(2, decoder.leBytesToDecimal(data, 0x6C, 0x6C))
            self.sectorsPerCluster: int = pow(2, decoder.leBytesToDecimal(data, 0x6D, 0x6D))
        elif diskO.diskType == "FAT32":
            self.bytesPerSector: int = decoder.leBytesToDecimal(data, 0x0B, 0x0C)
            self.sectorsPerCluster: int = decoder.leBytesToDecimal(data, 0x0D, 0x0D)
            self.reservedSectors: int = decoder.leBytesToDecimal(data, 0x0E, 0x0F)
            self.numFATs: int = decoder.leBytesToDecimal(data, 0x10, 0x10)
            self.sectorsPerFAT: int = decoder.leBytesToDecimal(data, 0x24, 0x27)
            self.rootDirectoryCluster: int = 2
