# -*- coding: utf-8 -*-
import patientalloc
import getpass
from appJar import appjar
import patientalloc.src.Database.DatabaseError as DatabaseError
import math
import subprocess
from scipy.io import savemat
import os

class DatabaseLoaderDisplay():
    def __init__(self, currentGui):
        self.gui = currentGui
        self.app = currentGui.app
        self.database = None
        self.loaded = False
        self.data_path = "/home/" + getpass.getuser() + "/data"
        self.labels_to_remove = []
        self.buttons_to_remove = []
        self.checkboxes_to_remove = []
        self.option_box_to_remove = []
        self.entries_to_remove = []
        self.subject_factory = None

    def handleCommand(self, command):
        if command == "Save":
            self.__save_database__()
        elif command == "Save as":
            self.file = self.gui.getFullpathToSaveFromUser()
            self.database.createWithFullPath(self.file)

    def __save_database__(self):
        self.gui.databaseHandler.saveDatabase(
            self.database, self.gui.getDatabaseFolder(), self.gui.getDatabaseFilename())

    def display(self):
        if self.database is None:
            self.__try_loading_database__()
        if self.loaded:
            self.__display_database__()

    def __try_loading_database__(self):
        try:
            self.database = self.gui.databaseHandler.loadDatabase(
                self.gui.getDatabaseFolder(), self.gui.getDatabaseFilename())
            if self.database is not None:
                self.loaded = True
                self.subject_factory = patientalloc.SubjectFactory(
                    self.database, self.gui.settings) #, self.gui)
                self.gui.enableSaveMenu()
        except DatabaseError.DatabaseError as error:
            print("==============================================")
            print(error.message)
            print("==============================================")
            self.app.setStatusbar(error.message, field=0)

    def __display_database__(self):
        self.app.setFont(size=14)
        field_index = 0
        
        self.app.setStretch("column")
        self.app.startFrame("DatabaseDisplay", row=0, colspan=5)
        self.app.startScrollPane("DatabaseScroll", colspan=8)
        self.app.addLabel("Indices", "Indices", row=0, column=field_index)
        self.labels_to_remove.append("Indices")
        
        entry_index = 1
        for _ in self.database.entries:
            self.app.addLabel("Indices_" + str(entry_index),
                              str(entry_index), row=entry_index, column=0)
            self.labels_to_remove.append("Indices_" + str(entry_index))
            entry_index += 1
        self.app.addLabel("PValues", "PValues", row=entry_index, column=0)
        self.labels_to_remove.append("PValues")
        self.app.addLabel("New Entry", "New Entry",
                          row=entry_index + 1, column=0)
        self.labels_to_remove.append("New Entry")
        field_index += 1
        for field in self.database.order:
            self.__create_field_frame__(field, field_index)
            field_index += 1
        
        entry_index = self.__display_rejection__(entry_index, field_index)
        field_index = self.__display_finish__(entry_index, field_index)
        field_index += 2
        entry_index += 2
        self.app.stopScrollPane()
        self.app.addButton("Add Patient", self.__add_subject__,
                           row=entry_index, column=0, colspan=math.floor(field_index / 2))
        self.buttons_to_remove.append("Add Patient")
        if self.gui.mode == 'admin':
            self.app.addButton("Check Probabilities",
                               self.__check_probability_groups__)
            self.buttons_to_remove.append("Check Probabilities")
        self.app.addButton("Save", self.__save_database__, row=entry_index, column=math.floor(
            field_index / 2), colspan=math.floor(field_index / 2))
        self.buttons_to_remove.append("Save")
        self.app.setButtonBg("Save", "green")
        self.app.addButton("Generate Playback files", self.__compute_playback__,
                           row=entry_index+1, column=0, colspan=field_index)
        self.buttons_to_remove.append("Generate Playback files")
        self.app.stopFrame()
        
        self.databaseDisplayed = True

    def __display_finish__(self, entry_index, field_index):
        field_index += 1
        entry_index = 1
        self.app.addLabel("Finish", "Finish", row=0, column=field_index)
        self.labels_to_remove.append("Finish")
        for entry in self.database.entries:
            self.app.addNamedCheckBox(
                "", "Finish_" + str(entry_index), row=entry_index, column=field_index)
            self.checkboxes_to_remove.append("Finish_" + str(entry_index))
            if entry_index in self.database.finished_entries:
                self.app.setCheckBox("Finish_" + str(entry_index), True, False)
            else:
                self.app.setCheckBox(
                    "Finish_" + str(entry_index), False, False)
            self.app.setCheckBoxChangeFunction(
                "Finish_" + str(entry_index), self.__set_entry_as_finished__)
            entry_index += 1
        return field_index

    def __display_rejection__(self, entry_index, field_index):
        self.app.addLabel("Reject", "Reject", row=0, column=field_index)
        self.labels_to_remove.append("Reject")
        entry_index = 1
        for entry in self.database.entries:
            self.app.addNamedCheckBox(
                "", "Reject_" + str(entry_index), row=entry_index, column=field_index)
            self.checkboxes_to_remove.append("Reject_" + str(entry_index))
            if entry_index in self.database.rejected_entries:
                self.app.setCheckBox("Reject_" + str(entry_index), True, False)
            else:
                self.app.setCheckBox(
                    "Reject_" + str(entry_index), False, False)
            self.app.setCheckBoxChangeFunction(
                "Reject_" + str(entry_index), self.__reject_entry__)
            entry_index = entry_index + 1
        return entry_index

    def __reject_entry__(self, entry):
        entry_index = int(entry[7:len(entry)])
        if entry_index in self.database.rejected_entries:
            self.database.unrejectEntry(entry_index)
        else:
            self.database.rejectEntry(entry_index)
        for field in self.database.order:
            if self.gui.mode == 'admin' or field != 'Group':
                try:
                    self.app.setLabel(
                        "PValue_" + field, str(round(self.database.getPValue(field), 2)))
                except DatabaseError.CannotComputeTTestOnField:
                    self.app.setLabel("PValue_" + field, "")

    def __set_entry_as_finished__(self, entry):
        entry_index = int(entry[7:len(entry)])
        if entry_index in self.database.finished_entries:
            self.database.setEntryAsUnFinished(entry_index)
        else:
            self.database.setEntryAsFinished(entry_index)

    def __compute_playback__(self):
        temp_path = "/tmp/sinergia"
        if not os.path.isdir(temp_path):
            os.mkdir(temp_path)
        file_name = temp_path + '/finishedEntries.mat'
        finished_subject_ids = [];
        for index in self.database.finished_entries:
            finished_subject_ids.append(self.database.getEntryId(index-1))
        savemat(file_name, {'finished_entries': finished_subject_ids})
        subprocess.call('gnome-terminal ---tab -e "bash -c \'computeSham\'"', shell=True)

    def __create_field_frame__(self, field, field_index):
        if self.gui.mode == 'admin' or field != 'Group':
            self.app.addLabel(field, field, row=0, column=field_index)
            self.labels_to_remove.append(field)
            entry_index = 0
            for entry in self.database.entries:
                self.app.addLabel(field + "_ " + str(entry_index),
                                  entry[field], row=entry_index + 1, column=field_index)
                self.labels_to_remove.append(field + "_ " + str(entry_index))
                entry_index += 1
            entry_index += 1
            try:
                self.app.addLabel("PValue_" + field, str(
                    round(self.database.getPValue(field), 2)), row=entry_index, column=field_index)
            except DatabaseError.CannotComputeTTestOnField:
                self.app.addLabel("PValue_" + field, "",
                                  row=entry_index, column=field_index)
            self.labels_to_remove.append("PValue_" + field)
            entry_index += 1
            if field != "Group":
                if self.database.getFieldTypeFromField(field) == "List":
                    self.app.addOptionBox("New " + field, self.database.getLimitedValuesFromField(
                        field), row=entry_index, column=field_index)
                    self.option_box_to_remove.append("New " + field)
                elif self.database.getFieldTypeFromField(field) == "Number":
                    self.app.addNumericEntry(
                        "New " + field, row=entry_index, column=field_index)
                    self.entries_to_remove.append("New " + field)
                else:
                    self.app.addEntry(
                        "New " + field, row=entry_index, column=field_index)
                    self.entries_to_remove.append("New " + field)
            else:
                self.app.addLabel("New " + field, "",
                                  row=entry_index, column=field_index)
                self.labels_to_remove.append("New " + field)

    def __add_subject__(self):
        subject_properties = self.__create_subject_properties_from_form_values__()
        subject_properties = self.subject_factory.addGroup(subject_properties)

        if self.gui.viewmode is not 'blind':
            probs_by_group = self.database.get_groups_probabilities_from_new_entry(subject_properties)
            [_, _, probs_by_field] = self.database.__create_pvalues_for_all_groups__(subject_properties)
            self.gui.display_frane_algorithm_results(probs_by_group, probs_by_field, subject_properties)
            subject_properties = self.gui.confirm_new_entry_group_manually(self.database.groups, subject_properties)

        newentry_origgrp = subject_properties['Group']
        subject = self.subject_factory.createSubject(subject_properties)
        subject_properties = subject.extract()

        if newentry_origgrp != subject_properties['Group'] and self.gui.viewmode is not 'blind':
            self.app.infoBox("NEW GROUP PLACEMENT", "New Entry placed in '" + subject_properties['Group'] + "' Group (based on limited matched BCI subjects)")

        subject.create()
        self.removeFrame()
        self.database.addEntryWithGroup(subject_properties)
        print("New Entry ID: " + subject_properties["SubjectID"])
        self.__display_database__()

    def __check_probability_groups__(self):
        self.__try_removing_check_probability_frame__()
        subject = self.__create_subject_properties_from_form_values__()
        probabilities = self.database.get_groups_probabilities_from_new_entry(
            subject)
        index_key = 0
        for key in probabilities.keys():
            self.app.startFrame("Probas_" + str(index_key),
                                row=2 + index_key, column=0, colspan=5)
            self.app.addLabel("key_" + str(index_key), key, 0, 0)
            self.app.addLabel("proba_" + str(index_key),
                              round(probabilities[key], 2), 0, 1)
            index_key += 1
            self.app.stopFrame()

    def __create_subject_properties_from_form_values__(self):
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
            self.__try_removing_check_probability_frame__()
            for label in self.labels_to_remove:
                self.app.removeLabel(label)
            for entry in self.entries_to_remove:
                self.app.removeEntry(entry)
            for checkbox in self.checkboxes_to_remove:
                self.app.removeCheckBox(checkbox)
            for button in self.buttons_to_remove:
                self.app.removeButton(button)
            for box in self.option_box_to_remove:
                self.app.removeOptionBox(box)
            self.app.removeFrame("DatabaseDisplay")
            del self.labels_to_remove[:]
            del self.entries_to_remove[:]
            del self.checkboxes_to_remove[:]
            del self.buttons_to_remove[:]
            del self.option_box_to_remove[:]

    def __try_removing_check_probability_frame__(self):
        try:
            for index_key in range(0, len(self.database.groups)):
                self.app.removeLabel("key_" + str(index_key))
                self.app.removeLabel("proba_" + str(index_key))
                self.app.removeFrame("Probas_" + str(index_key))
        except appjar.ItemLookupError:
            pass
