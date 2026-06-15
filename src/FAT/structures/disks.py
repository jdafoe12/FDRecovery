import glob
import os
import os.path

class Disk:

    """
    Contains data associated with a disk.

    Attributes
    ----------
    diskPath : str
        The file path of the disk.
    diskType : str
        The disk type (EXFA or FAT32).
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


def getDiskType(diskPath: str):

    """
    Gets the supported FAT-family filesystem type from a disk boot sector.

    Parameters
    ----------
    diskPath : str
        The raw disk or partition path to inspect.

    Returns
    -------
    str | None
        EXFA for exFAT, FAT32 for FAT32, or None for unsupported paths.
    """

    try:
        disk = open(diskPath, "rb")
        data = disk.read(512)
        disk.close()
    except OSError:
        return None

    if len(data) < 512:
        return None

    if data[3:11] == b"EXFAT   ":
        return "EXFA"

    if data[0x52:0x57] == b"FAT32":
        return "FAT32"

    return None


def getWindowsDiskPaths() -> list:

    """
    Gets candidate raw drive paths on Windows.
    """

    dl = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    drives = ["%s" % d for d in dl if os.path.exists("%s:" % d)]

    return ["\\\\.\\" + drive + ":" for drive in drives]


def getLinuxDiskPaths() -> list:

    """
    Gets candidate raw partition paths on Linux.
    """

    candidates = []

    for pattern in [
        "/dev/disk/by-label/*",
        "/dev/disk/by-uuid/*",
        "/dev/disk/by-id/*",
        "/dev/disk/by-path/*",
        "/dev/mapper/*",
        "/dev/sd*[0-9]",
        "/dev/nvme*n*p*",
        "/dev/mmcblk*p*",
        "/dev/loop*p*",
    ]:
        candidates.extend(glob.glob(pattern))

    try:
        mounts = open("/proc/mounts", "r")
        for line in mounts:
            device = line.split(" ", 1)[0]
            if device.startswith("/dev/"):
                candidates.append(device)
        mounts.close()
    except OSError:
        pass

    return candidates


def getCandidateDiskPaths() -> list:

    """
    Gets candidate raw disk paths for the current platform.
    """

    if os.name == "nt":
        return getWindowsDiskPaths()

    if os.name == "posix":
        return getLinuxDiskPaths()

    return []


def getDisks()-> list:

    """
    Gets all valid disks and puts them in a list.

    Returns
    -------
    disks : list[Disk]
        A list of all valid disks
    """

    disks = []
    seen = set()

    for diskPath in getCandidateDiskPaths():
        realPath = os.path.realpath(diskPath)
        if realPath in seen:
            continue

        typeID = getDiskType(diskPath)
        if typeID == "EXFA" or typeID == "FAT32":
            disks.append(Disk(diskPath, typeID))
            seen.add(realPath)

    return disks
