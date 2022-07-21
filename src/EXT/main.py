

from math import floor, ceil
from tkinter import END, filedialog
import tkinter as tk
import time

from src.EXT import journal
from src.EXT import recovery
from src.EXT import structures


class App:

    """
    Initializes all GUI aspects
    and contains handlers for GUI events

    Attributes
    ----------
    numRecovered : int
        A running total of all successfully recovered files.
    transactions : list[journal.Transaction]
        A list of all transactions in the journal.
        This is only used if the selected disk is a journaling filesystem.
    currentDisk : disks.Disk
        Contains the disk object corresponding to the disk currently in use.
    outputDirectory : str
        Contains the path for the selected output directory.
    deletedInodes: list[tuple]
        A list of tuples, corresponding to inodes which refer to
        deleted files within the currently selected disk.

        if the currently selected disk is a journaling filesystem (ext3, ext4) then this tuple is
        of the form (block num of inode table, offset within inode table, deletion time).

        if it is not a journaling filesystem (ext2) then
        this tuple is of the form (inode num, inode deletion time).
    deletedFiles : list[str]
        A list of the identifiers associated with each deleted inode.
        The identifier strings contain the date and time of deletion.
        The indices of this list correspond to the indices of deletedInodes.

    topFrame : tk.Frame
        The frame in which all GUI widgets reside.
    selectDeletedFiles0 : tk.ListBox
        A ListBox containing the first 1/3 of deletedFiles.
        The user can select files from this list to recover.
    selectDeletedFiles1 : tk.ListBox
        A ListBox containing the second 1/3 of deletedFiles.
        The user can select files from this list to recover.
    selectDeletedFiles2 : tk.ListBox
        A ListBox containing the final 1/3 of deletedFiles.
        The user can select files from this list to recover.
    outputDirectoryLabel : tk.Label
        A label which displays the current selected output directory path.
    recoveredLabel : tk.Label
        A label which displays numRecovered.

    Methods
    -------
    getDeletedFiles(disk)
        When the selected disk changes, this function is called.
        Updates currentDisk, deletedInodes, deletedFiles, and the ListBoxes.
    updateBoxes()
        getDeletedFiles calls this function.
        Changes the ListBoxes to contain the updated deletedFiles.
    getOutputDirectory()
        Prompts the user to select an output directory for recovered files.
        Updates outputDirectory
    recover()
        Called when recoveryButton is pushed.
        Recovers the selected files to outputDirectory.
        updates numRecovered and numRecoveredLabel
    selectAll()
        Called when selectAll button is pushed.
        When there are no files selected, this function selects all files.
        When there are files selected, this function deselects all files.
    """


    def __init__(self, master: tk.Tk):

        """
        Parameters
        ----------
        master : tk.Tk
            The master window for the GUI
        """

        # initialize attributes
        self.numRecovered: int = 0
        self.transactions: list[journal.journal.Transaction] = None

        allDisks: list[structures.disks.Disk] = structures.disks.getDisks()
        self.currentDisk: structures.disks.Disk = structures.disks.Disk

        self.outputDirectory: str = ""

        self.deletedInodes: list[tuple] = []
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

        """
        When the selected disk changes, this function is called.
        Updates currentDisk, deletedInodes, deletedFiles, and the ListBoxes.

        Parameters
        ----------
        disk : disks.Disk
            The disk that has just been selected

        returns
        -------
        Explicit:
        None

        Implicit:
        transactions : list[journal.Transaction]
            Reads all transactions from the journal and updates this value.
        deletedInodes : list[tuple]
            Gets all deleted inodes from journal and updates this value.
        deletedFiles : list[str]
            Updates this value to correspond with deletedInodes.
        Calls updateBoxes() which has its own implicit outputs.
        """

        if self.currentDisk != disk:
            self.topFrame.config(cursor="exchange")
            self.topFrame.update_idletasks()

            self.currentDisk = disk

            # ext3 and ext3 have journals, which are used for recovery
            if disk.diskType == "ext3" or disk.diskType == "ext4":
                fileRecovery: recovery.recovery_journaled.FileRecoveryJournaled = recovery.recovery_journaled.FileRecoveryJournaled()
                readJournal: journal.read_journal.ReadJournal = journal.read_journal.ReadJournal(self.currentDisk)

                self.transactions = readJournal.readFileSystemJournal()
                self.transactions.sort(key=lambda transaction: -transaction.transactionNum)

                self.deletedInodes = fileRecovery.getDeletedInodes(self.currentDisk, self.transactions)
                self.deletedFiles = []
                for inode in self.deletedInodes:
                    self.deletedFiles.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(inode[2])) + f"_inode{inode[0]}_{inode[1]}")

            # ext2 does not have a journal
            elif disk.diskType == "ext2":
                fileRecovery: recovery.recovery_no_journal.FileRecoveryNoJournal = recovery.recovery_no_journal.FileRecoveryNoJournal()

                self.deletedInodes = fileRecovery.getDeletedInodes(self.currentDisk)
                self.deletedFiles = []
                for inode in self.deletedInodes:
                    self.deletedFiles.append(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(inode[1])) + f"_inode{inode[0]}")

            self.updateBoxes()
            self.topFrame.config(cursor="")
            self.topFrame.update_idletasks()

        else:
            return


    def updateBoxes(self):

        """
        A getDeletedFiles calls this function.
        Changes the ListBoxes to contain the updated deletedFiles

        Returns
        -------
        Explicit:
        None

        Implicit:
        selectDeletedFiles0 : tk.ListBox
            Removes previous contents and replaces it with updated deletedFiles
        selectDeletedFiles1 : tk.ListBox
            Removes previous contents and replaces it with updated deletedFiles
        selectDeletedFiles2 : tk.ListBox
            Removes previous contents and replaces it with updated deletedFiles
        """
        self.selectDeletedFiles0.delete(0, self.selectDeletedFiles0.size())
        self.selectDeletedFiles1.delete(0, self.selectDeletedFiles1.size())
        self.selectDeletedFiles2.delete(0, self.selectDeletedFiles2.size())

        deletedFiles0: list[str] = self.deletedFiles[0:floor(len(self.deletedFiles) / 3)]
        deletedFiles1: list[str] = self.deletedFiles[floor(len(self.deletedFiles) / 3):floor(len(self.deletedFiles) - (len(self.deletedFiles) / 3))]
        deletedFiles2: list[str] = self.deletedFiles[floor(len(self.deletedFiles) - (len(self.deletedFiles) / 3)): len(self.deletedFiles)]

        self.selectDeletedFiles0.insert(0, *deletedFiles0)
        self.selectDeletedFiles1.insert(0, *deletedFiles1)
        self.selectDeletedFiles2.insert(0, *deletedFiles2)


    def getOutputDirectory(self):

        """
        Prompts the user to select an output directory for recovered files.
        Updates outputDirectory

        Returns
        -------
        Explicit:
        None

        Implicit:
        outputDirectory : str
            Gets the output directory from the user and updates it
        """

        self.outputDirectory = tk.filedialog.askdirectory(title="Select Output Directory", initialdir="/home")
        self.outputDirectoryLabel.config(text=f"Output dir: {self.outputDirectory}")

    def selectAll(self):

        """
        Called when selectAll button is pushed.
        When there are no files selected, this function selects all files.
        When there are files selected, this function deselects all files.

        Returns
        -------
        Explicit:
        None

        Implicit:
        selectDeletedFiles0 : tk.ListBox
            Either selects all items, or deselects all items.
        selectDeletedFiles1 : tk.ListBox
            Either selects all items, or deselects all items.
        selectDeletedFiles2 : tk.ListBox
            Either selects all items, or deselects all items.
        """
        if (len(self.selectDeletedFiles0.curselection()) > 0 or len(self.selectDeletedFiles1.curselection()) > 0
        or len(self.selectDeletedFiles2.curselection()) > 0):
            self.selectDeletedFiles0.selection_clear(0, END)
            self.selectDeletedFiles1.selection_clear(0, END)
            self.selectDeletedFiles2.selection_clear(0, END)
        else:
            self.selectDeletedFiles0.select_set(0, END)
            self.selectDeletedFiles1.select_set(0, END)
            self.selectDeletedFiles2.select_set(0, END)


    def recover(self):

        """
        Called when recoveryButton is pushed.
        Recovers the selected files to outputDirectory.
        updates numRecovered and numRecoveredLabel

        Returns
        -------
        Explicit:
            None

        Implicit:
        numRecovered : int
            Adds the number of recovered files to this attribute
        numRecoveredLabel : tk.Label
            Updates to reflect the change to numRecovered
        """

        if self.currentDisk.diskType == "ext3" or self.currentDisk.diskType == "ext4":
            fileRecovery = recovery.recovery_journaled.FileRecoveryJournaled()
        elif self.currentDisk.diskType == "ext2":
            fileRecovery = recovery.recovery_no_journal.FileRecoveryNoJournal()

        toRecover = []

        for index in self.selectDeletedFiles0.curselection():
            toRecover.append(self.deletedInodes[index])
        for index in self.selectDeletedFiles1.curselection():
            toRecover.append(self.deletedInodes[(index) + floor(len(self.deletedFiles) / 3)])
        for index in self.selectDeletedFiles2.curselection():
            toRecover.append(self.deletedInodes[(index) + ((len(self.deletedFiles) - ceil(len(self.deletedFiles) / 3)))])

        if self.currentDisk.diskType == "ext3" or self.currentDisk.diskType == "ext4":
            self.numRecovered += fileRecovery.recoverFiles(self.currentDisk, self.transactions, toRecover, len(toRecover), self.outputDirectory)
        elif self.currentDisk.diskType == "ext2":
            self.numRecovered += fileRecovery.recoverFiles(self.currentDisk, toRecover, len(toRecover), self.outputDirectory)

        self.selectDeletedFiles0.selection_clear(0, END)
        self.selectDeletedFiles1.selection_clear(0, END)
        self.selectDeletedFiles2.selection_clear(0, END)

        self.recoveredLabel.config(text=f"Recovered {self.numRecovered} files")


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()

