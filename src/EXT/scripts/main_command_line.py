
import journal.read_journal
import recovery.recovery_journaled
import structures.disks

def main():
    fileRecovery = recovery.recovery_journaled.FileRecoveryJournaled()

    print("select from availible disk file paths: ", end="")

    diskList = structures.disks.getDisks()

    for disk in diskList:
        print(disk.diskPath, end=" ")
    print("\n")

    while True:
            diskName = input("File path of disk: ")

            for disk in diskList:
                if disk.diskPath == diskName:
                    currentDisk = disk

            try:
                readJournal = journal.read_journal.ReadJournal(currentDisk)
                break
            except UnboundLocalError:
                print("Invalid disk path, try again.")


    transactions = readJournal.readFileSystemJournal()
    transactions.sort(key=lambda transaction: -transaction.transactionNum)
    deletedInodes = fileRecovery.getDeletedInodes(currentDisk, transactions)

    numDeleted = len(deletedInodes)

    while True:
        try:
            userChoice = input("%d deleted files found. Enter Y to recover all, and an integer N (1 to %d) to recover the N most recently deleted files: " % (numDeleted, numDeleted))

            numToRecover = 0
            if userChoice.upper() == "Y":
                numToRecover = numDeleted

            elif int(userChoice) <= numDeleted and int(userChoice) > 0:
                numToRecover = int(userChoice)
            break
        except ValueError:
            print("Ivalid input, please enter Y or an integer value")


    while True:
        try:
            filePath = input("Output path for recovered files: ")

            numRecovered = fileRecovery.recoverFiles(currentDisk, transactions, deletedInodes, numToRecover, filePath)

            print("%d files were successfully recovered" % numRecovered)
            break
        except FileNotFoundError:
            print("Invalid output path, please try again.")

if __name__ == "__main__":
    main()