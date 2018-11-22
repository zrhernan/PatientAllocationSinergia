import unittest
import patientalloc
from pathlib import Path
import os


class testGUISettings(unittest.TestCase):
    def setUp(self):
        self.GUISettings = patientalloc.GUISettings()
        dirname, _ = os.path.split(os.path.abspath(__file__))
        self.fullpath = dirname + "/database/settings.yml"

    def testGUISettingsCreation(self):
        self.assertEqual(self.GUISettings.settingsFile, str(
            Path.home()) + '/.patientalloc/settings.yml')
        self.__assertDefaulDatabasetSettingsValues__()

    def testGUISettingsFileCreation(self):
        self.GUISettings.settingsFile = self.fullpath
        self.GUISettings.createSettingsFile()
        self.assertTrue(os.path.isdir(str(Path.home()) + '/.patientalloc'))
        self.assertTrue(os.path.exists(self.fullpath))

    def testSaveGUISettings(self):
        self.GUISettings.settingsFile = self.fullpath
        self.GUISettings.save()
        self.assertTrue(os.path.exists(self.fullpath))

    def testLoadGUISettings(self):
        self.GUISettings.settingsFile = self.fullpath
        self.GUISettings.save()
        self.GUISettings.fileName = ""
        self.GUISettings.folder = ""
        self.GUISettings.server = ""
        self.GUISettings.saveMode = ""
        self.GUISettings.load()
        self.__assertDefaulDatabasetSettingsValues__()

    def __assertDefaulDatabasetSettingsValues__(self):
        xmlFilePath = str(Path.home()) + "/.cnbitk/cnbimi/xml/"
        xmlFileName = "mi_stroke_prot.xml"
        self.assertEqual(self.GUISettings.fileName, "sinergia.db")
        self.assertEqual(self.GUISettings.folder, str(
            Path.home()) + '/.patientalloc/SinergiaPatients')
        self.assertEqual(self.GUISettings.server, "")
        self.assertEqual(self.GUISettings.saveMode, "local")
        self.assertEqual(self.GUISettings.subjectCreationType, "BCI")
        self.assertEqual(self.GUISettings.savingProperties, {"folder": str(Path.home()) + "/data/",
                                                             "xmlFilePath": xmlFilePath, "xmlFileName": xmlFileName})

    def tearDown(self):
        if os.path.exists(self.fullpath):
            os.remove(self.fullpath)
