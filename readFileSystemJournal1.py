
from Decoder import Decoder
from GroupDescriptor import GroupDescriptor
from Inode import Inode
from SuperBlock import SuperBlock
from ExtentNode import *

fileSystemName = "/dev/sda5"


superBlock = SuperBlock(fileSystemName)

fileSystemJournalInode = Inode(fileSystemName, superBlock.getJournalInode(), superBlock, False)

# for entry in fileSystemJournalInode.entries:

journal = open("fileSystemJournal.txt", "ab")

for entry in fileSystemJournalInode.entries:
    disk = open(fileSystemName, "rb")
    disk.seek(superBlock.getBlockSize() * entry[2])
    for i in range(0, entry[1]):
        journal.write(disk.read(superBlock.getBlockSize()))

    disk.close

journal.close