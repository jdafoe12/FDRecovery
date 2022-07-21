
from time import sleep
import os
import re

import structures.disks
import structures.read_inode
import structures.super_block

def getReadableJournalCopy():

    diskList = structures.disks.getDisks()

    print("Available disks: ", end="")

    for disk in diskList:
        print(disk.diskPath, end=" ")
    print("\n")

    while True:
        try:
            diskName = input("Choose disk to get copy of journal from: ")

            for disk in diskList:
                if diskName == disk.diskPath:
                    currentDisk = disk

            superBlock = structures.super_block.SuperBlock(currentDisk)
            break
        except UnboundLocalError:
            print("Invalid disk path, try again.")

    while True:
        try:
            numCopies = int(input("Number of copies: "))
            break
        except ValueError:
            print("Invalid input, please enter an integer value")

    timeDelayInSeconds = 0

    if numCopies > 1:
        
        while True:
            try: 
                timeDelayInSeconds = int(input("Time delay between copies (in seconds)? "))
                break
            except ValueError:
                print("invalid input, please enter an integer value")

    outputPath = input("Output path: ")

    for journalNum in range(0, numCopies):

        while True:
            try:
                journal = open(f"{outputPath}/fileSystemJournal{journalNum}.txt", "w")
                break
            except FileNotFoundError:
                print("Invalid output path, try again")
                outputPath = input("Output path: ")

        # flush filesystem cache
        os.sync()
        drop_caches = open("/proc/sys/vm/drop_caches", "w")
        drop_caches.write("3")
        drop_caches.close()
        
        fileSystemJournalInode = structures.read_inode.Inode(currentDisk, superBlock.journalInode, superBlock, False, True)

        for entry in fileSystemJournalInode.entries:
            disk = open(currentDisk.diskPath, "rb")
            disk.seek(superBlock.blockSize * entry.blockNum)
            for i in range(0, entry.numBlocks):

                numReads = int(superBlock.blockSize / 16)
                for i in range(0, numReads):
                    blockBytesHex = (" ").join(re.findall(".{1,4}", disk.read(16).hex()))
                    journal.write(blockBytesHex + "\n")
                journal.write("\n")
            disk.close

        journal.close
        sleep(timeDelayInSeconds)

if __name__ == "__main__":
    getReadableJournalCopy()