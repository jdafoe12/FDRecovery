

class Decoder:

    """
    Decodes byte data into usable forms.

    Methods
    -------
    leBytesToDecimal(self, data: bytes, lower: int, upper: int)
        Converts part of a list of little endian ordered bytes to decimal.
    leBytesToDecimalLowerAndUpper(self, data: bytes, lowerLS: int, lowerMS: int, upperLS: int, upperMS: int)
        Converts a list of little endian ordered bytes,
        with a most significant part and less significant part
        to decimal.
    beBytesToDecimal(self, data: bytes, lower: int, upper: int)
        Converts part of a list of big endian ordered bytes to decimal.
    leBytesToBitArray(self, data: bytes)
        Converts a list of little endian ordered bytes to an array of bits.
    """


    def leBytesToDecimal(self, data: bytes, lower: int, upper: int):

        """
        Converts part of a list of little endian ordered bytes to decimal.

        Parameters
        ----------
        data : bytes
            The data which contains the bytes that will be converted.
        lower : int
            The index within data where the bytes that will be converted start.
        upper : int
            The index within data where the bytes that will be converted end.

        Returns
        -------
        num : int
            The decimal form of the little endian bytes which were converted.
        """

        num: int = 0
        count: int = 0

        for i in range(lower, upper + 1):
            if count > 0:
                num += (data[i] * pow(16, count))
            else:
                num += data[i]

            count += 2

        return num


    def leBytesToDecimalLowerAndUpper(self, data: bytes, LSLower: int, LSUpper: int, MSLower: int, MSUpper: int):

        """
        Converts a list of little endian ordered bytes,
        with a most significant part and less significant part
        to decimal.

        Parameters
        ----------
        data : bytes
            The data which contains the bytes that will be converted.
        LSLower : int
            The index within data where the least significant bytes that will be converted start.
        LSUpper : int
            The index within data where the least significant bytes that will be converted end.
        MSLower : int
            The index within data where the most significant bytes that will be converted start.
        MSUpper : int
            The index within data where the most significant bytes that will be converted end.

        Returns
        -------
        num : int
            The decimal form of the little endian bytes which were converted.
        """
        
        newBytes: bytearray = bytearray()

        for i in range(LSLower, LSUpper + 1):
            newBytes.append(data[i])

        for i in range(MSLower, MSUpper + 1):
            newBytes.append(data[i])

        decoder = Decoder()

        num: int = decoder.leBytesToDecimal(newBytes, 0, len(newBytes) - 1)

        return num


    def beBytesToDecimal(self, data: bytes, lower: int, upper: int):

        """
        Converts part of a list of big endian ordered bytes to decimal.

        Parameters
        ----------
        data : bytes
            The data which contains the bytes that will be converted.
        lower : int
            The index within data where the bytes that will be converted start.
        upper : int
            The index within data where the bytes that will be converted end.

        Returns
        -------
        num : int
            The decimal form of the big endian bytes which were converted.
        """

        num: int = 0
        count = (upper - lower) * 2
        
        for i in range(lower, upper + 1):
            if count > 0:
                num += (data[i] * pow(16, count))
            else:
                num += data[i]

            count -= 2

        return num

    
    def leBytesToBitArray(self, data: bytes):

        """
        Converts a list of little endian ordered bytes to an array of bits

        Parameters
        ----------
        data : bytes
            The data which contains the bytes that will be converted

        Returns
        -------
        Explicit:
        bits : list[int]
            The list of bits which were converted from little endian bytes

        Implicit:
        None
        """

        bits = []

        for byte in data:
            for i in range(0, 8):
                bits.append(byte & 0x01)
                byte = byte >> 1

        return bits

