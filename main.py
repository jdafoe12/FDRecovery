
from ReadJournal import *
from ExtentNode import *
from FileRecovery import *
import Disks


fileRecovery = FileRecovery()

print("select from availible disk file paths: ", end="")

disks = Disks.getDisks()

for disk in disks:
    print(disk.diskPath, end=" ")
print("\n")

diskName = input("File path of disk: ")
readJournal = ReadJournal(diskName)


transactions = readJournal.readFileSystemJournal()
transactions.sort(key=lambda transaction: -transaction.transactionNum)
deletedInodes = fileRecovery.getDeletedInodes(diskName, transactions)

numDeleted = len(deletedInodes)


userChoice = input("%d deleted files found. Enter Y to recover all, and an integer N (1 to %d) to recover the N most recently deleted files: " % (numDeleted, numDeleted))

numToRecover = 0
if userChoice.upper() == "Y":
    numToRecover = numDeleted

elif int(userChoice) <= numDeleted and int(userChoice) > 0:
    numToRecover = int(userChoice)

filePath = input("please provide a file path for recovered files: ")

numRecovered = fileRecovery.recoverFiles(diskName, transactions, deletedInodes, numToRecover, filePath)

print("%d files were successfully recovered" % numRecovered)