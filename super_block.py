
import decode
import disks

class SuperBlock:   

    def __init__(self, diskO):

        # read the data
        disk = open(diskO.diskPath, "rb")
        disk.seek(1024)
        data = disk.read(1024)
        disk.close

        # interpret the data
        decoder = decode.Decoder()

        if diskO.diskType == "ext4" or diskO.diskType == "ext3":
            self.journalInode = decoder.leBytesToDecimal(data, 224, 227)

        if diskO.diskType == "ext4":
            self.groupDescriptorSize = decoder.leBytesToDecimal(data, 254, 255)

        elif diskO.diskType == "ext3" or diskO.diskType == "ext2":
            self.groupDescriptorSize = 32

        self.inodeSize = decoder.leBytesToDecimal(data, 88, 89)
        self.inodesPerGroup = decoder.leBytesToDecimal(data, 40, 43)
        self.blocksPerGroup = decoder.leBytesToDecimal(data, 32, 35)
        self.blockSize = pow(2, (10 + decoder.leBytesToDecimal(data, 24, 27)))
        self.numBlocks = decoder.leBytesToDecimal(data, 4, 7)
        self.numInodes = decoder.leBytesToDecimal(data, 0, 3)

        if self.inodeSize != 256:
            self.inodeSize == 128