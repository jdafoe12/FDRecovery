

from src.FAT import structures
from src.FAT import directory_tree
import os

class Recovery:
    def recoverFiles(self, diskO: structures.disks.Disk, deletedFiles, outputDir):
        #FAT32 files have attr name, firstClust, dataLen, isFull

        bootSector = structures.boot_sector.BootSector(diskO)
        bytesPerCluster = bootSector.bytesPerSector * bootSector.sectorsPerCluster

        if diskO.diskType == "EXFA":
            firstClusterLoc = (bootSector.clusterHeapOffset * bootSector.bytesPerSector)
        elif diskO.diskType == "FAT32":
            firstClusterLoc = bootSector.bytesPerSector * (bootSector.reservedSectors + (bootSector.sectorsPerFAT * bootSector.numFATs))

        for file in deletedFiles:
            disk = open(diskO.diskPath, "rb")
            newFilePath = "%s/recoveredFile_%s" % (outputDir, file.name)

            recoveredFile = open(newFilePath, "wb")

            if diskO.diskType == "EXFA":
                for clustRun in file.clustRuns:
                    disk.seek((bytesPerCluster * (clustRun[0] - 2)) + firstClusterLoc)
                    recoveredFile.write(disk.read(clustRun[1]))
            elif diskO.diskType == "FAT32":
                disk.seek(bytesPerCluster * (file.startingClust - 2) + firstClusterLoc)
                recoveredFile.write(disk.read(file.dataLen))

            disk.close
            recoveredFile.close

        return len(deletedFiles)

    def getDeletedFiles(self, diskO: structures.disks.Disk, bootSector: structures.boot_sector.BootSector):
        if diskO.diskType == "EXFA":
            return self.exFATGetDeleted(diskO, bootSector)
        elif diskO.diskType == "FAT32":
            return self.FAT32GetDeleted(diskO, bootSector)

    def FAT32GetDeleted(self, diskO: structures.disks.Disk, bootSector: structures.boot_sector.BootSector):
        bytesPerCluster = bootSector.bytesPerSector * bootSector.sectorsPerCluster
       
        firstClusterLoc = bootSector.bytesPerSector * (bootSector.reservedSectors + (bootSector.sectorsPerFAT * bootSector.numFATs))

        rootDirOffset = firstClusterLoc + (bytesPerCluster * (bootSector.rootDirectoryCluster - 2))

        

        disk = open(diskO.diskPath, "rb")
        disk.seek(rootDirOffset)
        data = disk.read(bytesPerCluster)

        dirSets = [] # this is a queue of FAT32EntrySet
        deletedFiles = [] # this is a list of FAT32EntrySet

        inRoot = True
        while len(data) > 0:
            numDirs = 0

            currentOffset = 0
            currentEntrySet: list[directory_tree.entries.FAT32Entry] = [] # this is a stack

            while currentOffset < len(data) and data[currentOffset] > 0:

                currentEntrySet.append(directory_tree.entries.FAT32Entry(data[currentOffset:currentOffset + 32]))
                currentOffset += 32
                
                if not currentEntrySet[-1].isLongName:
                    if currentEntrySet[-1].isDir:
                        if not inRoot and numDirs < 2:
                            pass
                        else:
                            dirSets.append(directory_tree.entry_set.FAT32EntrySet(diskO, bootSector, currentEntrySet))
                        numDirs += 1
                    elif currentEntrySet[-1].isDeleted:
                        deletedFiles.append(directory_tree.entry_set.FAT32EntrySet(diskO, bootSector, currentEntrySet))
                    currentEntrySet = []

            data = []
            if len(dirSets) > 0:
                inRoot = False
                dirSet = dirSets.pop(0)
                disk.seek((bytesPerCluster * (dirSet.startingClust - 2)) + firstClusterLoc)
                data = disk.read(bytesPerCluster)
        disk.close

        return deletedFiles


    def exFATGetDeleted(self, diskO: structures.disks.Disk, bootSector: structures.boot_sector.BootSector):

        bytesPerCluster = bootSector.bytesPerSector * bootSector.sectorsPerCluster

        firstClusterLoc = (bootSector.clusterHeapOffset * bootSector.bytesPerSector)         

        rootDirOffset = firstClusterLoc + (bytesPerCluster * (bootSector.rootDirectoryCluster - 2))

        disk = open(diskO.diskPath, "rb")
        disk.seek(rootDirOffset)
        data = disk.read(bytesPerCluster)

        dirSets = []
        deletedFiles = []


        while len(data) > 0:

            currentOffset = 0

            numSeconds = data[1]

            while currentOffset < len(data) and data[currentOffset] > 0:

                numSeconds = data[currentOffset + 1]
                while numSeconds == 0:
                    currentOffset += 32
                    numSeconds = data[currentOffset + 1]

                entrySet = directory_tree.entry_set.EntrySet(data[currentOffset : currentOffset + (32 * (numSeconds + 1))], diskO, bootSector, True)
                currentOffset += 32 * (numSeconds + 1)

                if entrySet.fileDirEntry.isDir:
                    dirSets.append(entrySet)
                elif not entrySet.fileDirEntry.isDir and not entrySet.isInUse:
                    deletedFiles.append(entrySet)

            data = []
            if len(dirSets) > 0:
                dirSet = dirSets.pop(0)
            

                for clustRun in dirSet.clustRuns:
                    disk.seek((bytesPerCluster * (clustRun[0] - 2)) + firstClusterLoc)
                    data = disk.read(clustRun[1])
        disk.close
        return deletedFiles