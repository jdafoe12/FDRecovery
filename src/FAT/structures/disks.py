

import os.path

class Disk:

    """
    Contains data associated with a disk.
    
    Attributes
    ----------
    diskPath : str
        The file path of the disk.
    diskType : str
        The disk type (ext4, ext3, ext2).
    """

    def __init__(self, diskPath: str, diskType: str):

        """
        Parameters
        ----------
        diskPath : str
            The path of the disk
        diskType : str
            The filesystem type of the disk.
        """

        self.diskPath = diskPath
        self.diskType = diskType

    def __str__(self):
        return self.diskPath


def getDisks()-> list:

    """
    Gets all valid disks and puts them in a list.

    Returns
    -------
    disks : list[Disk]
        A list of all valid disks
    """

    disks = []

    dl = "ABCDEFGHIJKLMNIPQRSTUVWXYZ"
    drives = ["%s" % d for d in dl if os.path.exists("%s:" % d)]

    for drive in drives:
        disk = open("\\\\.\\" + drive + ":", "rb")
        typeID = disk.read(7)

        typeID = typeID[3:7].decode()


        if typeID != "EXFA" and typeID != "NTFS":
            disk.seek(0x52)
            typeID = disk.read(5)
            typeID = typeID.decode()


        disks.append(Disk("\\\\.\\" + drive + ":", typeID))

    i = 0
    while len(disks) > i:
        if disks[i].diskType != "EXFA" and disks[i].diskType != "FAT32":
            disks.pop(i)
        else:
            i += 1

    return disks
