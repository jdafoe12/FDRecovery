
from math import ceil

from src import common
from src.FAT import directory_tree
from src.FAT import structures

class EntrySet:
    
    def __init__(self, data: bytes, diskO: structures.disks.Disk, bootSector: structures.boot_sector.BootSector, readPointers: bool):



        self.fileDirEntry = directory_tree.entries.FileDirEntry
        self.streamExtEntries = []
        nameEntries = []

        if data[0] == 0x85 or data[0] == 0x05:
            self.fileDirEntry = directory_tree.entries.FileDirEntry(data[0:32])
            self.isInUse = self.fileDirEntry.isInUse

            for i in range(32, (32 * self.fileDirEntry.numSeconds) + 1, 32):
                if data[i] == 0xC0 or data[i] == 0x40:
                    self.streamExtEntries.append(directory_tree.entries.StreamExtEntry(data[i: i + 32]))
                    nameLen = self.streamExtEntries[0].nameLen
                elif data[i] == 0xC1 or data[i] == 0x41:
                    if nameLen > 30:
                        nameEntries.append(directory_tree.entries.NameEntry(data[i: i + 32], 30))
                        nameLen -= 30
                    else: 
                        nameEntries.append(directory_tree.entries.NameEntry(data[i: i + 32], nameLen))

            self.name = ""
            tempName = ""
            for name in nameEntries:
                tempName = tempName + name.name

            for char in tempName:
                if ord(char) > 0 and ord(char) <= 128:
                    self.name = self.name + char


            if readPointers:
                self.clustRuns = self.getClustRuns(diskO.diskPath, bootSector)
        else:
            return

    def getClustRuns(self, diskO: structures.disks.Disk, bootSector: structures.boot_sector.BootSector):
        
        clustRuns = []

        for streamExt in self.streamExtEntries:
            
            if not streamExt.hasFatChain:
                clustRuns.append((streamExt.firstCluster, streamExt.dataLen))

            else:
                clusterSize = bootSector.bytesPerSector * bootSector.sectorsPerCluster
                runSize = 0
                currentClust = streamExt.firstCluster
                firstRunClust = currentClust
                prevClust = currentClust - 1


                while currentClust < 4294967295:
                    clustRuns.append((firstRunClust, runSize))
                    firstRunClust = currentClust
                    runSize = 0

                    while currentClust == prevClust + 1:
                        runSize += clusterSize
                        prevClust = currentClust
                        # Note: it seems kinda inneficient to do this one pointer at a time.
                        currentClust = self.getFatPointer(diskO.diskPath, bootSector, currentClust)

                clustRuns.append((firstRunClust, runSize))

        return clustRuns

    def getFatPointer(self, diskO: structures.disks.Disk, bootSector: structures.boot_sector.BootSector, clustNum):

        decoder = common.decode.Decoder

        fatOffset = bootSector.fatOffset * bootSector.bytesPerSector
        clustOffset = clustNum * 8

        disk = open(diskO.diskPath, "rb")
        disk.seek(fatOffset + clustOffset)
        data = disk.read(8)

        pointer = decoder.leBytesToDecimal(data, 0, 7)

        return pointer


class FAT32EntrySet:
    def __init__(self, diskO: structures.disks.Disk, bootSector: structures.boot_sector.BootSector, dirSet: list):
        # dirSet is a stack. On top is shortName, followed by whatever longName it has
        startLen = len(dirSet)
        entry: directory_tree.entries.FAT32Entry = dirSet.pop()
        self.startingClust = entry.startingClust
        self.dataLen = entry.dataLen
        tempName = entry.name
        self.name = ""

        while len(dirSet) > 0:
            if len(dirSet) == startLen - 1:
                tempName = ""

            entry = dirSet.pop()
            tempName = tempName + entry.name

        for char in tempName:
            if ord(char) > 0 and ord(char) <= 128:
                self.name = self.name + char

    #     # this is only relevent if the file has been deleted. will always be false otherwise
    #     self.isFull = self.checkFull(diskO, bootSector, self.startingClust, self.dataLen)

    # def checkFull(self, diskO: structures.disks.Disk, bootSector: structures.boot_sector.BootSector, startingClust, dataLen):

    #     bytesPerCluster = bootSector.bytesPerSector * bootSector.sectorsPerCluster

    #     fatOffset = (bootSector.bytesPerSector * bootSector.reservedSectors)
    #     clustOffset = (startingClust) * 4
    #     numClusters = ceil(dataLen / bytesPerCluster)

    #     disk = open(diskO.diskPath, "rb")
    #     # I have stumbled upon a very interesting phenomena. it seems to be the case that
    #     # I cannot seek into anything before the first cluster in the data section. 
    #     # this read will still provide the desired offset.
    #     disk.read(fatOffset + clustOffset)

    #     for i in range(0, numClusters):
    #         pointer = disk.read(4)
    #         if pointer != 0 or pointer != 0xFFFF0F:
    #             disk.close
    #             return False
    #         else:
    #             disk.close
    #             return True


        

