import tkinter as tk
from tkinter import END, filedialog
from math import floor, ceil

from src.FAT import recovery
from src.FAT import structures

class App:

    def __init__(self, master: tk.Tk):

        self.numRecovered: int = 0

        allDisks: list[structures.disks.Disk] = structures.disks.getDisks()
        self.currentDisk: structures.disks.Disk = structures.disks.Disk

        self.outputDirectory: str = ""

        self.deletedEntrySets: list[tuple] = []
        self.deletedFiles: list[str] = []

        self.topFrame: tk.Frame = tk.Frame(master=master, height=50)
        self.topFrame.columnconfigure([0, 1, 2], weight=1)
        self.topFrame.rowconfigure([0, 1, 2, 3], weight=1)
        self.topFrame.pack(fill=tk.BOTH, side=tk.TOP, expand=True)

        # Disk selector
        diskVar: tk.StringVar = tk.StringVar(master, "select disk")
        diskOptions: tk.OptionMenu = tk.OptionMenu(self.topFrame, diskVar, *allDisks, command=self.getDeletedFiles)
        diskOptions.grid(column=0, row=0, columnspan=2, sticky="w")

        labelSelect: tk.Label = tk.Label(master=self.topFrame, anchor=tk.CENTER, text="Select Files to Recover:")
        labelSelect.grid(column=1, row=0, sticky="nsew")

        # 3 listBox with list of strings to show the deleted files
        self.selectDeletedFiles0: tk.Listbox = tk.Listbox(master=self.topFrame, exportselection=False, selectmode=tk.MULTIPLE, height=30)
        self.selectDeletedFiles1: tk.Listbox = tk.Listbox(master=self.topFrame, exportselection=False, selectmode=tk.MULTIPLE, height=30)
        self.selectDeletedFiles2: tk.Listbox = tk.Listbox(master=self.topFrame, exportselection=False, selectmode=tk.MULTIPLE, height=30)
        self.selectDeletedFiles0.grid(column=0, row=1, sticky="nesw")
        self.selectDeletedFiles1.grid(column=1, row=1, sticky="nesw")
        self.selectDeletedFiles2.grid(column=2, row=1, sticky="nesw")

        selectAllButton: tk.Button = tk.Button(master=self.topFrame, text="Select/Deselect All", command=self.selectAll)
        selectAllButton.grid(column=2, row=0, sticky="e")

        # When pressed, user can select output directory.
        getOutputDirectoryButton: tk.Button = tk.Button(master=self.topFrame, text="Select output directory", command=self.getOutputDirectory)
        getOutputDirectoryButton.grid(column=0, row=2, sticky="w")

        # Displays current output directory.
        self.outputDirectoryLabel: tk.Label = tk.Label(master=self.topFrame, text="Output dir: ")
        self.outputDirectoryLabel.grid(column=1, row=2, sticky = "w")

        recoveryButton: tk.Button = tk.Button(master=self.topFrame, text="Recover", command=self.recover)
        recoveryButton.grid(column=2, row=2, sticky="e")

        # Displays the number of recovered files.
        self.recoveredLabel: tk.Label = tk.Label(master=self.topFrame, text=f"Recovered {self.numRecovered} files")
        self.recoveredLabel.grid(column=1, row=3, sticky="w")


    def getDeletedFiles(self, disk: structures.disks.Disk):

        if self.currentDisk != disk:
            self.topFrame.config(cursor="exchange")
            self.topFrame.update_idletasks()

            self.currentDisk: structures.disks.Disk = disk

            fileRecovery: recovery.recovery.Recovery = recovery.recovery.Recovery()

            bootSector = structures.boot_sector.BootSector(self.currentDisk)
            self.deletedEntrySets = fileRecovery.getDeletedFiles(self.currentDisk, bootSector)
            self.deletedFiles = []
            for set in self.deletedEntrySets:
                self.deletedFiles.append(set.name)


            self.updateBoxes()
            self.topFrame.config(cursor="")
            self.topFrame.update_idletasks()

        else:
            return

    def selectAll(self):
        if (len(self.selectDeletedFiles0.curselection()) > 0 or len(self.selectDeletedFiles1.curselection()) > 0
        or len(self.selectDeletedFiles2.curselection()) > 0):
            self.selectDeletedFiles0.selection_clear(0, END)
            self.selectDeletedFiles1.selection_clear(0, END)
            self.selectDeletedFiles2.selection_clear(0, END)
        else:
            self.selectDeletedFiles0.select_set(0, END)
            self.selectDeletedFiles1.select_set(0, END)
            self.selectDeletedFiles2.select_set(0, END)

    def getOutputDirectory(self):
        self.outputDirectory = tk.filedialog.askdirectory(title="Select Output Directory", initialdir="/home")
        self.outputDirectoryLabel.config(text=f"Output dir: {self.outputDirectory}")


    def recover(self):

        fileRecovery = recovery.recovery.Recovery()

        toRecover = []

        for index in self.selectDeletedFiles0.curselection():
            toRecover.append(self.deletedEntrySets[index])
        for index in self.selectDeletedFiles1.curselection():
            toRecover.append(self.deletedEntrySets[(index) + floor(len(self.deletedFiles) / 3)])
        for index in self.selectDeletedFiles2.curselection():
            toRecover.append(self.deletedEntrySets[(index) + ((len(self.deletedFiles) - ceil(len(self.deletedFiles) / 3)))])

        self.numRecovered += fileRecovery.recoverFiles(self.currentDisk, toRecover, self.outputDirectory)


        self.selectDeletedFiles0.selection_clear(0, END)
        self.selectDeletedFiles1.selection_clear(0, END)
        self.selectDeletedFiles2.selection_clear(0, END)

        self.recoveredLabel.config(text=f"Recovered {self.numRecovered} files")

    def updateBoxes(self):

        self.selectDeletedFiles0.delete(0, self.selectDeletedFiles0.size())
        self.selectDeletedFiles1.delete(0, self.selectDeletedFiles1.size())
        self.selectDeletedFiles2.delete(0, self.selectDeletedFiles2.size())

        deletedFiles0: list[str] = self.deletedFiles[0:floor(len(self.deletedFiles) / 3)]
        deletedFiles1: list[str] = self.deletedFiles[floor(len(self.deletedFiles) / 3):floor(len(self.deletedFiles) - (len(self.deletedFiles) / 3))]
        deletedFiles2: list[str] = self.deletedFiles[floor(len(self.deletedFiles) - (len(self.deletedFiles) / 3)): len(self.deletedFiles)]

        self.selectDeletedFiles0.insert(0, *deletedFiles0)
        self.selectDeletedFiles1.insert(0, *deletedFiles1)
        self.selectDeletedFiles2.insert(0, *deletedFiles2)





def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
