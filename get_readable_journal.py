
from time import sleep
import os

import disks
import read_inode
import super_block

def getReadableJournalCopy():

    diskList = disks.getDisks()

    print("Available disks: ", end="")

    for disk in diskList:
        print(disk.diskPath, end=" ")
    print("\n")

    diskName = input("Choose disk to get copy of journal from: ")

    for disk in diskList:
        if diskName == disk.diskPath:
            currentDisk = disk

    numCopies = int(input("Number of copies: "))

    timeDelayInSeconds = 0

    if numCopies > 1:
        timeDelayInSeconds = int(input("Time delay between copies (in seconds)? "))

    outputPath = input("Output path: ")

    for journalNum in range(0, numCopies):

        journal = open(f"{outputPath}/fileSystemJournal{journalNum}.txt", "w")

        # flush filesystem cache
        os.sync()
        drop_caches = open("/proc/sys/vm/drop_caches", "w")
        drop_caches.write("3")
        drop_caches.close()
        
        superBlock = super_block.SuperBlock(currentDisk)
        fileSystemJournalInode = read_inode.Inode(currentDisk, superBlock.journalInode, superBlock, False)

        for entry in fileSystemJournalInode.entries:
            disk = open(currentDisk.diskPath, "rb")
            disk.seek(superBlock.blockSize * entry.blockNum)
            for i in range(0, entry.numBlocks):

                numReads = int(superBlock.blockSize / 32)
                for i in range(0, numReads):
                    blockBytesHex = disk.read(32).hex()
                    journal.write(blockBytesHex + "\n")
                journal.write("\n")
            disk.close

        journal.close
        sleep(timeDelayInSeconds)

if __name__ == "__main__":
    getReadableJournalCopy()