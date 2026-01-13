from qgis.PyQt.QtWidgets import QWidget, QMessageBox


import os
import importlib
import yaml

from qsequoia2.scripts.tools_settings.R.run_R import run_r_script
from qsequoia2.scripts.tools_settings.PY.unload import unknown_data
from qsequoia2.scripts.tools_settings.tools_settings_dialog import Ui_ToolsSettingsDialog





class ToolsSettingsDialog(QWidget):
    def __init__(self, current_project_name, current_style_folder, downloads_path, current_project_folder, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.current_project_name = current_project_name
        self.current_style_folder = current_style_folder
        self.downloads_path = downloads_path
        self.current_project_folder = current_project_folder

        self.tools_ui = Ui_ToolsSettingsDialog()
        self.tools_ui.setupUi(self)

        # Connexion des signaux après setupUi
        self.tools_ui.functionsLibrary.itemClicked.connect(self.on_item_clicked)

    #-------------------------------------------------------------------------
    # Import des fonctions externes et appel en fonction de l'item cliqué
    #-------------------------------------------------------------------------

        # Fonction d'appel des fonctions externes python

        
    def on_item_clicked(self, item, column):
        print(f"Clic sur l'item : {item.text(0)}")
        label = item.text(0)

        # Cas R
        if label.startswith("📊"):
            self.call_R_functions(item, column)
        else:
            self.call_functions(item, column)


    def call_functions(self, item, column):


        plugin_dir = os.path.dirname(__file__)
        yaml_path = os.path.join(plugin_dir, "..", "actions.yaml")

        with open(yaml_path, "r", encoding="utf-8") as f:
            action_config = yaml.safe_load(f)["actions"]

        project_name = getattr(self, "current_project_name", "DefaultProject")
        style_folder = getattr(self, "current_style_folder", None)
        label = item.text(0)

        # --- Catégories globales : on ne fait rien ---
        if label in ["Outils en ligne", "Utilitaire python", "Gestion de projets"]:
            print(f"Clique sur un label de catégorie : {label}")
            return

        # --- Vérifie que le label existe ---
        action = action_config.get(label)
        if action is None:
            unknown_data(parent=self)
            return

        # --- Lecture du flag ---
        skip_check = action.get("skip_check", False)

        # --- Vérifications ---
        if not skip_check:

            if not project_name or project_name in [
                "Nom du projet - doit être le même que CARTO FUTAIE ou RSEQUOIA",
                "DefaultProject"
            ]:
                QMessageBox.information(
                    self,
                    "Nom absent",
                    "Merci de renseigner le nom du projet."
                )
                return

            if not style_folder:
                QMessageBox.information(
                    self,
                    "Kartenn",
                    "Pas de dossier de styles sélectionné, veuillez cliquer sur 🔧."
                )
                return

        else:
            # Neutralisation des valeurs manquantes
            project_name = project_name or ""
            style_folder = style_folder or ""

        # --- Appel dynamique ---
        mod_name = action["module"]
        func_name = action["function"]
        print(f"Appel de la fonction {func_name} du module {mod_name}")

        module = importlib.import_module(mod_name)
        func = getattr(module, func_name)

        func(project_name, style_folder, dockwidget=self, iface=self.iface)


        #appel des fonctions R



    def call_R_functions(self, item, column):
        project_name = getattr(self, "current_project_name", "DefaultProject")
        
        if item.text(0) == "📊 Test R":
            run_r_script(project_name, dockwidget=self , iface=self.iface)