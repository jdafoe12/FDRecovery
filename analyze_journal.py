

import disks
import read_journal

def analyzeJournal():
    diskList = disks.getDisks()

    print("Available disks: ", end="")

    for disk in diskList:
        print(disk.diskPath, end=" ")
    print("\n")

    diskName = input("Choose disk to read journal from: ")

    for disk in diskList:
        if disk.diskPath == diskName:
            currentDisk = disk

    readJournal = read_journal.ReadJournal(currentDisk)

    transactions = readJournal.readFileSystemJournal()

    transactionsInJournalOrder = transactions.copy()

    transactionsInTransactionOrder = sorted(transactions, key=lambda transaction: transaction.transactionNum)

    numTransactions = len(transactions) - 1

    firstTransactionNum = transactionsInTransactionOrder[0].transactionNum
    latestTransactionNum = transactionsInTransactionOrder[-1].transactionNum


    loop = True

    while loop:
        order = int(input("Search by journal order or transaction order (0 or 1 respectively)? "))

        readN = 0

        if order == 0:
            journalTransactionNum = int(input(f"Which transaction would you like to start at (0 to {numTransactions})? "))
            readN = int(input("How many transactions would you like to see? "))

            for i in range(journalTransactionNum, journalTransactionNum + readN):
                for dashes in range(0, 150):
                    print("-", end="")
                print()
                print(transactionsInJournalOrder[i])
                for dashes in range(0, 150):
                    print("-", end="")
                print()

        elif order == 1:
            transactionNum = int(input(f"Which transaction would you like to start at ({firstTransactionNum} to {latestTransactionNum})? "))
            readN = int(input("How many transactions would you like to see? "))

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

        
        isContinue = int(input("0 to continue, 1 to quit: "))

        if isContinue == 1:
            loop = False

if __name__  == "__main__":
    analyzeJournal()