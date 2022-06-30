

from math import ceil

import time
import os

import disks
import group_descriptor
import super_block
import decode
import read_inode


class FileRecoveryNoJournal:

    """
    Contains methods directly related to file recovery in filesystems without journals (ext2).

    Methods
    -------
    recoverFiles(self, diskO: disks.Disk, deletedInodes: list[tuple], numToRecover: int, outputPath: str)
        Attempts to recover the files that the user has selected.
    getDeletedInodes(self, diskO: disks.Disk)
        Gets a list of deleted inodes.
    getInodeBitmaps(self, diskO: disks.Disk, superBlock:super_block.SuperBlock)
        Gets a list of block numbers associated with inode bitmaps.
    findHoles(self, diskO: disks.Disk, iBitmap: tuple, superBlock: super_block.SuperBlock)
        Given a list of inode bitmaps, returns the inode numbers which are free and surrounded by used inodes.
        These inodes are likely to be associated with deleted files.
    """

    def recoverFiles(self, diskO: disks.Disk, deletedInodes: list, numToRecover: int, outputPath: str):

        """
        Attempts to recover the files that the user has selected.

        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem.
        deletedInodes: list[tuple]
            List of the inodes which the user selected for recovery.
            inodes in this case are stored as a tuple of the form
            (inode num, inode deletion time).
        numToRecover : int
            The number of files within deletedInodes
            that the user wishes to recover.
        outputPath : str
            The path of the output directory.

        Returns
        -------
        Explicit:
        numRecovered : int
            The number of successfully recovered files.

        Implicit:
        Writes recovered files to outputPath/recoveredFile_%s.
        """

        superBlock = super_block.SuperBlock(diskO)

        toRecover = deletedInodes[0 : numToRecover]

        numRecovered = 0
        for deletedInode in toRecover:

            inode = read_inode.Inode(diskO, deletedInode[0], superBlock, False, True)

            numRecovered += 1

            recoveredFile = open("%s/recoveredFile_%s" % (outputPath, (time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(deletedInode[1])) + f"_num_{numRecovered}")), "ab")

            for entry in inode.entries:
                disk = open(diskO.diskPath, "rb")
                disk.seek(superBlock.blockSize * entry.blockNum)

                for i in range(0, entry.numBlocks):
                    recoveredFile.write(disk.read(superBlock.blockSize))
                                
                disk.close
            recoveredFile.close

        return numRecovered

    # returns a list of deleted inodes as tuple (inode num, inode deletion time)
    def getDeletedInodes(self, diskO: disks.Disk):

        """
        Gets a list of deleted inodes.

        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem.

        Returns
        -------
        Explicit:
        DeletedInodes : list[tuple]
            List of the inodes which the user selected for recovery.
            inodes in this case are stored as a tuple of the form
            (inode num, inode deletion time).

        Implicit:
        None
        """

        # flush filesystem cache
        os.sync()
        drop_caches = open("/proc/sys/vm/drop_caches", "w")
        drop_caches.write("3")
        drop_caches.close()
        # need to add cache flushing somewhere. Maybe write a seperate function for it at this point.
        deletedInodes = []

        superBlock = super_block.SuperBlock(diskO)

        inodeBitmaps = self.getInodeBitmaps(diskO, superBlock)

        for iBitmap in inodeBitmaps:
            holes = self.findHoles(diskO, iBitmap, superBlock)

            for inodeNum in holes[0]:
                inode = read_inode.Inode(diskO, inodeNum, superBlock, False, False)

                if inode.deletionTime != 0:
                    deletedInodes.append((inodeNum, inode.deletionTime))

            for inodeNum in range(holes[1], superBlock.inodesPerGroup - (holes[1] - (iBitmap[1] * superBlock.inodesPerGroup))): # Fix this line?
                print(inodeNum)
                inode = read_inode.Inode(diskO, inodeNum, superBlock, False, False)

                if inode.deletionTime != 0:
                    deletedInodes.append((inodeNum, inode.deletionTime))
                elif inode.deletionTime == 0:
                    break
        
        deletedInodes.sort(key=lambda inode: -inode[1])

        return deletedInodes

    # returns a list of inode bitmaps which are tuple(iBitmapBlockNum, descriptorNum)
    def getInodeBitmaps(self, diskO: disks.Disk, superBlock:super_block.SuperBlock):

        """
        Gets a list of block numbers associated with inode bitmaps.

        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem.
        superBlock : super_block.SuperBlock
            The super block associated with the filesystem.

        Returns
        -------
        Explicit:
        iBitmaps : list[tuple[int, int]]
            A list of inode bitmaps which are of the form tuple(iBitmapBlockNum, descriptorNum).

        Implicit:
        None
        """
        blockSize = superBlock.blockSize
        blocksPerGroup = superBlock.blocksPerGroup
        inodesPerGroup = superBlock.inodesPerGroup

        iBitmaps = []

        for descriptorNum in range(0, int(superBlock.numBlocks / blocksPerGroup)):
            groupDescriptor = group_descriptor.GroupDescriptor(diskO, descriptorNum, superBlock)


            for iBitmapBlockNum in range(groupDescriptor.inodeBitMapLoc, groupDescriptor.inodeBitMapLoc + ceil(inodesPerGroup / (blockSize * 8))):
                iBitmaps.append((iBitmapBlockNum, descriptorNum))
        
        return iBitmaps


    # returns a list [list of hole inodes, first end inode]
    def findHoles(self, diskO: disks.Disk, iBitmap: tuple, superBlock: super_block.SuperBlock):

        """
        Given a list of inode bitmaps, returns the inode numbers which are free and surrounded by used inodes.
        These inodes are likely to be associated with deleted files.

        Parameters
        ----------
        diskO : disks.Disk
            The disk object associated with the filesystem.
        iBitmap : tuple
            A tuple associated with an inode bitmap of the form tuple(iBitmapBlockNum, descriptorNum).
        superBlock : super_block.SuperBlock
            The super block associated with the filesystem.

        Returns
        -------
        Explicit:
            holeInodes : list[list | int]
                The inode numbers which are free and surrounded by used inodes.
                These inodes are likely to be associated with deleted files.
                holeInodes[0] contains a list of Inodes which are likely associated with deleted files.
                holeInodes[1] contains the inode number directly following the last used inode.


        Implicit:
        None
        """

        # Note that inode numbers start at 1
        # This is the first inode number represented in the bitmap
        firstInodeNum = (iBitmap[1] * superBlock.inodesPerGroup) + 1

        # holeInodes[0] contains a list of Inodes which are likely associated with deleted files.
        # holeInodes[1] contains the inode number directly following the last used inode
        holeInodes = [[]]

        disk = open(diskO.diskPath, "rb")
        disk.seek(superBlock.blockSize * iBitmap[0])
        bytes = disk.read(ceil(superBlock.inodesPerGroup / 8))
        disk.close

        decoder = decode.Decoder

        bits = decoder.leBytesToBitArray(self, bytes)

        gapRanges = []

        prevBit = 1
        for i in range(0, len(bits)):
            if bits[i] == 1 and prevBit == 0:
                gapRanges.append((i, 0))
            elif bits[i] == 0 and prevBit == 1:
                gapRanges.append((i - 1, 1))

            prevBit = bits[i]


        prevPosition = (-1, 1)
        for position in gapRanges:
            if prevPosition[1] == 1 and position[1] == 0:
                holeInodes[0].extend(list(range(firstInodeNum + (prevPosition[0] + 1), firstInodeNum + (position[0] - 1))))
            elif position[1] == 1 and position == gapRanges[-1]:
                holeInodes.append(firstInodeNum + (position[0] + 1))
            prevPosition = position

            holeInodes.append(firstInodeNum)

        return holeInodes