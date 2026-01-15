import importlib
from PyQt5.QtWidgets import QDialog, QMessageBox
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem
import os
import yaml

from qsequoia2.scripts.tools_settings.PY.unload import unknown_data



from .add_data_dialog import Ui_AddDataDialog
from itertools import chain


# Import from utils folder

from qsequoia2.scripts.utils.add_vector_layers import load_vectors
from qsequoia2.scripts.utils.add_wmts_layers import load_wmts
from qsequoia2.scripts.utils.config import *

class AddDataDialog(QDialog):
    def __init__(self, current_project_name, current_style_folder, downloads_path, current_project_folder, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.current_project_name = current_project_name
        self.current_style_folder = current_style_folder
        self.downloads_path = downloads_path
        self.current_project_folder = current_project_folder

        self.ui = Ui_AddDataDialog()
        self.ui.setupUi(self)
        self.add_tree_tab()
        self.dock = parent


        # Connexion des signaux après setupUi
        self.treeVECTOR.itemClicked.connect(self.on_item_clicked)
        self.treeRASTOR.itemClicked.connect(self.on_item_clicked)
        self.treeHECTOR.itemClicked.connect(self.on_item_clicked)
        self.treeCASTOR.itemClicked.connect(self.on_item_clicked)
        # etc.



    def add_tree_tab(self):

        # Widget Vecteurs 

        # 1) Créer le widget qui servira d'onglet
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 2) Créer le QTreeWidget
        self.treeVECTOR = QTreeWidget()
        self.treeVECTOR.setObjectName("treeVECTOR")
        self.treeVECTOR.setHeaderLabels(["Vecteurs disponibles"])

        # 3) ajout des items en lisant le yaml
        script_dir = os.path.dirname(__file__)
        yaml_path = os.path.join(script_dir, "..","..","inst","seq_layers.yaml")

        with open(yaml_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

            categories = {}

            for key, entry in data.items():
                name = entry.get('name', "")
                ext = entry.get('ext', "")

                # On ne garde que geojson
                if ext != "geojson":
                    continue

                category_name = name.split("_")[0] if "_" in name else name

                if category_name not in categories:
                    cat_item = QTreeWidgetItem([category_name])
                    self.treeVECTOR.addTopLevelItem(cat_item)
                    categories[category_name] = cat_item

                # Ajout de l’élément dans la catégorie
                QTreeWidgetItem(categories[category_name], [name, ext])


        # 4) Ajouter le tree dans le layout
        layout.addWidget(self.treeVECTOR)

        # 5) Ajouter l’onglet au TabWidget
        self.ui.tabWidget.addTab(tab, "VECTEURS")

        # Widget Rasters

        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.treeRASTOR = QTreeWidget()
        self.treeRASTOR.setObjectName("treeRASTOR")
        self.treeRASTOR.setHeaderLabels(["Rasters disponibles"])

        with open(yaml_path, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

            categories = {}

            for key, entry in data.items():
                name = entry.get('name', "")
                ext = entry.get('ext', "")

                # On ne garde que tiff
                if ext != "tif":
                    continue

                category_name = ext

                if category_name not in categories:
                    cat_item = QTreeWidgetItem([category_name])
                    self.treeRASTOR.addTopLevelItem(cat_item)
                    categories[category_name] = cat_item

                # Ajout de l’élément dans la catégorie
                QTreeWidgetItem(categories[category_name], [name, ext])

        layout.addWidget(self.treeRASTOR)
        self.ui.tabWidget.addTab(tab, "RASTERS")

        # Widget Services Web

        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.treeHECTOR = QTreeWidget()
        self.treeHECTOR.setObjectName("treeHECTOR")
        self.treeHECTOR.setHeaderLabels(["Services Web disponibles"])

        yaml_path = os.path.join(script_dir, "..","..","inst","qseq_URLS.yaml")
        with open(yaml_path, 'r', encoding='utf-8') as file:
            WMS_data = yaml.safe_load(file)

            categories = {}

            for key, entry in WMS_data["wmts"].items():
                name = entry.get("display_name", "")
                url = entry.get("url", "")

                suffix = key.replace("wmts_", "", 1)

                # On prend le premier segment : "scan1000" → "scan"
                category_name = suffix.split("_")[0]


                if category_name not in categories:
                    cat_item = QTreeWidgetItem([category_name])
                    self.treeHECTOR.addTopLevelItem(cat_item)
                    categories[category_name] = cat_item

                # Ajout de l’élément dans la catégorie
                QTreeWidgetItem(categories[category_name], [name, url])



        layout.addWidget(self.treeHECTOR)
        self.ui.tabWidget.addTab(tab, "WMS/WFS")

        # Widget Bases de Données
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.treeCASTOR = QTreeWidget()
        self.treeCASTOR.setHeaderLabels(["Bases de Données disponibles"])
        # (code to read YAML and populate tree would go here)
        layout.addWidget(self.treeCASTOR)
        self.ui.tabWidget.addTab(tab, "BASES DE DONNÉES")

    # quand on clique sur un bouton des arborescences la couche est ajoutée au projet

        
    def on_item_clicked(self, item, column):
        tree = self.sender()  # QTreeWidget qui a émis le signal
        label = item.text(0)

        print(f"Clic sur '{label}' depuis l’arbre : {tree.objectName()}")

        self.whats_layers(item, label, column)


    def whats_layers(self, item, label, column):



        print(f"\n[add_data] => Clic sur l'item : {label}")



        # --- Détection automatique des sections (items parents) ---
        if item is not None and item.parent() is None:
            print(f"\n[add_data] => Clique sur une section : {label}")
            return


        # --- Vérifications projet ---
        if not self.current_project_name or self.current_project_name in [
            "Nom du projet - doit être le même que CARTO FUTAIE ou RSEQUOIA",
            "DefaultProject"
        ]:
            QMessageBox.information(
                self,
                "Nom absent",
                "Merci de renseigner le nom du projet."
            )
            return

        if not self.current_style_folder:
            QMessageBox.information(
                self,
                "Kartenn",
                "Pas de dossier de styles sélectionné, veuillez cliquer sur 🔧."
            )
            return

        current_tab = self.ui.tabWidget.tabText(self.ui.tabWidget.currentIndex())

        # --- Appel dynamique ---

        if current_tab == "WMS/WFS":  # index de l'onglet "Paramètres de données"
            load_wmts([label])

        if current_tab == "RASTERS":
            print("Chargement raster")



        else:
            if self.current_project_folder is None:

                layer_paths = {}

                files, _ = QFileDialog.getOpenFileNames(
                    parent=self,
                    caption="Sélectionner une couche",
                    directory="",
                    filter="Couches vecteur (*.shp *.gpkg *.geojson)"
                )

                if files:
                    # Cas normal : un seul label → une seule couche
                    layer_paths[label] = files[0]

            else:
                layer_paths = get_path(
                    label,
                    project_name=self.current_project_name,
                    project_folder=self.current_project_folder,
                    style_folder=self.current_style_folder,
                    parent=self
                )

            if layer_paths:
                load_vectors(
                    layer_paths,
                    project_name=self.current_project_name,
                    project_folder=self.current_project_folder,
                    style_folder=self.current_style_folder,
                    parent=self
                )


