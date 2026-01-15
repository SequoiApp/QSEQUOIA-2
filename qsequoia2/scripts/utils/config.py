# region IMPORT
from qgis.core import (QgsMessageLog,Qgis)
import os
import yaml
from pathlib import Path
from dataclasses import dataclass



from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsWkbTypes



# endregion


# region PLUGIN PATH

def get_plugin_root() -> Path:
    """
    Returns the root directory of the plugin (two levels up from this file).
    """
    return Path(__file__).resolve().parent.parent

def get_config_path(filename: str) -> Path:
    """
    Returns the full path to a file under the plugin's 'config' folder.
    """
    return get_plugin_root() / ".." / "inst" / filename

# endregion

# region SIG_STRUCTURE

_SIG_STRUCT: dict | None = None

def _load_sig_structure() -> dict:
    global _SIG_STRUCT
    if _SIG_STRUCT is None:
        cfg_path = get_config_path("sig_structure.yaml")
        with open(cfg_path, encoding="utf-8") as f:
            _SIG_STRUCT = yaml.safe_load(f)
    return _SIG_STRUCT

def _find_entry(logical_key):
    """
    Return (entry_dict, folder_path_parts) for this key,
    or KeyError if missing entirely.
    """
    struct = _load_sig_structure()["structure"]
    if logical_key in struct.keys():
        path = struct[logical_key].get("path", [])
        return False, path  
    for folder in struct.values():
        files = folder.get("files", {})
        if logical_key in files:
            return files[logical_key], folder.get("path", [])
    raise KeyError(f"No entry for '{logical_key}' in sig_structure.yaml")


# endregion

# region GET PATH


# ----------------------------------------------------------------------------------
# Fonction get_path modifiée pour rechercher la couche dans le dossier de projet
# ----------------------------------------------------------------------------------

def get_path(label, project_name, project_folder, style_folder, parent):

    path = find_best_layer_qgis(project_folder, label)

    if path:
        QgsMessageLog.logMessage(
            f"Layer trouvé : {path}",
            "Qsequoia2",
            level=Qgis.Info
        )
        return {label: path}

    QgsMessageLog.logMessage(
        f"Aucune couche trouvée pour {label}",
        "Qsequoia2",
        level=Qgis.Warning
    )
    return {}


# Fonction utilitaire de get_path pour trouver les couches

def find_best_layer_qgis(project_folder, label, max_candidates=3):
    """
    Version optimisée pour plugin QGIS, support vecteur + raster
    """

    label = label.lower()
    parts = label.split("_")

    expected_geom = None
    if parts[-1] in ("poly", "line", "point"):
        expected_geom = parts[-1]
        parts = parts[:-1]

    expected_tokens = parts

    # Extensions supportées
    vector_exts = (".shp", ".gpkg", ".geojson")
    raster_exts = (".tif", ".img")

    candidates = []

    for root, _, files in os.walk(project_folder):
        for f in files:
            fname = f.lower()
            path = os.path.join(root, f)

            score = 0

            # --- Détection vecteur
            if fname.endswith(vector_exts):
                if expected_geom and expected_geom in fname:
                    score += 50
                for token in expected_tokens:
                    if token in fname:
                        score += 20
                if score > 0:
                    candidates.append((score, path))

            # --- Détection raster
            elif fname.endswith(raster_exts):
                # Pour raster, on ne teste pas la géométrie
                # juste les tokens métier
                for token in expected_tokens:
                    if token in fname:
                        score += 20
                if score > 0:
                    candidates.append((score, path))

    if not candidates:
        return None

    # On garde les N meilleurs
    candidates.sort(reverse=True)
    candidates = candidates[:max_candidates]

    # ----------------------------
    # Vérification finale
    # ----------------------------
    for _, path in candidates:
        if path.lower().endswith(vector_exts):
            # vecteur → vérification géométrie
            layer = QgsVectorLayer(path, "tmp", "ogr")
            if not layer.isValid():
                continue
            g = QgsWkbTypes.geometryType(layer.wkbType())
            found_geom = None
            if g == QgsWkbTypes.PolygonGeometry:
                found_geom = "poly"
            elif g == QgsWkbTypes.LineGeometry:
                found_geom = "line"
            elif g == QgsWkbTypes.PointGeometry:
                found_geom = "point"
            if expected_geom and found_geom != expected_geom:
                continue
            return path

        elif path.lower().endswith(raster_exts):
            # raster → on accepte directement
            return path

    return None



# endregion

# region STYLES


# ----------------------------------------------------------------------------------
# Fonction get_style modifiée pour rechercher le style dans le dossier de styles
# ----------------------------------------------------------------------------------



