# La fonction extract_files permet de détécter l'arrivé d'un ZIP ayant le même nom de projet dans le dossier de téléchargement de l'utilisateur

# Lorsqu'un tel ZIP est détecté, un message s'affiche dans QGIS demandant à l'utilisateur s'il souhaite extraire les fichiers

# Si l'utilisateur clique sur "Ranger les couches", le ZIP est extrait dans un dossier temporaire du choix de l'utilisateur

# La fonction en appelle une autre pour ajouter les couches avec leurs styles dans QGIS

# Attention s'execute dans le thread watchdog, il faut faire attention aux interactions avec l'interface QGIS

# Alexandre Le bars
# Kartenn
# 2026
# alexlb329@gmail.com

import zipfile
from pathlib import Path
from PyQt5.QtCore import QTimer
from qgis.PyQt.QtWidgets import QFileDialog
import os, time, shutil
from qgis.PyQt.QtWidgets import QPushButton
from qgis.core import Qgis
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QFileDialog





from .add_vector_layers import load_vectors
from .add_raster_layers import load_rasters

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def extract_files():
    """"""

def show_add_banner(project_folder, downloads_path, project_name, style_folder, _zip_path, dockwidget):

    print("Affichage du bandeau d'ajout des couches...")

    bar = iface.messageBar()
    message = bar.createMessage(
        "[Watchdog] ",
        f"Ajout détecté dans : {downloads_path}. Que voulez-vous faire ?"
    )

    btn_ok = QPushButton("Ranger les couches")

    def on_click():
        print("Rangement...")
        try:
            real_extract_files(
                downloads_path,
                project_name,
                style_folder,
                project_folder,
                _zip_path,
                dockwidget
            )
        except Exception as e:
            print("Erreur dans real_extract_files :", e)
        bar.popWidget(message)

    btn_ok.clicked.connect(on_click)
    message.layout().addWidget(btn_ok)
    bar.pushWidget(message, Qgis.Success)



def real_extract_files(downloads_path, project_name, style_folder, project_folder, _zip_path, dockwidget=None):


    # --- Extraction dans dossier ---

    def_folder = QFileDialog.getExistingDirectory(dockwidget, "Sélectionner le dossier de stockage des fichiers")

    extr_folder = os.path.join(def_folder)

    print(f"\nExtract_files indique => Rangement vers : {extr_folder}")

    # Fichiers avant extraction
    before_files = set(os.listdir(extr_folder))

    # Extraction
    with zipfile.ZipFile(_zip_path, 'r') as z:
        z.extractall(extr_folder)

    # Fichiers après extraction
    after_files = set(os.listdir(extr_folder))

    # Nouveaux fichiers
    new_files = after_files - before_files

    # Chemins complets
    new_files_path = [
        os.path.join(extr_folder, f)
        for f in new_files
        if os.path.isfile(os.path.join(extr_folder, f))
    ]

    # Détection des extensions
    vector_ext = {".shp", ".geojson", ".gpkg", ".kml",".las",".laz"}
    raster_ext = {".tiff", ".tif", ".png"}

    def get_extension(path):
        return os.path.splitext(path)[1].lower()

    # Créer le message
    bar = iface.messageBar()
    message = bar.createMessage(
        "[Watchdog] ",
        f"Fichiers déplacés vers : {extr_folder}"
    )

    # Bouton
    btn_ok = QPushButton("Ouvrir ici")

    def on_click():
        # Vecteurs
        print(">>> on_click() déclenché")
        if any(get_extension(f) in vector_ext for f in new_files_path):

            layer_path = {os.path.splitext(os.path.basename(f))[0]: f for f in new_files_path if get_extension(f) in vector_ext}
            print("appel de load_vector")
            load_vectors(layer_path, style_folder, project_folder, project_name, group_name=None, parent=dockwidget)

        # Rasters
        if any(get_extension(f) in raster_ext for f in new_files_path):

            layer_path = {
                os.path.splitext(os.path.basename(f))[0]: f
                for f in new_files_path
                if get_extension(f) in raster_ext
            }

            load_rasters(
                layer_path,
                project_folder,
                project_name,
                style_folder,
                group_name=None,
                parent=dockwidget)

        bar.popWidget(message)

    btn_ok._callback = on_click

    btn_ok.clicked.connect(btn_ok._callback)



    # Ajouter le bouton
    message.layout().addWidget(btn_ok)

    # Afficher
    bar.pushWidget(message, Qgis.Success)





