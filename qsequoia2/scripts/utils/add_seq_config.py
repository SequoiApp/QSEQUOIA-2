# La fonction add seq_config permet de télécharger depuis le repo gitlab à chaque démarrage du plugin 
# Une version des yaml de configuration à jour pour les couches RSequoia2
# Elle remplace les fichiers locaux s'ils sont différents de ceux en ligne


# Auteur : Alexandre Le bars - Comité des Forêts 

# alexlb329@gmail.com


#---------------------------------------------------------------------------------

import os
import urllib.request
import yaml
from qgis.PyQt.QtWidgets import QMessageBox

#---------------------------------------------------------------------------------


def add_seq_config():
    """Télécharge et met à jour les fichiers de configuration RSequoia2 depuis le dépôt distant."""
    
    # Récupération du dossier de configuration de QSequoia2

    script_path = os.path.dirname(os.path.abspath(__file__))
    inst = os.path.abspath(os.path.join(script_path, '..', '..', 'inst'))

    # Lecture du YAML des URLs 

    urls_yaml_path = os.path.join(inst, 'URLs.yaml')
    with open(urls_yaml_path, 'r', encoding='utf-8') as file:
        urls_data = yaml.safe_load(file)
    seq_layers_url = urls_data['seq_layers']['url']

    # Connexion au dépôt GitHub pour récupérer les fichiers YAML

    for key, entry in urls_data.items():

        # Récupération de l’URL dans le sous-dictionnaire
        url = entry.get("url")
        if not url:
            print(f"[WARN] Pas d'URL pour {key}, ignoré.")
            continue

        try:
            response = urllib.request.urlopen(url)
            remote_yaml_content = response.read().decode('utf-8')
        except Exception as e:
            QMessageBox.critical(None, "Erreur de téléchargement",
                                f"Impossible de télécharger {key}.yaml.\nErreur : {e}")
            continue

        local_yaml_path = os.path.join(inst, f"{key}.yaml")

        try:
            with open(local_yaml_path, 'w', encoding='utf-8') as local_file:
                local_file.write(remote_yaml_content)
        except Exception as e:
            QMessageBox.critical(None, "Erreur d'écriture",
                                f"Impossible d'écrire {key}.yaml.\nErreur : {e}")
            return
        
        # Message de confirmation dans les logs de QGIS

    print("Les fichiers de configuration RSequoia2 ont été mis à jour avec succès.")


