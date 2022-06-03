

from ReadJournal import *
from ExtentNode import *
from FileRecovery import *
import Disks
import tkinter as tk
from unittest.util import _MIN_DIFF_LEN

fileRecovery = FileRecovery()

currentDisk = ""
deletedInodes = []
deletedFiles = []
files0 = deletedFiles[0:floor(len(deletedFiles) / 3)]
files1 = deletedFiles[floor(len(deletedFiles) / 3):floor(len(deletedFiles) - (len(deletedFiles) / 3))]
files2 = deletedFiles[floor(len(deletedFiles) - (len(deletedFiles) / 3)): len(deletedFiles)]

def getDeletedFiles(disk):
    global currentDisk
    
    if currentDisk != disk:
        currentDisk = disk
        readJournal = ReadJournal(disk)
        transactions = readJournal.readFileSystemJournal()
        global deletedInodes
        deletedInodes = []
        global deletedFiles
        deletedFiles = []
        global files0
        global files1
        global files2
        deletedInodes = fileRecovery.getDeletedInodes(disk, transactions)
        for inode in deletedInodes:
            print(inode)
            deletedFiles.append(str(inode))
            files0 = deletedFiles[0:floor(len(deletedFiles) / 3)]
            files1 = deletedFiles[floor(len(deletedFiles) / 3):floor(len(deletedFiles) - (len(deletedFiles) / 3))]
            files2 = deletedFiles[floor(len(deletedFiles) - (len(deletedFiles) / 3)): len(deletedFiles)]
    else:
        return




allDisks = Disks.getDisks()
diskPaths = []
for disk in allDisks:
    diskPaths.append(disk.diskPath)


window = tk.Tk()


topFrame = tk.Frame(master=window, height=50)
midFrame = tk.Frame(master=window)
lowMidFrame = tk.Frame(master=window)


topFrame.pack(fill=tk.X, side=tk.TOP)
midFrame.pack(fill=tk.BOTH, side=tk.TOP)
lowMidFrame.pack(fill=tk.X, side=tk.TOP)

topFrame.columnconfigure([0,1,2,3,4,5,6,7], weight=1)
midFrame.columnconfigure([0,1,2], weight=1)

diskVar = tk.StringVar()
diskVar.set("select disk")
diskOptions = tk.OptionMenu(topFrame, diskVar, *diskPaths, command=getDeletedFiles)


diskOptions.grid(column=0, row=1, columnspan=2, sticky="w")


labelSelect = tk.Label(master=topFrame, anchor=tk.CENTER, text="Select Files to Recover:")


labelSelect.grid(column=2, row=1, columnspan=4, sticky="nsew")


helpButton = tk.Button(master=topFrame, text="help")


helpButton.grid(column=7, row=1, sticky="e")



files0Var = tk.StringVar(value=files0)

files1Var = tk.StringVar(value=files1)

files2Var = tk.StringVar(value=files2)


selectFiles0 = tk.Listbox(master=midFrame, selectmode=tk.MULTIPLE, height=25, listvariable=files0Var)
selectFiles1 = tk.Listbox(master=midFrame, selectmode=tk.MULTIPLE, height=25, listvariable=files1Var)
selectFiles3 = tk.Listbox(master=midFrame, selectmode=tk.MULTIPLE, height=25, listvariable=files2Var)


selectFiles0.grid(column=0, row=1, sticky="nesw")
selectFiles1.grid(column=1, row=1, sticky="nesw")
selectFiles3.grid(column=2, row=1, sticky="nesw")

getOutputDirectoryButton = tk.Button(master=lowMidFrame, text="Select output directory")
getOutputDirectoryButton.pack(side=tk.LEFT)

recoveryButton = tk.Button(master=lowMidFrame, text="Recover")
recoveryButton.pack(side=tk.RIGHT)

window.mainloop()



