
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
        self.add_tree_tab()




    def add_tree_tab(self):

        # Widget Vecteurs 

        # 1) Créer le widget qui servira d'onglet
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 2) Créer le QTreeWidget
        tree = QTreeWidget()
        tree.setHeaderLabels(["Vecteurs disponibles"])

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
                    tree.addTopLevelItem(cat_item)
                    categories[category_name] = cat_item

                # Ajout de l’élément dans la catégorie
                QTreeWidgetItem(categories[category_name], [name, ext])


        # 4) Ajouter le tree dans le layout
        layout.addWidget(tree)

        # 5) Ajouter l’onglet au TabWidget
        self.tabWidget.addTab(tab, "VECTEURS")

        # Widget Rasters

        tab = QWidget()
        layout = QVBoxLayout(tab)
        tree = QTreeWidget()
        tree.setHeaderLabels(["Rasters disponibles"])

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
                    tree.addTopLevelItem(cat_item)
                    categories[category_name] = cat_item

                # Ajout de l’élément dans la catégorie
                QTreeWidgetItem(categories[category_name], [name, ext])

        layout.addWidget(tree)
        self.tabWidget.addTab(tab, "RASTERS")

        # Widget Services Web

        tab = QWidget()
        layout = QVBoxLayout(tab)
        tree = QTreeWidget()
        tree.setHeaderLabels(["Services Web disponibles"])

        yaml_path = os.path.join(script_dir, "..","..","inst","qseq_URLS.yaml")
        with open(yaml_path, 'r', encoding='utf-8') as file:
            WMS_data = yaml.safe_load(file)

            categories = {}

            for key, entry in WMS_data["wmts"].items():
                name = entry.get("display_name", "")

                suffix = key.replace("wmts_", "", 1)

                # On prend le premier segment : "scan1000" → "scan"
                category_name = suffix.split("_")[0]


                if category_name not in categories:
                    cat_item = QTreeWidgetItem([category_name])
                    tree.addTopLevelItem(cat_item)
                    categories[category_name] = cat_item

                # Ajout de l’élément dans la catégorie
                QTreeWidgetItem(categories[category_name], [name])



        layout.addWidget(tree)
        self.tabWidget.addTab(tab, "WMS/WFS")

        # Widget Bases de Données
        tab = QWidget()
        layout = QVBoxLayout(tab)
        tree = QTreeWidget()
        tree.setHeaderLabels(["Bases de Données disponibles"])
        # (code to read YAML and populate tree would go here)
        layout.addWidget(tree)
        self.tabWidget.addTab(tab, "BASES DE DONNÉES")


 

    def retranslateUi(self, AddDataDialog):
        """"""