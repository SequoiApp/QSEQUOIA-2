
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsMessageLog,
    Qgis)




def load_rasters(*raster_keys, group_name=None):
    """
    Load raster layers by key into the project. Create group only if at least one is valid.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    group = None
    loaded_keys = []

    for key in raster_keys:
        display_name = get_display_name(key)
        
        print(f"load_raster - key: {key}")
        path = get_path(key)
        layer = QgsRasterLayer(str(path), display_name)

        # Skip invalid layers
        if not layer.isValid():
            QgsMessageLog.logMessage(f"Invalid raster '{key}' at {path}", "Qsequoia2", Qgis.Warning)
            continue
        
        loaded_keys.append(key)

        # Create group only when actually needed
        if group_name and group is None:
            group = root.findGroup(group_name) or root.addGroup(group_name)

        project.addMapLayer(layer, not bool(group))
        if group:
            group.addLayer(layer)

        # Try styling
        try:
            style_path = get_style(key)
            layer.loadNamedStyle(str(style_path))
        except Exception as e:
            QgsMessageLog.logMessage(f"Styling failed for '{key}': {e}", "Qsequoia2", Qgis.Warning)

        layer.triggerRepaint()

    return loaded_keys