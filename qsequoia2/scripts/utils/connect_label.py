from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from qgis.PyQt import uic
import os
from .get_download_folder import get_download_folder
from qgis.PyQt.QtWidgets import QButtonGroup

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "connect_label.ui")
)

from qgis.PyQt.QtWidgets import QDialog, QButtonGroup

class connect_label(QDialog, FORM_CLASS):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.plugin = plugin

        # bouton OK
        self.OK.clicked.connect(self.close)

        # radio boutons exclusifs
        self.radio_group = QButtonGroup(self)
        self.radio_group.addButton(self.radio_auto)
        self.radio_group.addButton(self.radio_downloads)

        # valeur par défaut au premier lancement
        if not hasattr(self.plugin, "watch_mode"):
            self.plugin.watch_mode = "auto"

        # connecter les radios
        self.radio_auto.toggled.connect(self.update_watch_mode)
        self.radio_downloads.toggled.connect(self.update_watch_mode)

        # initialiser la radio selon le mode stocké
        # initialiser la radio selon le mode stocké
        if self.plugin.watch_mode == "downloads":
            self.radio_downloads.setChecked(True)
        else:
            self.radio_auto.setChecked(True)

        # mettre à jour le label APRÈS avoir coché la radio
        self.update_watch_path_label()

    def update_watch_path_label(self):
        """Met à jour le label du dossier surveillé."""
        if self.plugin.watch_mode == "downloads":
            path = self.plugin.downloads_path
        else:  # auto
            path = self.plugin.current_project_folder or self.plugin.downloads_path

        self.down.setText(str(f"Watchdog monitors: {path}"))

    def update_watch_mode(self):
        """Met à jour le mode d'écoute et relance le watcher."""
        if self.radio_downloads.isChecked():
            self.plugin.watch_mode = "downloads"
            print("[UI] Mode écoute : Téléchargements")
        else:
            self.plugin.watch_mode = "auto"
            print("[UI] Mode écoute : Automatique")

        # mettre à jour le label
        self.update_watch_path_label()

        # relancer le watcher
        if hasattr(self.plugin, "restart_watcher"):
            self.plugin.restart_watcher()







