# la fonction add_layer récupère les couches ajoutées dans le dossier temporaire, 
# recherche les styles dans le dossier de style, les appliques, et ajoute les couches au projet courant
from pathlib import Path
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsMessageLog,
    Qgis)

from .config import get_style


def load_vectors(layer_path, style_folder, project_folder, project_name, group_name=None, parent=None):

    project = QgsProject.instance()
    root = project.layerTreeRoot()
    group = None
    loaded_keys = []

    for key, path in layer_path.items():

        layer = QgsVectorLayer(path, key, "ogr")
        print(f"\nload_vectors : adding {layer}")

        if not layer.isValid():
            QgsMessageLog.logMessage(
                f"Failed to load vector '{key}' from {path}",
                "Qsequoia2",
                Qgis.Warning
            )
            continue

        # Créer le groupe si nécessaire
        if group_name and group is None:
            group = root.findGroup(group_name) or root.addGroup(group_name)

        # --- Charger le style AVANT d'ajouter la couche ---
        style = get_style(layer_path, style_folder)

        if style:
            try:
                res, msg = layer.loadNamedStyle(str(style))
                if not res:
                    QgsMessageLog.logMessage(f"Impossible d'appliquer le style '{key}': {msg}", "Qsequoia2", Qgis.Warning)
                else:
                    # Appliquer immédiatement le style chargé
                    layer.triggerRepaint()
            except Exception as e:
                QgsMessageLog.logMessage(f"Erreur lors de l'application du style '{key}': {e}", "Qsequoia2", Qgis.Warning)

        # --- Ajouter la couche au projet ---
        project.addMapLayer(layer, not bool(group))

        # --- Ajouter dans le groupe si nécessaire ---
        if group:
            group.addLayer(layer)

        layer.triggerRepaint()
        loaded_keys.append(key)
