
import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'global_settings.ui'))



class Ui_GlobalSettingsDialog(FORM_CLASS):
    def setupUi(self, GlobalSettingsDialog):
        super().setupUi(GlobalSettingsDialog)
        GlobalSettingsDialog.setObjectName("GlobalSettingsDialog")
        GlobalSettingsDialog.setEnabled(True)
        GlobalSettingsDialog.resize(400, 200)
 
        self.retranslateUi(GlobalSettingsDialog)
