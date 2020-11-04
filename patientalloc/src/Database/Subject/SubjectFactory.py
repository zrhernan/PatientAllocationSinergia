import patientalloc
import random


class SubjectFactory:
    def __init__(self, database, settings):
        self.database = database
        self.settings = settings

    def addGroup(self, properties):
        properties['Group'] = self.database.getGroupFromNewEntry(properties)
        return properties

    def createSubject(self, properties):
        subject = None
        if self.settings.subjectCreationType == 'Simple':
            subject = patientalloc.Subject(properties)
        elif self.settings.subjectCreationType == 'BCI':
            matching_subject_id, properties['Group'] = self.get_matching_subject_id(properties['Group'])
            subject = patientalloc.BCISubject(properties, self.settings.savingProperties, matching_subject_id)
        return subject

    def get_matching_subject_id(self, new_entry_group):
        nb_of_entries = len(self.database.entries) - 1
        matching_subject_index = random.randint(0, nb_of_entries)
        sham_list = []
        for e in range(nb_of_entries+1):
            if self.database.entries[e]['Group'] != 'BCI':
                sham_list.append(e + 1)
        full_entries_list = [x+1 for x in list(range(len(self.database.entries)))]
        should_not_be_matching_subject = list(set(full_entries_list) ^ set(self.database.finished_entries) | set(self.database.rejected_entries) | set(sham_list) | set(self.database.previously_matched_entries))
        counter = 0
        while matching_subject_index + 1 in should_not_be_matching_subject:
            counter += 1
            if counter > len(self.database.entries):
                new_entry_group = 'BCI'
                break
            else:
                matching_subject_index = random.randint(0, nb_of_entries)
        if new_entry_group == 'Sham':
            self.database.previously_matched_entries.append(matching_subject_index+1)
        return self.database.getEntryId(matching_subject_index), new_entry_group

