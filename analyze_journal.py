

from distutils.log import error
from multiprocessing.sharedctypes import Value
import disks
import read_journal

def analyzeJournal():
    diskList = disks.getDisks()

    print("Available disks: ", end="")

    for disk in diskList:
        print(disk.diskPath, end=" ")
    print("\n")


    while True:
        diskName = input("Choose disk to read journal from: ")

        for disk in diskList:
            if disk.diskPath == diskName:
                currentDisk = disk

        try:
            readJournal = read_journal.ReadJournal(currentDisk)
            break
        except UnboundLocalError:
            print("Invalid disk path, try again.")


    transactions = readJournal.readFileSystemJournal()

    transactionsInJournalOrder = transactions.copy()

    transactionsInTransactionOrder = sorted(transactions, key=lambda transaction: transaction.transactionNum)

    numTransactions = len(transactions) - 1

    firstTransactionNum = transactionsInTransactionOrder[0].transactionNum
    latestTransactionNum = transactionsInTransactionOrder[-1].transactionNum


    loop = True

    while loop:

        while True:
            try:
                order = int(input("Search by journal order or transaction order (0 or 1 respectively)? "))
                break
            except ValueError:
                print("Invalid input. Please enter 0 or 1")

        readN = 0

        if order == 0:
            while True:
                try:
                    while True:
                        try:
                            journalTransactionNum = int(input(f"Which transaction would you like to start at (0 to {numTransactions})? "))
                            break
                        except ValueError:
                            print("Invalid input. please enter an integer value")

                    while True:
                        try:
                            readN = int(input("How many transactions would you like to see? "))
                            break
                        except ValueError:
                            print("Invalid input. Please enter an integer value")
                        
                    
                    for i in range(journalTransactionNum, journalTransactionNum + readN):
                        for dashes in range(0, 150):
                            print("-", end="")
                        print()
                        print(transactionsInJournalOrder[i])
                        for dashes in range(0, 150):
                            print("-", end="")
                        print()

                    break
                except IndexError:
                    print("Transaction number out of range, try again.")

        elif order != 0:

            while True:
                try:
                    while True:
                        try:
                            transactionNum = int(input(f"Which transaction would you like to start at ({firstTransactionNum} to {latestTransactionNum})? "))
                            break
                        except ValueError:
                            print("Invalid input. Please enter an integer value")

                    while True:
                        try:
                            readN = int(input("How many transactions would you like to see? "))
                            break
                        except ValueError:
                            print("Invalid input. Please enter an integer value")

                    index = 0
                    for transaction in transactionsInTransactionOrder:
                        if transaction.transactionNum == transactionNum:
                            break
                        index += 1

                    for i in range(index, index + readN):
                        for dashes in range(0, 150):
                            print("-", end="")
                        print()
                        print(transactionsInTransactionOrder[i])
                        for dashes in range(0, 150):
                            print("-", end="")
                        print()
                    
                    break
                except IndexError:
                    print("Transaction number out of range, try again.")

        while True:
            try:
                isContinue = int(input("0 to quit, 1 to continue: "))
                break
            except ValueError:
                print("Invalid input. Please enter 0 or 1")

        if isContinue == 0:
            loop = False

if __name__  == "__main__":
    analyzeJournal()