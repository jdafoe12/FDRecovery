
class Data:

    def __init__(self):
        return

class DataRun:

    def __init__(self):
        return

class FileName:

    def __init__(self, data, startByte):
        self.name: str = ""

        # I should verify this number
        self.lenName = data[startByte + 63]

        # I need to figure this out. Going backwards because I am assuming little endian order. also assuming that I can append bytes to strings.
        for i in range((self.lenName - 1) + startByte, startByte - 1, - 1):
            self.name = self.name + data[i]


        return
