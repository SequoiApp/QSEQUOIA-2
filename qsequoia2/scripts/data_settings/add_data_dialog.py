
import os, yaml
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'add_data.ui'))


class Ui_AddDataDialog(FORM_CLASS):
    def setupUi(self, AddDataDialog):
        super().setupUi(AddDataDialog)



        AddDataDialog.setObjectName("AddDataDialog")
        AddDataDialog.resize(600, 500)
 
        self.retranslateUi(AddDataDialog)



 

    def retranslateUi(self, AddDataDialog):
        """"""