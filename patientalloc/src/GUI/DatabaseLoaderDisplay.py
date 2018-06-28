# -*- coding: utf-8 -*-

from appJar import appjar
from pathlib import Path
from patientalloc.src.Database.Database import Database
import patientalloc.src.Database.DatabaseError as DatabaseError
from patientalloc.src.GUI.WelcomeDisplay import WelcomeDisplay
import yaml
import os


class DatabaseLoaderDisplay():
    def __init__(self, currentGui):
        self.gui = currentGui
        self.app = currentGui.app
        self.file = None
        self.database = None
        self.loaded = False

    def display(self):
        if self.database is None:
            self.__tryLoadingDatabase__()
        if self.loaded:
            self.__displayDatabase__()

    def handleCommand(self, command):
        if command == "Save":
            self.__save__()
        elif command == "Save as":
            self.file = self.gui.getFullpathToSaveFromUser()
            self.database.createWithFullPath(self.file)

    def __save__(self):
        if self.__getSavingModeFromSettings__() == "local":
            if self.gui.mode == 'admin':
                if self.database.fileName == "":
                    self.file = self.gui.getFullpathToSaveFromUser()
                    self.database.createWithFullPath(self.file)
                else:
                    self.database.create()
            elif self.gui.mode == 'user':
                self.database.create()
        elif self.__getSavingModeFromSettings__() == "online":
            fileInfo = self.__getFileLocationFromSettings__()
            self.database.folder = fileInfo['folder']
            self.database.fileName = fileInfo['fileName']
            address = self.__getServerAddressFromSettings__()
            os.system("git clone -v " + address + ' ' + self.database.folder)
            self.database.create()
            os.system("cd " + self.database.folder + " ; git add . ; git commit -m 'saving database' ; git push")
            os.system("rm -rf " + self.database.folder)


    def __tryLoadingDatabase__(self):
        try:
            if self.__getSavingModeFromSettings__() == "local":
                path = str(Path.home()) + "/dev/PatientAllocationSinergia/tests/database"
                self.file = self.app.openBox(title="Load database file",
                                                 dirName=path,
                                                 fileTypes=[('Database', '*.db')],
                                                 asFile=True,
                                                 parent=None)
                if self.file is not None:
                    self.file = self.file.name
            elif self.__getSavingModeFromSettings__() == "online":
                fileInfo = self.__getFileLocationFromSettings__()
                self.file = os.path.join(fileInfo['folder'], fileInfo['fileName'])
                address = self.__getServerAddressFromSettings__()
                os.system("git clone " + address + " " + fileInfo['folder'])
            if self.file is None:
                self.app.setStatusbar("Operation Canceled", field=0)
                self.gui.switchFrame(WelcomeDisplay(self.app))
            else:
                self.__loadDatabase__()
                os.system("rm -rf " + self.database.folder)
        except DatabaseError.DatabaseError as error:
            self.app.setStatusbar(error.message, field=0)
            print(error.message)

    def __getFileLocationFromSettings__(self):
        fullpath = str(Path.home()) + "/.patientalloc/settings.yml"
        with open(fullpath, 'r') as guiFile:
            guiInfo = yaml.safe_load(guiFile)
            return {'fileName': guiInfo['fileName'], 'folder': guiInfo['folder']}

    def __getServerAddressFromSettings__(self):
        fullpath = str(Path.home()) + "/.patientalloc/settings.yml"
        with open(fullpath, 'r') as guiFile:
            guiInfo = yaml.safe_load(guiFile)
            return guiInfo['server']

    def __getSavingModeFromSettings__(self):
        fullpath = str(Path.home()) + "/.patientalloc/settings.yml"
        with open(fullpath, 'r') as guiFile:
            guiInfo = yaml.safe_load(guiFile)
            return guiInfo['saveMode']

    def __loadDatabase__(self):
        self.database = Database()
        self.database.loadWithFullPath(self.file)
        self.loaded = True
        self.gui.enableSaveMenu()
        self.app.setStatusbar("File " + self.file + " loaded", field=0)

    def __displayDatabase__(self):
        self.app.setFont(size=14)
        fieldIndex = 0
        self.app.setStretch("column")
        self.app.startFrame("DatabaseDisplay", row=0, colspan=5)
        self.app.startFrame("IndicesFrame", row=0, column=fieldIndex)
        self.app.addLabel("Indices", "Indices")
        entryIndex = 1
        for _ in self.database.entries:
            self.app.addLabel("Indices_" + str(entryIndex), str(entryIndex))
            entryIndex += 1
        self.app.addLabel("PValues", "PValues")
        self.app.addLabel("New Entry", "New Entry")
        self.app.stopFrame()
        fieldIndex += 1
        for field in self.database.order:
            self.__createFieldFrame__(field, fieldIndex)
            fieldIndex += 1
        self.app.startFrame("AddSubject", row=1, column=0, colspan=fieldIndex)
        self.app.addButton("Add Patient",self.__addSubject__)
        if self.gui.mode == 'admin':
            self.app.addButton("Check Probabilities",self.__checkProbabilityGroups__)
        self.app.addButton("Save",self.__save__)
        self.app.stopFrame()
        self.app.stopFrame()
        self.databaseDisplayed = True

    def __createFieldFrame__(self, field, fieldIndex):
        if self.gui.mode == 'admin' or field != 'Group':
            self.app.startFrame(field, row=0, column=fieldIndex)
            self.app.addLabel(field, field)
            entryIndex = 0
            for entry in self.database.entries:
                self.app.addLabel(field + "_ " + str(entryIndex), entry[field])
                entryIndex += 1
            try:
                self.app.addLabel("PValue_" + field, str(round(self.database.getPValue(field),2)))
            except DatabaseError.CannotComputeTTestOnField:
                self.app.addLabel("PValue_" + field, "")
            if field != "Group":
                if self.database.getFieldTypeFromField(field) == "List":
                    self.app.addOptionBox("New " + field, self.database.getLimitedValuesFromField(field))
                elif self.database.getFieldTypeFromField(field) == "Number":
                    self.app.addNumericEntry("New " + field)
                else:
                    self.app.addEntry("New " + field)
            else:
                self.app.addLabel("New " + field, "")
            self.app.stopFrame()

    def __addSubject__(self):
        subject = self.__createSubjectFromFormValues__()
        subject["Group"] = self.database.getGroupFromNewEntry(subject)
        self.removeFrame()
        self.database.addEntryWithGroup(subject)
        self.__displayDatabase__()

    def __checkProbabilityGroups__(self):
        self.__tryRemovingCheckProbabilityFrame__()
        subject = self.__createSubjectFromFormValues__()
        probabilities = self.database.getGroupsProbabilitiesFromNewEntry(subject)
        indexKey = 0
        for key in probabilities.keys():
            self.app.startFrame("Probas_" + str(indexKey), row=2 + indexKey, column=0, colspan=5)
            self.app.addLabel("key_" + str(indexKey), key,0,0)
            self.app.addLabel("proba_" + str(indexKey), round(probabilities[key],2),0,1)
            indexKey += 1
            self.app.stopFrame()

    def __createSubjectFromFormValues__(self):
        subject = dict()
        for field in self.database.fields:
            if field != "Group":
                fieldType = self.database.getFieldTypeFromField(field)
                if fieldType == "List":
                    subject[field] = self.app.getOptionBox("New " + field)
                elif fieldType == "Entry" or fieldType == "Number":
                    subject[field] = self.app.getEntry("New " + field)
        return subject

    def removeFrame(self):
        if self.loaded:
            self.__tryRemovingCheckProbabilityFrame__()
            self.app.removeLabel("Indices")
            for entryIndex in range(1,len(self.database.entries)+1):
                self.app.removeLabel("Indices_" + str(entryIndex))
            self.app.removeButton("Save")
            self.app.removeButton("Add Patient")
            if self.gui.mode == 'admin':
                self.app.removeButton("Check Probabilities")
            self.app.removeLabel("PValues")
            self.app.removeLabel("New Entry")
            for field in self.database.fields:
                self.__removeFieldColumn__(field)
            self.app.removeFrame("AddSubject")
            self.app.removeFrame("IndicesFrame")
            self.app.removeFrame("DatabaseDisplay")

    def __removeFieldColumn__(self, field):
        if self.gui.mode == 'admin' or field != 'Group':
            self.app.removeLabel("PValue_" + field)
            if field == "Group":
                self.app.removeLabel("New " + field)
            else:
                if self.database.getFieldTypeFromField(field) == "List":
                    self.app.removeOptionBox("New " + field)
                else:
                    self.app.removeEntry("New " + field)
            self.app.removeLabel(field)
            for entryIndex in range(0,len(self.database.entries)):
                self.app.removeLabel(field + "_ " + str(entryIndex))
            self.app.removeFrame(field)


    def __tryRemovingCheckProbabilityFrame__(self):
        try:
            for indexKey in range(0,len(self.database.groups)):
                self.app.removeLabel("key_" + str(indexKey))
                self.app.removeLabel("proba_" + str(indexKey))
                self.app.removeFrame("Probas_" + str(indexKey))
        except appjar.ItemLookupError:
            pass
