

class Decoder:

    def leBytesToDecimal(self, data, lower, upper):

        num = 0
        count = 0
        for i in range(lower, upper + 1):
            if count > 0:
                num += (data[i] * pow(16, count))

            else:
                num += data[i]

            count += 2

        return num


    def leBytesToDecimalLowerAndUpper(self, data, lowerLower, lowerUpper, upperLower, upperUpper):
        
        newBytes: bytearray = bytearray()

        num = 0
        count = 0
        for i in range(lowerLower, lowerUpper + 1):
            newBytes.append(data[i])

        for i in range(upperLower, upperUpper + 1):
            newBytes.append(data[i])

        decoder = Decoder()

        return decoder.leBytesToDecimal(newBytes, 0, len(newBytes) - 1)


    def beBytesToDecimal(self, data, lower, upper):

        num = 0
        count = (upper - lower) * 2
        for i in range(lower, upper + 1):
            if count > 0:
                num += (data[i] * pow(16, count))

            else:
                num += data[i]

            count -= 2

        return num

    
    def leBytesToBitArray(self, data):

        bits = []

        for byte in data:
            for i in range(0, 8):
                bits.append(byte & 0x01)
                byte = byte >> 1

        return bits

