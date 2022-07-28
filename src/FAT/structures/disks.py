



import os.path

class Disk:

    def __init__(self, diskName, diskType):
        self.diskName = diskName
        self.diskType = diskType

    def __str__(self):
        return self.diskName


def getDisks()-> list:

    disks = []

    dl = "ABCDEFGHIJKLMNIPQRSTUVWXYZ"
    drives = ["%s" % d for d in dl if os.path.exists("%s:" % d)]

    for drive in drives:
        disk = open("\\\\.\\" + drive + ":", "rb")
        typeID = disk.read(7)
        disks.append(Disk("\\\\.\\" + drive + ":", typeID[3:7]))
    
    return disks