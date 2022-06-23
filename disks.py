
import re

class Disk:

    def __init__(self, diskPath, diskType):
        self.diskPath = diskPath
        self.diskType = diskType

    def __str__(self):
        return self.diskPath


def getDisks():
    # /proc/mounts contains data on all mounted disk partitions
    mounts = open("/proc/mounts", "r")
    disks = mounts.readlines()

    goodDisks = []

    for disk in disks:
        disk = re.split(" |,", disk)

        if disk[0][0:4] == "/dev" and (disk[2] == "ext4" or disk[2] == "ext3" or disk[2] == "ext2") and disk[3] == "rw":
            goodDisks.append(Disk(disk[0], disk[2]))

    return goodDisks
