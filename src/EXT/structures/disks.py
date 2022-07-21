
import re


class Disk:

    """
    Contains data associated with a disk

    Attributes
    ----------
    diskPath : str
        The file path of the disk.
    diskType : str
        The disk type (ext4, ext3, ext2)

    Methods
    -------
    None
    """


    def __init__(self, diskPath, diskType):

        """
        Parameters
        ----------
        diskPath : str
            The path of the disk
        diskType : str
            The filesystem type of the disk
        """
        self.diskPath: str = diskPath
        self.diskType: str = diskType


    def __str__(self):
        return self.diskPath


def getDisks() -> list:

    """
    Gets all valid disks and puts them in a list

    Returns
    -------
    goodDisks : list[Disk]
        A list of all valid disks
    """
    # /proc/mounts contains data on all mounted disk partitions
    mounts = open("/proc/mounts", "r")
    disks: list[str] = mounts.readlines()

    goodDisks: list[Disk] = []

    for disk in disks:
        # The different data fields in /proc/mounts are seperated by " " or ","
        disk: str = re.split(" |,", disk)

        if disk[0][0:4] == "/dev" and (disk[2] == "ext4" or disk[2] == "ext3" or disk[2] == "ext2") and disk[3] == "rw":
            goodDisks.append(Disk(disk[0], disk[2]))

    return goodDisks

