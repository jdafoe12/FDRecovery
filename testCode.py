

from Decoder import Decoder
from GroupDescriptor import GroupDescriptor
from Inode import Inode
from ReadJournal import *
from SuperBlock import SuperBlock
from ExtentNode import *
from FileRecovery import *

readJournal = ReadJournal("/dev/sda5")

transactions = readJournal.readFileSystemJournal()

# for transaction in transactions:
#     print(transaction.dataBlocks)

fileRecovery = FileRecovery()

deletedInodes = fileRecovery.getDeletedInodes("/dev/sda5", transactions)

for inode in deletedInodes:
    print(inode)

# print(transactions[7].dataBlocks)
# print(transactions[7].isDeletion)
# print(transactions[7].journalBlockNum)
# print(transactions[7].deletedInodes)

# for transaction in transactions:
#     print(transaction.isDeletion)