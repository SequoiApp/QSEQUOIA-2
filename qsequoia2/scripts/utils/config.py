import yaml
from pathlib import Path
from dataclasses import dataclass

from qgis.PyQt.QtWidgets import QMessageBox

from .variable import get_project_variable, get_global_variable

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

def get_path(logical_key, forest=None, base_dir=None):
    entry, path = _find_entry(logical_key)
    forest = forest or get_project_variable("forest_prefix")
    base_dir = base_dir or get_project_variable("forest_directory")
    if not forest or not base_dir:
        QMessageBox.critical(None, "Configuration Error", "Veuillez sélectionner une forêt dans 'project_settings'.")
        return None
    
    if not entry:
        return(Path(base_dir).joinpath(*path))

    filename = entry.get("filename")
    if not filename:
        raise KeyError(f"Entry for '{logical_key}' missing 'filename'")

    # ensure dir exists
    folder = Path(base_dir).joinpath(*path)
    folder.mkdir(parents=True, exist_ok=True)

    # prefix if needed
    if not filename.startswith(forest):
        filename = f"{forest}_{filename}"

    return folder / filename

def get_style(logical_key, styles_dir=None):
    entry, _ = _find_entry(logical_key)
    style_name = entry.get("style")
    if not style_name:
        raise KeyError(f"Entry '{logical_key}' missing required 'style'")

    styles_dir = styles_dir or get_global_variable("styles_directory")
    if not styles_dir:
        raise ValueError("Global 'styles_directory' is not set")

    style_path = Path(styles_dir) / style_name
    if not style_path.exists():
        raise FileNotFoundError(f"Style file not found: {style_path}")

    return style_path

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
