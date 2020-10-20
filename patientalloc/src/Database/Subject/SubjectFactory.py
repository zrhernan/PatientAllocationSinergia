import patientalloc
import random


class SubjectFactory:
    def __init__(self, database, settings, currentGui):
        self.gui = currentGui
        self.app = currentGui.app
        self.database = database
        self.settings = settings

    def createSubject(self, properties):
        properties['Group'] = self.database.getGroupFromNewEntry(properties)
        if self.gui.viewmode is not 'blind':
            self.display_frane_algorithm_results(properties)
            properties['Group'] = self.confirm_new_entry_group_manually(properties['Group'])

        # user_confirm = input(" ________________________________________________________\n"
        #                      "| Do you wish to change this group placement?            |\n"
        #                      " ________________________________________________________\n"
        #                      " ________________________________________________________\n"
        #                      "| WARNING: Selecting 'Y' or 'y' will automatically       |\n"
        #                      "| place the new subject entry into the opposite group.   |\n"
        #                      "| (Press 'Y'/'y' for yes, otherwise press ENTER)         |\n"
        #                      " -------------------------------------------------------- \n"
        #                      "                          ")
        # if user_confirm in ['Y', 'y']:
        #     new_group = [i for i in self.database.groups if properties['Group'] not in i]
        #     properties['Group'] = new_group[0]
        #     print("New entry manually placed into '" + properties['Group'] + "' group.")
        new_entry_group = properties['Group']
        subject = None
        if self.settings.subjectCreationType == 'Simple':
            subject = patientalloc.Subject(properties)
        elif self.settings.subjectCreationType == 'BCI':
            # new_entry_group_orig = new_entry_group
            matching_subject_id, properties['Group'] = self.get_matching_subject_id(new_entry_group)
            if new_entry_group != properties['Group'] and self.gui.viewmode is not 'blind':
                print("New Entry placed in '" + properties['Group'] + "' Group (based on limited matched BCI subjects)")
                self.app.infoBox("NEW GROUP PLACEMENT", "New Entry placed in '" + properties['Group'] +
                                 "' Group (based on limited matched BCI subjects)")
            subject = patientalloc.BCISubject(
                properties, self.settings.savingProperties, matching_subject_id)
        return subject

    def get_matching_subject_id(self, new_entry_group):
        # print("This Subject's Group: " + str(new_entry_group))
        nb_of_entries = len(self.database.entries) - 1
        # print("nb_of_entries: " + str(nb_of_entries))
        matching_subject_index = random.randint(0, nb_of_entries)
        # print("Matching Subject: s0" + str(matching_subject_index+1))
        # print("Old List of Previously Matched Subjects: " + str(self.database.previously_matched_entries))
        # print("Finished Subjects: " + str(self.database.finished_entries))
        # print("Rejected Subjects: " + str(self.database.rejected_entries))
        sham_list = []
        for e in range(nb_of_entries+1):
            if self.database.entries[e]['Group'] != 'BCI':
                sham_list.append(e + 1)
        # print("Sham Group Subjects: " + str(sham_list))
        full_entries_list = [x+1 for x in list(range(len(self.database.entries)))]
        should_not_be_matching_subject = list(set(full_entries_list) ^ set(self.database.finished_entries) | set(self.database.rejected_entries) | set(sham_list) | set(self.database.previously_matched_entries))
        # print("List that shouldn't be matched to subject: " + str(should_not_be_matching_subject))
        counter = 0
        while matching_subject_index + 1 in should_not_be_matching_subject: #matching_subject_index + 1 not in self.database.finished_entries or matching_subject_index + 1 in self.database.rejected_entries or self.database.getEntryGroup(matching_subject_index) != "BCI" or matching_subject_index + 1 in self.database.previously_matched_entries:
            counter += 1
            # print("Count at " + str(counter))
            if counter > len(self.database.entries):
                new_entry_group = 'BCI'
                # print("Changed Group to BCI")
                break
            else:
                matching_subject_index = random.randint(0, nb_of_entries)
        if new_entry_group == 'Sham':
            self.database.previously_matched_entries.append(matching_subject_index+1)
        # print("New List of Previously Matched Subjects: " + str(self.database.previously_matched_entries))
        # print("Final Matching Subject: " + str(self.database.getEntryId(matching_subject_index)))
        return self.database.getEntryId(matching_subject_index), new_entry_group

    def confirm_new_entry_group_manually(self, curr_group):
        opposite_group = [i for i in self.database.groups if curr_group not in i]
        opposite_group = opposite_group[0]
        message = "New entry is in '" + curr_group.upper() + "' group. Do you want to change this?\n" \
                  "-----------------------------------------\n" \
                  "WARNING: Selecting 'Yes' will automatically place the new subject entry into " \
                  "'" + opposite_group.upper() + "' group. If you don't want to make any changes, " \
                  "please select 'No' or close this window."
        title = "NEW ENTRY GROUP CONFIRMATION"
        response = self.app.questionBox(title, message)
        if response:
            new_group = [i for i in self.database.groups if curr_group not in i]
            curr_group = new_group[0]
            print("New Entry manually placed into '" + curr_group.upper() + "' group.")
            self.app.infoBox("NEW GROUP PLACEMENT", "New Entry manually placed into '" + curr_group.upper() + "' group")
        else:
            print("New Entry remains in '" + curr_group.upper() + "' group")
            self.app.infoBox("NEW GROUP PLACEMENT", "New Entry remains in '" + curr_group.upper() + "' group")
        return curr_group

    def display_frane_algorithm_results(self, properties):
        probas = self.database.get_groups_probabilities_from_new_entry(properties)
        group_names = list(probas.keys())
        probs_groups = ["%.3f" % probas[grp] for grp in group_names]

        [_, _, probs_by_field] = self.database.__create_pvalues_for_all_groups__(properties)
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
