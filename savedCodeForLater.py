# def readInodeTableBlock(block: bytes, blockNum, deletedInodes: list, superBlock: SuperBlock):
#     numInodesInBlock = floor(superBlock.getBlockSize() / superBlock.getInodeSize())

#     isInodeTable = False

#     for i in range(0, numInodesInBlock):

#         inode = Inode(False, i, superBlock, block)

#         if inode.deletionTime > 0 and not inode.hasExtentTree:
#             # each deleted inode is represented as a tuple (inode table block num, inode number within the table block starting at 0, inode deletion time)
#             deletedInodes.append((blockNum, i, inode.deletionTime))

#         if inode.hasExtentTree:
#             isInodeTable = True
    
#     if len(deletedInodes) > 0:
#         isInodeTable = True

#     return isInodeTable


# # if any files associated with the inodes in the last transaction were deleted
# if len(deletedTransactionInodes) > 0:
#     for iTableDeleted in deletedTransactionInodes:
#         for iDeleted in iTableDeleted:
#             # iDeleted is a deleted inode tuple (inode table block num, inode number within the table block starting at 0, inode deletion time)
#             # the number 12 is subject to change once I better understand what the time range should be
#             if  commitTime - iDeleted[2] < 12:
#                 transactionList[-1].setIsDeletion(True)
#                 transactionList[-1].addDeletedInode(iDeleted)

for i in range(0, 300):
    file = open("/run/media/jdafoe/f3497e19-7976-4e76-bd06-050127653e50/%d" % i, "w")
    file.write("%d" % i)
    file.close()