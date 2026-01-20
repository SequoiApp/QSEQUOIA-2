import zipfile
from pathlib import Path
from PyQt5.QtCore import QTimer
from qgis.PyQt.QtWidgets import QFileDialog
import os, time, shutil
from qgis.PyQt.QtWidgets import QPushButton
from qgis.core import Qgis
from qgis.utils import iface
from qgis.PyQt.QtWidgets import QFileDialog
from ..utils.add_vector_layers import load_vectors
from ..utils.add_raster_layers import load_rasters

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from qgis.PyQt import uic
import os
from ..utils.get_download_folder import get_download_folder
from .watchdog_handler import DownloadEventHandler
from qgis.PyQt.QtWidgets import QButtonGroup


from PyQt5.QtCore import QTimer, QThread

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "watchdog_label.ui")
)

from qgis.PyQt.QtWidgets import QDialog, QButtonGroup

class watchdog_setting(QDialog, FORM_CLASS):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.plugin = plugin

        # bouton OK
        self.OK.clicked.connect(self.close)

        # radio boutons exclusifs
        self.radio_group = QButtonGroup(self)
        self.radio_group.addButton(self.radio_auto)
        self.radio_group.addButton(self.radio_downloads)

        # valeur par défaut au premier lancement
        if not hasattr(self.plugin, "watch_mode"):
            self.plugin.watch_mode = "auto"

        # connecter les radios
        self.radio_auto.toggled.connect(self.update_watch_mode)
        self.radio_downloads.toggled.connect(self.update_watch_mode)

        # initialiser la radio selon le mode stocké
        # initialiser la radio selon le mode stocké
        if self.plugin.watch_mode == "downloads":
            self.radio_downloads.setChecked(True)
        else:
            self.radio_auto.setChecked(True)

        # mettre à jour le label APRÈS avoir coché la radio
        self.update_watch_path_label()

    def update_watch_path_label(self):
        """Met à jour le label du dossier surveillé."""
        if self.plugin.watch_mode == "downloads":
            path = self.plugin.downloads_path
        else:  # auto
            path = self.plugin.current_project_folder or self.plugin.downloads_path

        self.down.setText(str(f"Watchdog monitors: {path}"))

    def update_watch_mode(self):
        """Met à jour le mode d'écoute et relance le watcher."""
        if self.radio_downloads.isChecked():
            self.plugin.watch_mode = "downloads"
            print("[UI] Mode écoute : Téléchargements")
        else:
            self.plugin.watch_mode = "auto"
            print("[UI] Mode écoute : Automatique")

        # mettre à jour le label
        self.update_watch_path_label()

        # relancer le watcher
        if hasattr(self.plugin, "restart_watcher"):
            self.plugin.restart_watcher()

        
    def start_watcher(self):
        if not self.current_project_name:
            print("[watchdog] Nom de projet vide → surveillance impossible")
            return

        # 🔁 choix du dossier selon le mode
        if self.watch_mode == "downloads":
            watch_path = self.downloads_path
            print("[watchdog] Mode manuel → Téléchargements")

        elif self.watch_mode == "project":
            if not self.current_project_folder:
                print("[watchdog] Mode projet sélectionné mais aucun dossier projet")
                return
            watch_path = self.current_project_folder
            print("[watchdog] Mode manuel → Dossier projet")

        else:  # mode AUTO
            if self.current_project_folder:
                watch_path = self.current_project_folder
                print("[watchdog] Mode auto → Dossier projet")
            else:
                watch_path = self.downloads_path
                print("[watchdog] Mode auto → Téléchargements")

        self.stop_watcher()

        event_handler = DownloadEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, watch_path, recursive=False)
        self.observer.start()

        self.watch_path = watch_path


    def stop_watcher(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            print("[watchdog] Surveillance watchdog arrêtée")
            self.observer = None

        if hasattr(self, "zip_timer") and self.zip_timer:
            self.zip_timer.stop()
            print("[watchdog] Timer ZIP arrêté")


    def restart_watcher(self):
        self.stop_watcher()
        self.start_watcher()


    def process_pending_zips(self):
        if not self.pending_zips:
            return

        # On prend le dernier ZIP en attente
        zip_path = self.pending_zips.pop(0)
        self.handle_zip(zip_path)



    def handle_zip(self, zip_path):
        filename = os.path.basename(zip_path)

        if not self.current_project_name:
            print("[watchdog] Projet vide → ZIP ignoré")
            return

        if self.current_project_name.lower() not in filename.lower():
            print("[watchdog] ZIP ignoré (ne correspond pas au projet)")
            return

        if getattr(self, "_zip_in_progress", None) == zip_path:
            print("[watchdog] ZIP déjà en cours de vérification → ignoré")
            return

        print("[watchdog] Vérification de la stabilité du ZIP…")

        self._zip_in_progress = zip_path
        self._zip_path = zip_path
        self._last_size = -1

        self.zip_timer = QTimer(self.iface.mainWindow())
        self.zip_timer.setInterval(500)
        self.zip_timer.timeout.connect(self.check_zip_stable)
        self.zip_timer.start()

    

    def check_zip_stable(self):
        print("[DEBUG] check_zip_stable thread =", QThread.currentThread())
        try:
            size = os.path.getsize(self._zip_path)
        except FileNotFoundError:
            print("[watchdog] ZIP disparu → abandon")
            self.zip_timer.stop()
            self._zip_in_progress = None
            return

        if size == self._last_size:
            print("[watchdog] ZIP stable → émission du signal")

            self.zip_timer.stop()

            self.show_add_banner(
                self,
                project_folder=str(self.current_project_folder),
                downloads_path=str(self.downloads_path),
                project_name=str(self.current_project_name),
                style_folder=str(self.current_style_folder),
                _zip_path=self._zip_path,
                dockwidget=None)


            # Libérer le verrou
            self._zip_in_progress = None
            return

        self._last_size = size

    def show_add_banner(self, project_folder, downloads_path, project_name, style_folder, _zip_path, dockwidget):

        print("Affichage du bandeau d'ajout des couches...")

        bar = iface.messageBar()
        message = bar.createMessage(
            "[Watchdog] ",
            f"Ajout détecté dans : {downloads_path}. Que voulez-vous faire ?"
        )

        btn_ok = QPushButton("Ranger les couches")

        def on_click():
            print("Rangement...")
            try:
                real_extract_files(
                    downloads_path,
                    project_name,
                    style_folder,
                    project_folder,
                    _zip_path,
                    dockwidget
                )
            except Exception as e:
                print("Erreur dans real_extract_files :", e)
            bar.popWidget(message)

        btn_ok.clicked.connect(on_click)
        message.layout().addWidget(btn_ok)
        bar.pushWidget(message, Qgis.Success)



        def real_extract_files(downloads_path, project_name, style_folder, project_folder, _zip_path, dockwidget=None):


            # --- Extraction dans dossier ---

            def_folder = QFileDialog.getExistingDirectory(dockwidget, "Sélectionner le dossier de stockage des fichiers")

            extr_folder = os.path.join(def_folder)

            print(f"\nExtract_files indique => Rangement vers : {extr_folder}")

            # Fichiers avant extraction
            before_files = set(os.listdir(extr_folder))

            # Extraction
            with zipfile.ZipFile(_zip_path, 'r') as z:
                z.extractall(extr_folder)

            # Fichiers après extraction
            after_files = set(os.listdir(extr_folder))

            # Nouveaux fichiers
            new_files = after_files - before_files

            # Chemins complets
            new_files_path = [
                os.path.join(extr_folder, f)
                for f in new_files
                if os.path.isfile(os.path.join(extr_folder, f))
            ]

            # Détection des extensions
            vector_ext = {".shp", ".geojson", ".gpkg", ".kml",".las",".laz"}
            raster_ext = {".tiff", ".tif", ".png"}

            def get_extension(path):
                return os.path.splitext(path)[1].lower()

            # Créer le message
            bar = iface.messageBar()
            message = bar.createMessage(
                "[Watchdog] ",
                f"Fichiers déplacés vers : {extr_folder}"
            )

            # Bouton
            btn_ok = QPushButton("Ouvrir ici")

            def on_click():
                # Vecteurs
                print(">>> on_click() déclenché")
                if any(get_extension(f) in vector_ext for f in new_files_path):

                    layer_path = {os.path.splitext(os.path.basename(f))[0]: f for f in new_files_path if get_extension(f) in vector_ext}
                    print("appel de load_vector")
                    load_vectors(layer_path, style_folder, project_folder, project_name, group_name=None, parent=dockwidget)

                # Rasters
                if any(get_extension(f) in raster_ext for f in new_files_path):

                    layer_path = {
                        os.path.splitext(os.path.basename(f))[0]: f
                        for f in new_files_path
                        if get_extension(f) in raster_ext
                    }

                    load_rasters(
                        layer_path,
                        project_folder,
                        project_name,
                        style_folder,
                        group_name=None,
                        parent=dockwidget)

                bar.popWidget(message)

            btn_ok._callback = on_click

            btn_ok.clicked.connect(btn_ok._callback)



            # Ajouter le bouton
            message.layout().addWidget(btn_ok)

            # Afficher
            bar.pushWidget(message, Qgis.Success)








