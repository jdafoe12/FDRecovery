
from src import common
from src.FAT import directory_tree
from src.FAT import structures

class EntrySet:
    
    def __init__(self, data: bytes, diskName, bootSector: structures.boot_sector.BootSector, readPointers: bool):



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
            for name in nameEntries:
                self.name = self.name + name.name


            if readPointers:
                self.clustRuns = self.getClustRuns(diskName, bootSector)
        else:
            return

    def getClustRuns(self, diskName, bootSector: structures.boot_sector.BootSector):
        
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
                        currentClust = self.getFatPointer(diskName, bootSector, currentClust)

                clustRuns.append((firstRunClust, runSize))

        return clustRuns

    def getFatPointer(self, diskName, bootSector: structures.boot_sector.BootSector, clustNum):

        decoder = common.decode.Decoder

        fatOffset = bootSector.fatOffset * bootSector.bytesPerSector
        clustOffset = clustNum * 8

        disk = open(diskName, "rb")
        disk.seek(fatOffset + clustOffset)
        data = disk.read(8)

        pointer = decoder.beBytesToDecimal(pointer, 0, 7)

        return pointer

