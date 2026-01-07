import os
from qgis.PyQt.QtWidgets import QFileDialog

def create_SIG_folder(nom_projet, style_folder, parent_widget=None,log=None,dockwidget=None, iface=None):
    """
    nom_projet : nom du projet (string)
    parent_widget : ton DockWidget (pour QFileDialog)
    log : fonction de log (ex: self.dockwidget.append_log)
    """


    # --- Sélection du dossier source ---
    dossier_source = QFileDialog.getExistingDirectory(
        parent_widget,
        "Enregistrer le dossier dans..."
    )

    if not dossier_source:
        print("Aucun dossier sélectionné. Fin du script.")
        return None

    # --- Création du dossier principal ---
    chemin_complet = os.path.join(dossier_source, f"{nom_projet}_KARTENN_SIG")
    os.makedirs(chemin_complet, exist_ok=True)
    print(f"Création de l'arborescence dans : {chemin_complet}")

    # --- Structure des sous-dossiers ---
    structure = {
        "0 SORTIE": {},
        "1 RASTER": {},
        "2 VECTEUR": {
            "2.1.point": {},
            "2.2.line": {},
            "2.3.polygon": {}
        },
        "3 TEMPO": {},
        "4 ZONAGE": {},
        "5 LIDAR": {},
        "6 ENVIRONNEMENTS": {}
    }

    # --- Fonction récursive ---
    def creer_dossiers(base_path, structure):
        for dossier, sous_dossiers in structure.items():
            chemin_dossier = os.path.join(base_path, dossier)
            try:
                os.makedirs(chemin_dossier, exist_ok=True)
                print(f"Dossier créé : {chemin_dossier}")
            except Exception as e:
                print(f"Erreur lors de la création de {chemin_dossier} : {e}", "ERROR")

            if isinstance(sous_dossiers, dict) and sous_dossiers:
                creer_dossiers(chemin_dossier, sous_dossiers)

    creer_dossiers(chemin_complet, structure)

    # --- Copie du template QGIS ---
    template = os.path.join(os.path.dirname(__file__), "../../data/template/KARTENN.qgz")
    nouveau_nom = f"{nom_projet}.qgz"
    destination = os.path.join(chemin_complet, nouveau_nom)

    import shutil
    shutil.copy(template, destination)
    print(f"Template copié : {destination}")

    # --- Ouvrir le dossier dans l'explorateur ---

    os.startfile(chemin_complet)






