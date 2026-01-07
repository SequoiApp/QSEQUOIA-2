from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from qgis.PyQt import uic
import os
from .get_download_folder import get_download_folder


FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "connect_label.ui")
)

class connect_label(QDialog, FORM_CLASS):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.plugin = plugin

        self.downloads_path = get_download_folder()
        print("Dossier Téléchargements :", self.downloads_path)
        
        self.down_path.setText(str(self.downloads_path))
        
        self.chk_listen.stateChanged.connect(self.on_listen_changed)

        self.OK.clicked.connect(self.close)


    def on_listen_changed(self, state):
        if state == 2:
            self.plugin.start_watcher()
        else:
            self.plugin.stop_watcher()
    












