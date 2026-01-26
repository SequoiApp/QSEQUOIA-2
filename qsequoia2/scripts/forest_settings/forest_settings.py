from pathlib import Path

from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QMessageBox
from qgis.core import Qgis, QgsProject
from .forest_settings_dialog import Ui_ForestSettingsDialog

# Import from utils folder
from ..utils.variable import get_project_variable, set_project_variable, get_formated_surface, get_grouped_values_from_shapefile, sum_surface_from_shapefile
from ..utils.config import get_path

class ForestSettingsDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.project = QgsProject.instance()
        self.ui = Ui_ForestSettingsDialog()
        self.ui.setupUi(self)

        # Charger les paramètres existants
        self.load_settings()

        # Connections

        ## refresh button
        self.ui.pushButton_refresh.clicked.connect(self.fill_in_cartouche)

        ## Connection des checkboxes
        self.nom_checkbox = {
            self.ui.checkBox_domaine: "Domaine",
            self.ui.checkBox_massif: "Massif",
            self.ui.checkBox_foret: "Forêt",
            self.ui.checkBox_bois: "Bois",
        }
        for cb in self.nom_checkbox:
            cb.toggled.connect(self.update_forest_name)

        ## Directory selection
        self.ui.pushButton.clicked.connect(self.select_directory)
        
        ## Save
        self.ui.buttonBox.accepted.connect(self.save_settings)

    def load_settings(self):
        directory = get_project_variable("forest_directory")
        if directory:
            self.directory = Path(directory)
            self.ui.lineEdit_folder.setText(str(self.directory))
        else:
            self.directory = None
            self.ui.lineEdit_folder.setText("")

        self.ui.lineEdit_prefixe.setText(get_project_variable("forest_prefix") or "")
        self.ui.lineEdit_name.setText(get_project_variable("forest_name") or "")
        self.ui.lineEdit_city.setText(get_project_variable("forest_city") or "")
        self.ui.lineEdit_owner.setText(get_project_variable("forest_owner") or "")
        self.ui.doubleSpinBox_1.setValue(float(get_project_variable("surface_boisee") or 0))
        self.ui.doubleSpinBox_2.setValue(float(get_project_variable("surface_non_boisee") or 0))

    def save_settings(self):
        # Récupère les paramètres
        directory = str(self.directory) if self.directory else ""
        dirname = Path(directory).name if directory else ""
        prefix = self.ui.lineEdit_prefixe.text()
        name = self.ui.lineEdit_name.text()
        city = self.ui.lineEdit_city.text()
        owner = self.ui.lineEdit_owner.text()
        surface_boisee = self.ui.doubleSpinBox_1.value()
        surface_non_boisee = self.ui.doubleSpinBox_2.value()
        surface_totale = surface_boisee + surface_non_boisee
        formated_surface = get_formated_surface(surface_boisee * 10000, surface_non_boisee * 10000)

        # Create a dictionary of all settings
        settings = {
            "directory": str(directory),
            "dirname": dirname,
            "prefix": prefix,
            "name": name,
            "city": city,
            "owner": owner,
            "surface_boisee": surface_boisee,
            "surface_non_boisee": surface_non_boisee,
            "surface_totale": surface_totale,
            "formated_surface": formated_surface,
            "type_project": "unwooded" if float(surface_non_boisee) > 0 else "wooded"
        }

        # prefix each key with "forest_"
        forest_vars = {f"forest_{k}": v for k, v in settings.items()}
        if not dirname:
            reset_vars = {key: None for key in forest_vars.keys()}
            self.project.setCustomVariables(reset_vars)
            self.ui.lineEdit_prefixe.setText("")
            self.ui.lineEdit_name.setText("")
            self.ui.lineEdit_city.setText("")
            self.ui.lineEdit_owner.setText("")
            self.ui.doubleSpinBox_1.setValue(0)
            self.ui.doubleSpinBox_2.setValue(0)
        else:
            self.project.setCustomVariables(forest_vars)
            
        link = f'<a href="file:///{directory}">{directory}</a>'
        self.iface.messageBar().pushMessage(
            "Qsequoia2",
            f"Dossier {dirname} sélectionné avec succès : {link}",
            level=Qgis.Success,
            duration=10
        )

    def select_directory(self):
        start_dir = QgsProject.instance().homePath() or str(Path.home())
    
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner un dossier de forêt",
            start_dir
        )
    
        if not folder:
            return
    
        self.directory = Path(folder)
        self.ui.lineEdit_folder.setText(folder)
    
        self.fill_in_cartouche()

    def fill_in_cartouche(self):
        if not self.directory or not self.directory.exists():
            QMessageBox.warning(
                self,
                "Dossier invalide",
                "Veuillez sélectionner un dossier valide."
            )
            return
    
        prefix = self._get_prefix_from_directory(self.directory)
        parca_path = get_path("parca_polygon", prefix, self.directory)
        ua_path = get_path("ua_polygon", prefix, self.directory)
    
        self._set_directory_and_prefix(self.directory, prefix)
        self._set_name(prefix)
        self._set_city_and_owner(parca_path)
        self._set_surface(ua_path, parca_path)

    @staticmethod
    def _get_prefix_from_directory(directory):
        """
        Récupère la partie avant le premier '_' dans le nom du dossier.
        Si aucun '_' n'est trouvé, renvoie une chaîne vide.
        """
        name = Path(directory).name
        prefix, sep, suffix = name.partition("_")
        return suffix if sep else prefix

    def _set_directory_and_prefix(self, directory: Path, prefix: str):
        dirname = directory.name
    
        set_project_variable("forest_dirname", dirname)
        set_project_variable("forest_directory", str(directory))
    
        self.ui.lineEdit_prefixe.setText(prefix)
        set_project_variable("forest_prefix", prefix)

    def _set_name(self, prefix):
        self.name = prefix.title() if prefix else ""
        self.ui.lineEdit_name.setText(self.name)
        set_project_variable("forest_name", self.name)

    def _set_city_and_owner(self, parca_path):
        city = owner = ""
        if parca_path.exists():
            city = get_grouped_values_from_shapefile(parca_path, "COM_NOM", "DEP_CODE", "SURF_CA")
            owner = get_grouped_values_from_shapefile(parca_path, "PROP", None, "SURF_CA")

        self.ui.lineEdit_city.setText(city)
        set_project_variable("forest_city", city)

        self.ui.lineEdit_owner.setText(owner)
        set_project_variable("forest_owner", owner)

    def _set_surface(self, ua_path, parca_path):
        surface_boisee = surface_non_boisee = 0

        if not ua_path.exists() and not parca_path.exists():
            QMessageBox.warning(
                None,
                "Couches manquantes",
                f"Pas de couches PARCA ou UA trouvées dans {self.directory}. Impossible de calculer les surfaces."
            )
            return
        
        surface_field = "SURF_COR" if ua_path.exists() else "SURF_CA"
        path = ua_path if ua_path.exists() else parca_path

        surface_boisee = sum_surface_from_shapefile(path, surface_field, "OCCUP_SOL", "BOISEE") or 0
        surface_non_boisee = sum_surface_from_shapefile(path, surface_field, "OCCUP_SOL", "NON BOISEE") or 0

        surface_totale = surface_boisee + surface_non_boisee
        set_project_variable("forest_surface_totale", surface_totale)

        self.ui.doubleSpinBox_1.setValue(surface_boisee)
        set_project_variable("forest_surface_boisee", surface_boisee)

        self.ui.doubleSpinBox_2.setValue(surface_non_boisee)
        set_project_variable("forest_surface_non_boisee", surface_non_boisee)

    def update_forest_name(self):

        base = self.name or get_project_variable("forest_name") or ""

        # find the first‐checked box (if any) and grab its label
        prefix = next((label for cb, label in self.nom_checkbox.items() if cb.isChecked()), "")

        if prefix and base:
            # plural names take " des "
            if base.lower().endswith("s"):
                connector = " des "
            # then vowel or mute-h → d'
            elif base[0].lower() in ("a","e","i","o","u","h"):
                connector = " d'"
            # otherwise normal " de "
            else:
                connector = " de "
            full = f"{prefix}{connector}{base}"
        else:
            full = base
            
        self.ui.lineEdit_name.setText(full)
