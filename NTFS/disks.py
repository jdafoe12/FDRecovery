import os.path

class Disk:

    def __init__(self, diskName, diskType):
        self.diskName = diskName
        self.diskType = diskType


def getDisks()-> list:

    disks = []

    dl = "ABCDEFGHIJKLMNIPQRSTUVWXYZ"
    drives = ["%s" % d for d in dl if os.path.exists("%s:" % d)]

    for drive in drives:
        disks.append(Disk("\\\\.\\" + drive + ":", "ntfs"))
    
    return disks