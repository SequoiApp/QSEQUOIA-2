from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.PyQt.QtWidgets import QDoubleSpinBox
from qgis.PyQt import QtGui, QtWidgets, uic
import os

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'WMS_settings.ui'))

class Ui_WMSSettingsDialog(FORM_CLASS):
    def setupUi(self, WMSSettingsDialog):
        """"""