# La fonction extract_files permet de détécter l'arrivé d'un ZIP ayant le même nom de projet dans le dossier de téléchargement de l'utilisateur

# Les fichiers sont copier et envoyés vers le dossier de couches temporaires de QGIS

# La fonction en appelle une autre pour ajouté les couches avec leurs styles dans QGIS

# Alexandre Le bars
# Kartenn
# 2026
# alexlb329@gmail.com

import zipfile
from pathlib import Path
from PyQt5.QtCore import QTimer
import os, time, shutil

from .add_layers import add_layers


def extract_files(downloads_path, project_name, style_folder) :

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

            # --- Test 2 : ZIP complet (taille stable)
            size1 = os.path.getsize(zip_path)
            time.sleep(0.5)  # petite pause
            size2 = os.path.getsize(zip_path)

            if size1 != size2:
                print("\nExtract_files indique => ZIP encore en téléchargement :", file)
                continue  # on attend le prochain cycle

            # --- Extraction dans dossier temporaire ---
            temp_folder = os.path.join(downloads_path, f"{project_name}_TEMPO_output")

            if os.path.exists(temp_folder):
                return

            os.makedirs(temp_folder, exist_ok=True)
            print(f"\nExtract_files indique => dossier tempo == {temp_folder}")

            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(temp_folder)

            # appel de la fonction d'ajout des couches : 

            add_layers(project_name, temp_folder, style_folder)



            return  # on sort dès qu’un ZIP valide a été traité
        

    # Si on sort de la boucle sans avoir trouvé de ZIP valide
    return





