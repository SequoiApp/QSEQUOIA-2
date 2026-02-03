from qgis.PyQt.QtWidgets import QDialog, QMessageBox

from PyQt5.QtWidgets import QDialog, QMessageBox, QFileDialog
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QCheckBox,QComboBox
from PyQt5.QtCore import Qt, QTimer


from qgis.core import QgsProject

#from .project_settings_service import compute_layout_info, import_layout, configure_layout

# Import from utils folder
#from ...utils.config import get_project, get_path, get_project_canvas, get_project_layout
#from ...utils.layers import configure_snapping 
#from ...utils.utils import show_message, clear_project, create_project
#from ...utils.variable import set_project_variable, get_project_variable, get_global_variable
#from ..forest_settings.forest_settings import ForestSettingsDialog

from pathlib import Path
import os,yaml, sys
from PyQt5 import QtCore, QtGui, QtWidgets
from project_settings_dialog import Ui_ProjectSettingsDialog


class ProjectSettingsDialog(QDialog):
    def __init__(self, current_project_name, current_style_folder, downloads_path, current_project_folder, iface, parent=None):
        super().__init__(parent)
        self.iface = iface

        self.current_project_name=current_project_name
        self.current_style_folder=current_style_folder
        self.downloads_path=downloads_path
        self.curent_project_folder=current_project_folder

        self.ui = Ui_ProjectSettingsDialog()
        self.ui.setupUi(self)

        self.combo_projects = QtWidgets.QComboBox(self)
        self.combo_projects.setObjectName("combo_projects")

        container = self.ui.combo_projects_container
        layout = container.layout()
        if layout is None:
            layout = QtWidgets.QVBoxLayout(container)
            container.setLayout(layout)
        layout.addWidget(self.combo_projects)

        self.get_current_project_type()

        self.current_project_type = None

    
    def layers_tab(self):
        """
        Crée et remplit les onglets de l'objet layers_tab avec un onglet vecteurs et raster,
        lit les couches de project.yaml, si il les trouves dans SEQ_layers.yaml il les ajoute en checkbox dans les onglets
        se modifie en fonction du projet choisi
        """
            
    def get_current_project_type(self):
        """Détermine les projets disponibles via project.yaml et remplit la combo Python."""
        yaml_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "inst", "project.yaml")
        )

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        if not isinstance(data, dict):
            return

        project_type = list(map(str, data.keys()))
        print(project_type)

        cb = self.combo_projects  # ← la combo créée dans __init__
        cb.blockSignals(True)
        cb.clear()

        # Variante A — propre avec placeholder (Qt ≥ 5.12/5.15)
        try:
            cb.addItems(project_type)
            cb.setCurrentIndex(-1)  # aucune sélection
            cb.setPlaceholderText("Sélectionner un thème…")
        except AttributeError:
            # Variante B — fallback universel : 1er item = invitation désactivée
            cb.addItem("— Sélectionner un thème —")
            cb.setItemData(0, 0, Qt.UserRole - 1)     # disabled
            cb.setItemData(0, Qt.gray, Qt.ForegroundRole)
            cb.addItems(project_type)
            cb.setCurrentIndex(0)

        cb.blockSignals(False)

        # Logs de contrôle
        print("count:", cb.count())
        for i in range(cb.count()):
            print("item", i, "=", cb.itemText(i))


        # --- après la création et insertion de la combo ---
        QtCore.QTimer.singleShot(0, self._finalize_ui)

    def _finalize_ui(self):
        self.layout().activate()
        self.adjustSize()
        self.repaint()




    def create_new_project():
        """Ajoute la possibilité de créer un nouveau projet personnalisé"""

"""


    # ------------------------------------------------------------------------

    # ------------------------------------------------------------------------

    def _get_project_key(self):
        selected_project_name = self.ui.comboBox_projects.currentText()
        project_key = next((key for key, name in self.projects_list.items() if name == selected_project_name), None)
        return project_key
    
    def accept(self):
        project_key = self._get_project_key()
        if not project_key:
            show_message(self.iface, f"Projet {project_key} n'existe pas", "critical", 15)
            return 

        # Resolve path and check existence
        project_path = get_path(project_key)
        if project_path.exists():
            reply = QMessageBox.question(
                self.iface.mainWindow(),
                "Projet existant",
                f"Le projet '{project_key}' existe déjà.\n"
                "Souhaitez-vous l'ouvrir plutôt que d'en créer un nouveau ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                # Open existing project and exit early
                print("Opening existing project:", project_path)
                self.project.read(str(project_path))
                new_forest_dir = ForestSettingsDialog.get_forest_path_lookup().get(get_project_variable("forest_dirname"))
                set_project_variable("forest_directory", new_forest_dir)
                super().accept()
                return
        
        try:
            set_project_variable("forest_map_project", project_key) #why do i need that ? I think is because of composer but i'm not sure anymore
            clear_project()
            create_project(project_key)
            configure_snapping()

            if project_key == "expertise":
                placette = LayerManager("placette").layer
                style_path = Path(get_global_variable("styles_directory")) / "EXPERTISE_placette.qml"
                placette.loadNamedStyle(str(style_path))

                transect = LayerManager("transect").layer
                style_path = Path(get_global_variable("styles_directory")) / "EXPERTISE_transect.qml"
                transect.loadNamedStyle(str(style_path))
            
            show_message(self.iface, f"Projet {project_key} généré avec succès", "success", 15)
            
            canvas_cfg = get_project_canvas(project_key)
            layout_cfg = get_project_layout(project_key)

            if self.ui.cb_composeur.isChecked():
                # Create layout
                # "parca_polygon" is used inside compute_layout_info considering all project should have downloaded parca
                info = compute_layout_info(scale = canvas_cfg.scale, coeff_cadre = self.ui.dsb_occup.value()/100)
                layout = import_layout(self.project, info.paper_format, info.orientation)
                
                # configure layout
                if layout:
                    configure_layout(self.project, self.iface, layout, layout_cfg.theme, canvas_cfg.scale, layout_cfg.legends)
                    self.iface.openLayoutDesigner(layout)
                    
            self.project.setFileName(str(project_path))
            self.project.setTitle(project_path.stem)

            super().accept()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue :\n{e}")
"""