

from ReadJournal import *
from ExtentNode import *
from FileRecovery import *
import Disks
import time
import tkinter as tk



class App():
    def __init__(self, master):

        # setup frame
        topFrame = tk.Frame(master=master, height=50)
        topFrame.columnconfigure([0, 1, 2], weight=1)
        topFrame.rowconfigure([0, 1, 2], weight=1)
        topFrame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)


        # get a list of disks
        allDisks = Disks.getDisks()
        diskPaths = []
        for disk in allDisks:
            diskPaths.append(disk.diskPath)

        self.currentDisk = ""

        # disk selector
        diskVar = tk.StringVar(master, "select disk")
        diskOptions = tk.OptionMenu(topFrame, diskVar, *diskPaths, command=self.getDeletedFiles)
        diskOptions.grid(column=0, row=0, columnspan=2, sticky="w")

        # label, prompting user to choose files to recover
        labelSelect = tk.Label(master=topFrame, anchor=tk.CENTER, text="Select Files to Recover:")
        labelSelect.grid(column=1, row=0, sticky="nsew")

        # help button opens a help window
        helpButton = tk.Button(master=topFrame, text="help")
        helpButton.grid(column=2, row=0, sticky="e")


        # setup 3 listBox with list of strings to indicate each file to show the deleted files - so the user can select which ones to recover
        self.deletedInodes = []
        self.deletedFiles = []

        self.selectDeletedFiles0 = tk.Listbox(master=topFrame, selectmode=tk.MULTIPLE, height=30)
        self.selectDeletedFiles1 = tk.Listbox(master=topFrame, selectmode=tk.MULTIPLE, height=30)
        self.selectDeletedFiles2 = tk.Listbox(master=topFrame, selectmode=tk.MULTIPLE, height=30)
        self.selectDeletedFiles0.grid(column=0, row=1, sticky="nesw")
        self.selectDeletedFiles1.grid(column=1, row=1, sticky="nesw")
        self.selectDeletedFiles2.grid(column=2, row=1, sticky="nesw")


        getOutputDirectoryButton = tk.Button(master=topFrame, text="Select output directory")
        getOutputDirectoryButton.grid(column=0, row=2, sticky="w")

        recoveryButton = tk.Button(master=topFrame, text="Recover")
        recoveryButton.grid(column=2, row=2, sticky="e")


    def getDeletedFiles(self, disk):

        if self.currentDisk != disk:
            self.currentDisk = disk

            fileRecovery = FileRecovery()
            readJournal = ReadJournal(disk)
            transactions = readJournal.readFileSystemJournal()
            self.deletedInodes = fileRecovery.getDeletedInodes(disk, transactions)
            self.deletedFiles = []
            for inode in self.deletedInodes:
                self.deletedFiles.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(inode[2])))
            self.updateBoxes()
        else:
            return

    def updateBoxes(self):
        self.selectDeletedFiles0.delete(0, self.selectDeletedFiles0.size())
        self.selectDeletedFiles1.delete(0, self.selectDeletedFiles1.size())
        self.selectDeletedFiles2.delete(0, self.selectDeletedFiles2.size())

        deletedFiles0 = self.deletedFiles[0:floor(len(self.deletedFiles) / 3)]
        deletedFiles1 = self.deletedFiles[floor(len(self.deletedFiles) / 3):floor(len(self.deletedFiles) - (len(self.deletedFiles) / 3))]
        deletedFiles2 = self.deletedFiles[floor(len(self.deletedFiles) - (len(self.deletedFiles) / 3)): len(self.deletedFiles)]

        self.selectDeletedFiles0.insert(0, *deletedFiles0)
        self.selectDeletedFiles1.insert(0, *deletedFiles1)
        self.selectDeletedFiles2.insert(0, *deletedFiles2)




def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()

if __name__ == '__main__':
    main()
