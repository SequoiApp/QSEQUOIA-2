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





from .add_layers import add_layers

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler




def extract_files(downloads_path, project_name, style_folder,project_folder,dockwidget=None):

    #---------------------------------------

    #boucle de surveillance : 

    zip_path = None

    for file in os.listdir(downloads_path):
        if file.lower().endswith(".zip") and project_name.lower() in file.lower() :
            zip_path = os.path.join(downloads_path, file)

            # --- Test 1 : ZIP récent (moins de 30 secondes)
            age_seconds = time.time() - os.path.getmtime(zip_path)
            if age_seconds > 30:
                continue  # trop vieux, on ignore

            # --- Test : ZIP complet (taille stable)
            size1 = os.path.getsize(zip_path)
            time.sleep(0.5)  # petite pause
            size2 = os.path.getsize(zip_path)

            if size1 != size2:
                print("\nExtract_files indique => ZIP encore en téléchargement :", file)
                continue  # on attend le prochain cycle
            print("\nExtract_files indique => ZIP détecté et prêt :", file)

            # Appel de l'affichage du message dans le thread principal de QGIS

            #show_add_banner(project_folder, downloads_path, project_name, style_folder, zip_path, dockwidget)
            return
    return
    #---------------------------------------
# A revoir car interaction thread QGIS

def show_add_banner(project_folder, downloads_path, project_name, style_folder, zip_path, dockwidget):
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
                zip_path,
                dockwidget
            )
        except Exception as e:
            print("Erreur dans real_extract_files :", e)
        bar.popWidget(message)

    btn_ok.clicked.connect(on_click)
    message.layout().addWidget(btn_ok)
    bar.pushWidget(message, Qgis.Success)



def real_extract_files(downloads_path, project_name, style_folder, project_folder, zip_path, dockwidget=None):


    # --- Extraction dans dossier temporaire ---
    if project_folder == None :
        def_folder = QFileDialog.getExistingDirectory(dockwidget, "Sélectionner le dossier de stockage des fichiers")

        temp_folder = os.path.join(def_folder, f"{project_name}_extract_output")
    else : 
        temp_folder = os.path.join(project_folder, f"{project_name}_extract_output")

    if os.path.exists(temp_folder):
        return
                

    os.makedirs(temp_folder, exist_ok=True)
    print(f"\nExtract_files indique => dossier tempo == {temp_folder}")

    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(temp_folder)

    # appel de add_layers pour ajouter les couches extraites: 

    # Créer le message
    bar = iface.messageBar()
    message = bar.createMessage(
        "[Watchdog] ",
        f"Fichiers déplacés vers : {temp_folder}"
    )

    # Bouton 1
    btn_ok = QPushButton("Ouvrir ici")
    btn_ok.clicked.connect(lambda: (
        print("ouverture...(appel de add_layers)"),
        add_layers(downloads_path, project_name, project_folder, temp_folder, style_folder, dockwidget=None),

        bar.popWidget(message)
    ))


    # Ajouter les boutons au bandeau
    message.layout().addWidget(btn_ok)

    # Afficher le bandeau (niveau SUCCESS = vert)
    bar.pushWidget(message, Qgis.Success)





