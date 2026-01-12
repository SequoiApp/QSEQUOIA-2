
from qgis.PyQt.QtWidgets import QDialog, QFileDialog

from .global_settings_dialog import Ui_GlobalSettingsDialog

import yaml

# Import from utils folder
from ...utils.variable import get_global_variable, set_global_variable
from ...utils.config import get_config_path


_agence_config_path = get_config_path("agences.yaml")
with open(_agence_config_path, "r", encoding="utf-8") as f:
    _agence_config = yaml.safe_load(f)['agences']

class GlobalSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_GlobalSettingsDialog()
        self.ui.setupUi(self)
        
        # Liste des agences possibles
        self.agences = list(_agence_config.keys())
        self.ui.combobox_agence.addItems(self.agences)
        
        # Charger les paramètres existants
        self.load_settings()

        # Connecter le bouton OK
        self.ui.buttonBox.accepted.connect(self.save_settings)
        self.ui.stylesButton.clicked.connect(self.select_styles_directory)
        self.ui.modelsButton.clicked.connect(self.select_models_directory)

    def load_settings(self):
        # Agence
        agence = get_global_variable("user_office_name")
        if agence in self.agences:
            self.ui.combobox_agence.setCurrentText(agence) # Sélectionner l'agence si elle existe dans la liste
        else:
            self.ui.combobox_agence.setCurrentIndex(-1)  # Aucun choix par défaut
        
        # Répertoire de styles
        styles_dir = get_global_variable("styles_directory") or ""
        self.ui.stylesInput.setText(styles_dir)
            
        # Répertoire de modèles
        models_dir = get_global_variable("models_directory") or ""
        self.ui.modelsInput.setText(models_dir)
        
        # Utilisateur
        user = get_global_variable("user_full_name")
        self.ui.userInput.setText(user)

    def save_settings(self):
        # Récupère les paramètres
        agence = self.ui.combobox_agence.currentText()
        styles_dir = self.ui.stylesInput.text()
        models_dir = self.ui.modelsInput.text()
        user = self.ui.userInput.text()
        
        # Sauvegarder les paramètres
        set_global_variable("user_office_name", agence)
        set_global_variable("styles_directory", styles_dir)
        set_global_variable("models_directory", models_dir)
        set_global_variable("user_full_name", user)
        
        # Créer et sauvegarder la variable user_office_full_name
        self.set_forest_office(agence)
        
    def set_forest_office(self, agence):
        agence = _agence_config.get(agence, {})
        parts = [
            agence.get("nom", ""),
            agence.get("adresse", ""),
            agence.get("numero", ""),
            agence.get("mail", ""),
            agence.get("site", ""),
        ]
        user_office_full_name = "\n".join(p for p in parts if p)
        set_global_variable("user_office_full_name", user_office_full_name)
        
    def select_styles_directory(self):
        modeles_path = QgsProject.instance().homePath() or str(Path.home())

        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner le répertoire de travail", str(modeles_path))
        if dir_path:
            self.ui.stylesInput.setText(dir_path)

    def select_models_directory(self):
        modeles_path = QgsProject.instance().homePath() or str(Path.home())
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner le répertoire de travail", str(modeles_path))
        if dir_path:
            self.ui.modelsInput.setText(dir_path)
