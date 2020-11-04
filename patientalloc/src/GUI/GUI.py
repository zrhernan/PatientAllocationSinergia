# -*- coding: utf-8 -*-
"""
Created on Sat Jun 23 14:44:52 2018

@author: cnbi
"""
from appJar import gui
from patientalloc.src.GUI.DatabaseLoaderDisplay import DatabaseLoaderDisplay
from patientalloc.src.GUI.DatabaseCreatorDisplay import DatabaseCreatorDisplay
from patientalloc.src.GUI.WelcomeDisplay import WelcomeDisplay
from patientalloc.src.GUI.SettingsDisplay import SettingsDisplay
from patientalloc.src.GUI.GUISettings import GUISettings
from patientalloc.src.Database.DatabaseHandlerFactory import DatabaseHandlerFactory
from patientalloc.src.GUI.GuiDatabaseHandler import GuiDatabaseHandler

import os


class GUI():
    def __init__(self, mode):
        self.mode = mode
        self.settings = GUISettings()
        if not os.path.exists(self.settings.settingsFile):
            self.settings.createSettingsFile()
        else:
            self.settings.load()
        databaseHandler = DatabaseHandlerFactory().create(self.settings)
        self.app = gui("Patient allocation")
        self.app.addStatusbar(fields=1, side="LEFT")
        self.app.setStatusbarWidth(120, 0)
        self.app.setStretch("COLUMN")
        self.settingsDisplay = SettingsDisplay(self.app, self.settings)
        self.databaseHandler = GuiDatabaseHandler(self.app, databaseHandler)
        if self.isAdminMode():
            self.fileMenus = ["Load", "Save", "Save as",
                              "Create", "-", "Settings", "-", "Close"]
        elif self.isUserMode():
            self.fileMenus = ["Load", "Save", "-", "Close"]
        self.app.addMenuList("File", self.fileMenus, self.__menuPress__)

        if self.isAdminMode():
            self.currentFrame = WelcomeDisplay(self.app, self)
            self.currentFrame.display()
        elif self.isUserMode():
            self.currentFrame = DatabaseLoaderDisplay(self)
            self.currentFrame.display()

        viewmode = self.getViewMode()
        if viewmode is True:
            self.viewmode = 'blind'
        else:
            self.viewmode = 'not blind'

    def isAdminMode(self):
        return self.mode == 'admin'

    def isUserMode(self):
        return self.mode == 'user'

    def start(self):
        self.app.go()

    def switchFrame(self, newFrame):
        self.currentFrame.removeFrame()
        del self.currentFrame
        self.currentFrame = newFrame
        self.currentFrame.display()

    def enableSaveMenu(self):
        if self.mode == 'admin':
            self.app.enableMenuItem("File", "Save as")
        self.app.enableMenuItem("File", "Save")

    def disableSaveMenu(self):
        if self.mode == 'admin':
            self.app.disableMenuItem("File", "Save as")
        self.app.disableMenuItem("File", "Save")

    def __menuPress__(self, menu):
        if menu == "Close":
            self.currentFrame.removeFrame()
            self.app.stop()
        elif menu == "Load":
            self.switchFrame(DatabaseLoaderDisplay(self))
        elif menu == "Create":
            self.switchFrame(DatabaseCreatorDisplay(self))
        elif menu == "Save":
            self.currentFrame.handleCommand("Save")
        elif menu == "Save as":
            self.currentFrame.handleCommand("Save as")
        elif menu == "Settings":
            self.settingsDisplay.display()
            self.databaseHandler = DatabaseHandlerFactory().create(self.settings)

    def getDatabaseFolder(self):
        if self.settings.folder == "" or self.settings.fileName == "":
            self.__setPathToDatabase__()
        else:
            return self.settings.folder

    def getDatabaseFilename(self):
        if self.settings.folder == "" or self.settings.fileName == "":
            self.__setPathToDatabase__()
        else:
            return self.settings.fileName

    def __setPathToDatabase__(self):
        fullpath = self.getFullpathToSaveFromUser()
        explodedPath = fullpath.split("/")
        self.settings.fileName = explodedPath[len(explodedPath) - 1]
        explodedPath[len(explodedPath) - 1] = ""
        self.settings.folder = "/".join(explodedPath)

    def getFullpathToSaveFromUser(self):
        return self.app.saveBox(title="Save database", fileName=None,
                                dirName=None, fileExt=".db",
                                fileTypes=[('Database', '*.db')],
                                asFile=None, parent=None)
    def getViewMode(self):
        title = "ALLOCATION VIEWING MODE"
        message = "Would you like to allocate patients in a blind viewing mode?"
        response = self.app.questionBox(title, message)
        return response

    def display_frane_algorithm_results(self, probs_by_group, probs_by_field, properties):
        group_names = list(probs_by_group.keys())
        probs_groups = ["%.3f" % probs_by_group[grp] for grp in group_names]

        field_names = list(probs_by_field[group_names[0]].keys())
        probs_fields_grp1 = ["%.3f" % probs_by_field[group_names[0]][fld] for fld in field_names]
        probs_fields_grp2 = ["%.3f" % probs_by_field[group_names[1]][fld] for fld in field_names]
        probs_fields_message = [field_names[i].upper() + "\t|" + probs_fields_grp1[i] + "\t" + probs_fields_grp2[i] + "\n" for i in range(0,len(field_names))]
        probs_field_message_concat = ''.join(probs_fields_message)

        title = "FRANE ALGORITHM RESULTS"
        message = "Group Probability Summary\n" \
                  "===================\n" \
                  "If added to...\n" \
                  + group_names[0].upper() + "\t" + group_names[1].upper() + "\n" \
                  + probs_groups[0] + "\t" + probs_groups[1] + "\n"\
                  "\n" \
                  "Field Probability Summary\n" \
                  "===================\n" \
                  "\t|If added to...\n" \
                  "FIELD\t|" + group_names[0].upper() + "\t" + group_names[1].upper() + "\n" \
                  "----------------------------------\n" \
                  + probs_field_message_concat + "\n" \
                  "New Entry in '" + properties['Group'].upper() + "' Group"
        self.app.infoBox(title, message)

    def confirm_new_entry_group_manually(self, groups, properties):
        curr_group = properties['Group']
        opposite_group = [i for i in groups if curr_group not in i]
        opposite_group = opposite_group[0]
        message = "New entry is in '" + curr_group.upper() \
                + "' group. Do you want to change this?\n" \
                "-----------------------------------------\n" \
                "WARNING: Selecting 'Yes' will automatically place the new subject entry into " \
                "'" + opposite_group.upper() + "' group. If you don't want to make any changes, " \
                "please select 'No' or close this window."
        title = "NEW ENTRY GROUP CONFIRMATION"
        response = self.app.questionBox(title, message)
        if response:
            new_group = [i for i in groups if curr_group not in i]
            curr_group = new_group[0]
            print("New Entry manually placed into '" + curr_group.upper() + "' group.")
            self.app.infoBox("NEW GROUP PLACEMENT",
                             "New Entry manually placed into '" + curr_group.upper() + "' group")
        else:
            print("New Entry remains in '" + curr_group.upper() + "' group")
            self.app.infoBox("NEW GROUP PLACEMENT", "New Entry remains in '" + curr_group.upper() + "' group")
        properties['Group'] = curr_group
        return properties
