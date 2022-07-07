
import sys

sys.path.insert(0, "C:/Users/jwdaf/Data_Recovery/DataRecovery/Common")

import boot_sector
import MFT_attributes
import decode
import disks
import MFT_entry


class Recovery:

    def recoverFiles():
        return
    
    def getDeletedFiles(diskName, bootSector: boot_sector):

        mftEntry = MFT_entry.MFTEntry(bootSector.MFTClusterNum, 0, diskName, bootSector, True)

        deletedFiles = []


        currentCluster = 0
        entryNum = 0
        while len(mftEntry.data.dataRuns) > 0: 

            currentRun = mftEntry.data.dataRuns.pop()
            
            currentCluster = currentCluster + currentRun.startingCluster

            for cluster in range(currentCluster, currentRun.numClusters):
                for i in range(0, 5, 2):
                    entry = MFT_entry.MFTEntry(cluster, i, diskName, bootSector, False)
                    if entry.header.isDeleted:
                        deletedFiles.append((entryNum, entry.fileName.name))

                    entryNum += 1

        return deletedFiles

diskList = disks.getDisks()

bootSector = boot_sector.BootSector(diskList[0].diskName)

recovery = Recovery
deletedFiles = recovery.getDeletedFiles(diskName=diskList[0].diskName,bootSector=bootSector)

print(deletedFiles)