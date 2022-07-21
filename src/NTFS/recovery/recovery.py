
from math import floor
import sys

sys.path.insert(0, "C:/Users/jwdaf/Data_Recovery/DataRecovery/Common")

from src.NTFS import structures
from src.NTFS import MFT


class Recovery:

    def recoverFiles(self, diskName, deletedFiles, outputDir):

        bootSector = structures.boot_sector.BootSector(diskName)

        for file in deletedFiles:
            entry = MFT.file_record.FileRecord(file[0], bootSector, True, False)

            disk = open(diskName, "rb")
            recoveredFile = open("%s/recoveredFile_%s" % (outputDir, file[1]), "wb")

            currentCluster = 0
            while len(entry.data.dataRuns) > 0:
                currentRun = entry.data.dataRuns.pop(0)
                currentCluster = currentCluster + currentRun.startingCluster
                for clusterNum in range(0, currentRun.numClusters):
                    disk.seek((bootSector.sectorsPerCluster * (currentCluster + clusterNum)) * bootSector.sectorSize)
                    recoveredFile.write(disk.read(bootSector.sectorSize * bootSector.sectorsPerCluster))
        recoveredFile.close
        disk.close
        return len(deletedFiles)
    
    
    def getDeletedFiles(self, diskName, bootSector: structures.boot_sector):

        clusterSize = bootSector.sectorsPerCluster * bootSector.sectorSize

        # Read the file record for the MFT, which provides the location on disk of the remainder of the MFT
        disk = open(diskName, "rb")
        disk.seek(clusterSize * bootSector.MFTClusterNum)
        # 1024 is the length (in bytes) of a file record
        fileRecordData = disk.read(1024)
        fileRecord = MFT.file_record.FileRecord(fileRecordData, bootSector, readPointers=True, readAllAttr=True)

        recordsPerCluster = floor(clusterSize / 1024)

        deletedFiles = []

        currentCluster = 0
        while len(fileRecord.data.dataRuns) > 0: 

            currentRun = fileRecord.data.dataRuns.pop(0)

            currentCluster = currentCluster + currentRun.startingCluster

            for clusterOffSet in range(0, currentRun.numClusters):

                for record in range(0, recordsPerCluster):
                    disk.seek(clusterSize * (currentCluster + clusterOffSet) + (1024 * record))
                    entryData: bytes = disk.read(1024)

                    entry = MFT.file_record.FileRecord(entryData, bootSector, False, True)
                    if entry.header.isDeleted:
                        if entry.fileName is not False:
                            deletedFiles.append((entryData, entry.fileName.name))


        return deletedFiles