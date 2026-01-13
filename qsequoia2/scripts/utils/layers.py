from pathlib import Path
from qgis.core import (
    QgsProject,
    QgsRasterLayer,
    QgsVectorLayer,
    QgsMessageLog,
    Qgis,
    QgsRelation,
    QgsEditorWidgetSetup,
)
from osgeo import ogr

from .config import get_wmts, get_style, get_path, get_display_name, get_wmts

# region LOAD LAYERS

def load_wmts(*wmts_keys, group_name = None):
    """
    Load WMTS layers by key (from wmts.yaml) into the project.
    If group_name is given, layers go into that group (hidden at root); 
    otherwise they appear at the root legend.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()

    # find or create the target group
    group = None
    if group_name:
        group = root.findGroup(group_name) or root.addGroup(group_name)

    for key in wmts_keys:
        display_name, url = get_wmts(key)
        if project.mapLayersByName(display_name):
            QgsMessageLog.logMessage(f"Layer '{display_name}' already loaded, skipping.", "Qsequoia2", Qgis.Info)
            print(f"Layer '{display_name}' already loaded, skipping.")
            continue

        layer = QgsRasterLayer(str(url), display_name, "wms")

        if not layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load WMTS '{key}' from {url}", "Qsequoia2", Qgis.Warning)
            continue

        # add to project, optionally hide it from the legend
        project.addMapLayer(layer, not bool(group))

        if group:
            group.addLayer(layer)

def load_vectors(*vector_keys, group_name=None):
    """
    Load vector layers by key into the project. Create group only if at least one is valid.
    Returns a list of successfully loaded keys.
    """
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    group = None
    loaded_keys = []

    for key in vector_keys:
        display_name = get_display_name(key)

        path = get_path(key)
        layer = QgsVectorLayer(str(path), display_name, "ogr")

        # Skip invalid layers
        if not layer.isValid():
            QgsMessageLog.logMessage(f"Failed to load vector '{key}' from {path}", "Qsequoia2", Qgis.Warning)
            continue

        # Create group only if a layer will be added
        if group_name and group is None:
            group = root.findGroup(group_name) or root.addGroup(group_name)

        project.addMapLayer(layer, not bool(group))
        if group:
            group.addLayer(layer)

        try:
            style_path = get_style(key)
            layer.loadNamedStyle(str(style_path))
        except Exception as e:
            QgsMessageLog.logMessage(f"Could not style '{key}': {e}", "Qsequoia2", Qgis.Warning)

        layer.triggerRepaint()
        loaded_keys.append(key)

    return loaded_keys

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

def resolve_layer_name(key: str) -> str:
    # Try alias lookup
    try:
        name = get_display_name(key)   # vector/alias
        if name:
            return name
    except KeyError:
        pass

    # Try WMTS lookup
    try:
        layer_name, _ = get_wmts(key)   # WMTS fallback
        if layer_name:
            return layer_name
    except KeyError:
        pass

    # Final fallback: assume it's already a layer name
    return key
   

def set_layers_readonly(*keys):
    for key in keys:
        name = get_display_name(key)
        layer = QgsProject.instance().mapLayersByName(name)
        if layer:
            vector_layer = layer[0]
            if isinstance(vector_layer, QgsVectorLayer):
                vector_layer.setReadOnly(True)

def configure_snapping():
    project = QgsProject.instance()
    cfg = project.snappingConfig()       # référence vers la config actuelle

    # 1. Activation globale
    cfg.setEnabled(True)

    # 2. Accrochage sur toutes les couches
    cfg.setMode(Qgis.SnappingMode.AllLayers)

    # 3. Types d’accrochage
    cfg.setTypeFlag(
        Qgis.SnappingTypes(
            Qgis.SnappingType.Vertex |
            Qgis.SnappingType.Segment |
            Qgis.SnappingType.MiddleOfSegment |
            Qgis.SnappingType.LineEndpoint
        )
    )

    # 4. Tolérance & unités
    cfg.setTolerance(15)                         # 15 px
    cfg.setUnits(Qgis.MapToolUnit.Pixels)

    # 5. Snapping divers
    cfg.setIntersectionSnapping(True)            # attraper les intersections
    cfg.setSelfSnapping(False)                   # pas de self-snapping (≥ 3.14)

    # 6. Options de topologie & chevauchement
    project.setTopologicalEditing(True)
    project.setAvoidIntersectionsMode(
        Qgis.AvoidIntersectionsMode.AllowIntersections
    )

    # 7. On pousse la config et on rafraîchit éventuellement le canevas
    project.setSnappingConfig(cfg)                                  

    return None
