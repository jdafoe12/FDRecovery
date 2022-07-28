
from src.FAT import structures
from src.FAT import directory_tree

class Recovery:
    def recoverFiles(self, diskName, deletedFiles, outputDir):

        bootSector = structures.boot_sector.BootSector(diskName)
        bytesPerCluster = bootSector.bytesPerSector * bootSector.sectorsPerCluster
        firstClusterLoc = (bootSector.clusterHeapOffset * bootSector.bytesPerSector)

        for file in deletedFiles:
            disk = open(diskName, "rb")
            newFilePath = "%s/recoveredFile_%s" % (outputDir, file.name)
            recoveredFile = open(newFilePath, "wb")

            for clustRun in file.clustRuns:
                disk.seek((bytesPerCluster * (clustRun[0] - 2)) + firstClusterLoc)
                recoveredFile.write(disk.read(clustRun[1]))
            disk.close
            recoveredFile.close
        return len(deletedFiles)

    def getDeletedFiles(self, diskName, bootSector: structures.boot_sector.BootSector):
        # go to root directory. from there, look at all directory entries for all files. 
        # I will need to recursively look at the data for all actual directories 
        # to find files and directories in those directories

        bytesPerCluster = bootSector.bytesPerSector * bootSector.sectorsPerCluster
        firstClusterLoc = (bootSector.clusterHeapOffset * bootSector.bytesPerSector)

        rootDirOffset = firstClusterLoc + (bytesPerCluster * (bootSector.rootDirectoryCluster - 2))

        disk = open(diskName, "rb")
        disk.seek(rootDirOffset)
        data = disk.read(bytesPerCluster)

        dirSets = []
        deletedFiles = []


        while len(data) > 0:

            numSeconds = data[1]
            currentOffset = 0

            while currentOffset < len(data) and data[currentOffset] > 0:
                numSeconds = data[currentOffset + 1]
                while numSeconds == 0:
                    currentOffset += 32
                    numSeconds = data[currentOffset + 1]

                entrySet = directory_tree.entry_set.EntrySet(data[currentOffset : currentOffset + (32 * (numSeconds + 1))], diskName, bootSector, True)
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
                    data.extend(disk.read(clustRun[1]))
        disk.close
        return deletedFiles