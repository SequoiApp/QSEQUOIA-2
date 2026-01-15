
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsMessageLog,
    Qgis)
from qgis.core import QgsRasterLayer
from .config import get_style




def load_rasters(layer_path, project_folder, project_name, style_folder, group_name=None, parent=None):
    """
    Load raster layers into the QGIS project. Create group if at least one raster is valid.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    group = None
    loaded_keys = []

    for key, path in layer_path.items():

        # --- Charger le raster correctement ---
        layer = QgsRasterLayer(path, key, "gdal")
        print(f"\nload_rasters : adding {layer}")

        if not layer.isValid():
            QgsMessageLog.logMessage(
                f"Failed to load raster '{key}' from {path}",
                "Qsequoia2",
                Qgis.Warning
            )
            continue

        # --- Créer le groupe si nécessaire ---
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