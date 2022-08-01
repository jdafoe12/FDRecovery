

import os.path

class Disk:

    def __init__(self, diskPath, diskType):
        self.diskPath = diskPath
        self.diskType = diskType

    def __str__(self):
        return self.diskPath


def getDisks()-> list:

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