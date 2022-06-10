
from time import sleep
import Disks
from Inode import Inode
from SuperBlock import SuperBlock
from ExtentNode import *
import os

disks = Disks.getDisks()

print("Available disks: ", end="")

for disk in disks:
    print(disk.diskPath, end=" ")
print("\n")

diskName = input("Choose disk to get copy of journal from: ")

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
    
    superBlock = SuperBlock(diskName)
    fileSystemJournalInode = Inode(diskName, superBlock.journalInode, superBlock, False)

    for entry in fileSystemJournalInode.entries:
        disk = open(diskName, "rb")
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