def get_style(layer_path, style_folder):
    """
    Sélectionne le fichier de style (.qml) pour une couche vecteur ou raster
    en fonction de son label.
    
    layer_path : dict {label: path}
    style_folder : dossier contenant les .qml
    """
    if not style_folder:
        raise ValueError("Global 'styles_directory' is not set")
    
    label, path = next(iter(layer_path.items()))
    label_lower = label.lower()

    # --- Extraire token métier + type de géométrie (vecteur)
    parts = label.split("_")
    geom = ""
    if len(parts) >= 2 and parts[-1] in ("poly", "line", "point"):
        geom = parts[-1]
        token = parts[1]
        token_with_geom = f"{token}_{geom}"
    elif len(parts) >= 2:
        token = parts[1]
        token_with_geom = token
    else:
        token = label_lower
        token_with_geom = token


    token_with_geom = token_with_geom.lower()
    token = token.lower()  # pour fallback

    # --- Scan des fichiers QML
    if not os.path.isdir(style_folder):
        return None

    # --- Liste des fichiers QML
    qml_files = [f for f in os.listdir(style_folder) if f.lower().endswith(".qml")]

    best_match = None

    # Cherche un match exact token + geom (vecteur)
    for f in qml_files:
        fname = os.path.splitext(f)[0].lower()
        if token_with_geom in fname:
            best_match = os.path.join(style_folder, f)
            break

    # Si pas trouvé, match sur token seul (vecteur ou raster)
    if not best_match:
        for f in qml_files:
            fname = os.path.splitext(f)[0].lower()
            if token in fname:
                best_match = os.path.join(style_folder, f)
                break

    # Si toujours pas trouvé, pour raster on peut tester juste label complet
    if not best_match and not geom:
        for f in qml_files:
            fname = os.path.splitext(f)[0].lower()
            if label_lower in fname:
                best_match = os.path.join(style_folder, f)
                break

    return best_match


    
    

    









def get_display_name(logical_key):
    """
    Return the display_name for this logical_key,
    or the key itself if none defined.
    """
    entry, _ = _find_entry(logical_key)
    return entry.get("display_name")

def get_project(folder: str = "output_folder"):

    structure = _load_sig_structure()["structure"]

    if folder not in structure:
        raise KeyError(f"Dossier '{folder}' non trouvé dans sig_structure.yaml")

    files = structure[folder]["files"]
    project_names = {key: get_display_name(key) for key in files.keys()}

    return project_names
  
# endregion

# region WMTS

# -----------------------------------------------------------------------
# WMTS
# -----------------------------------------------------------------------

def get_wmts(logical_key):
    wmts_config_path = get_config_path("qseq_URLS.yaml")
    with open(wmts_config_path, "r", encoding="utf-8") as f:
        wmts_config = yaml.safe_load(f)

    wmts_entries = wmts_config.get("wmts", {})

    # 1) Recherche directe par clé YAML
    entry = wmts_entries.get(logical_key)
    if entry:
        return entry.get("display_name"), entry.get("url")

    # 2) Recherche par display_name
    for key, data in wmts_entries.items():
        if data.get("display_name") == logical_key:
            return data.get("display_name"), data.get("url")

    # 3) Rien trouvé → erreur propre
    raise KeyError(f"No WMTS config for key or display_name '{logical_key}'")



# endregion

# region PROJECT

_PROJECT: dict | None = None

def _load_project() -> dict:
    global _PROJECT
    if _PROJECT is None:
        cfg_path = get_config_path("project.yaml")
        with open(cfg_path, encoding="utf-8") as f:
            _PROJECT = yaml.safe_load(f)
    return _PROJECT

@dataclass
class ProjectCanvas:
    scale: int
    zoom_on: str
    readonly: list | None
    groups: list 
    themes: list 

@dataclass
class ProjectLayout:
    theme: str
    legends: list

def _flatten(seq):
    for x in seq:
        if isinstance(x, (list, tuple)):
            yield from _flatten(x)
        else:
            yield x

def get_project_canvas(name: str) -> ProjectCanvas:
    raw = _load_project().get(name, {}).get("canvas", {})
    if "themes" in raw:
        for t in raw["themes"]:
            if isinstance(t, dict) and "show" in t:
                t["show"] = list(_flatten(t["show"]))

    raw.setdefault("readonly", None)      

    return ProjectCanvas(**raw)

def get_project_layout(name: str) -> ProjectLayout:
    raw = _load_project().get(name, {}).get("layout", {})
    return ProjectLayout(**raw)

# endregion
