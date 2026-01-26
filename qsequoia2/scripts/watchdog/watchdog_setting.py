"""
watchdog_setting.py
===================

Module de configuration du Watchdog pour QSEQUOIA2.

Permet de choisir le mode de surveillance des dossiers (auto / projet / téléchargements),
met à jour l'interface utilisateur et redémarre le DogWatcher du plugin si nécessaire.

Auteur : Alexandre Le bars - Comité des forêts
Date   : 2026-01-20
"""

import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QButtonGroup, QTimer

# --- Charger le fichier .ui pour le dialogue du watchdog
FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "watchdog_label.ui")
)


class watchdog_setting(QDialog, FORM_CLASS):
    """
    Dialogue de configuration du Watchdog pour QSEQUOIA2.
    
    Permet de choisir le mode de surveillance (auto / projet / téléchargements)
    et met à jour l'interface ainsi que le DogWatcher du plugin.
    """

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.plugin = plugin  # référence vers le plugin principal

        # --- Bouton OK pour fermer la fenêtre
        self.OK.clicked.connect(self.close)

        # --- Créer un groupe pour les radio boutons (exclusifs)
        self.radio_group = QButtonGroup(self)
        self.radio_group.addButton(self.radio_auto)
        self.radio_group.addButton(self.radio_downloads)

        # --- Valeur par défaut si le plugin n'a pas encore de mode
        if not hasattr(self.plugin, "watch_mode"):
            self.plugin.watch_mode = "auto"

        # --- Connecter les radio boutons à la fonction de mise à jour
        self.radio_auto.toggled.connect(self.update_watch_mode)
        self.radio_downloads.toggled.connect(self.update_watch_mode)

        # --- Initialiser la radio selon le mode stocké dans le plugin
        if self.plugin.watch_mode == "downloads":
            self.radio_downloads.setChecked(True)
        else:
            self.radio_auto.setChecked(True)

        # --- Mettre à jour le label pour afficher le dossier surveillé
        self.update_watch_path_label()

    # ----------------------------------------------------------------------
    def update_watch_path_label(self):
        """
        Met à jour le label du dialogue pour montrer quel dossier est surveillé.
        """
        if self.plugin.watch_mode == "downloads":
            path = self.plugin.downloads_path  # dossier Téléchargements
        else:
            # soit dossier du projet s'il est défini, sinon dossier Téléchargements
            path = self.plugin.current_project_folder or self.plugin.downloads_path

        self.down.setText(f"Watchdog monitors: {path}")

    # ----------------------------------------------------------------------
    def update_watch_mode(self):
        """
        Mise à jour du mode de surveillance selon la radio sélectionnée.
        Redémarre le DogWatcher pour prendre en compte le nouveau mode.
        """
        # --- Mettre directement le mode dans le plugin
        if self.radio_downloads.isChecked():
            self.plugin.watch_mode = "downloads"
        else:
            self.plugin.watch_mode = "project"

        # --- Mettre à jour le label pour refléter le changement
        self.update_watch_path_label()

        # --- Redémarrer le DogWatcher pour appliquer le nouveau mode
        if hasattr(self.plugin, "dogwatcher"):
            # Attention : QTimer.singleShot prend une fonction callable, sans ()
            QTimer.singleShot(50, self.plugin.dogwatcher.restart)
