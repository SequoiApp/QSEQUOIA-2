import os
from PyQt5.QtCore import QObject, QTimer
from watchdog.observers import Observer
from qgis.PyQt.QtCore import QThread

from ..utils.watchdog_handler import DownloadEventHandler
from ..utils.extract_files import show_add_banner


class DogWatcher(QObject):
    def __init__(self, iface, get_context_callback, parent=None):
        super().__init__(parent)

        self.iface = iface
        self.get_context = get_context_callback

        self.observer = None
        self.watch_path = None

        self.pending_zips = []
        self._zip_in_progress = None
        self._zip_path = None
        self._last_size = -1

        self.zip_timer = None

        # Timer de polling des ZIPs (comme avant)
        self.queue_timer = QTimer(self.iface.mainWindow())
        self.queue_timer.setInterval(500)
        self.queue_timer.timeout.connect(self.process_pending_zips)
        self.queue_timer.start()


    def start(self):
        ctx = self.get_context()

        project_name = ctx["project_name"]
        project_folder = ctx["project_folder"]
        downloads_path = ctx["downloads_path"]
        watch_mode = ctx["watch_mode"]

        if not project_name:
            print("[watchdog] Nom de projet vide → surveillance impossible")
            return

        if watch_mode == "downloads":
            watch_path = downloads_path
            print("[watchdog] Mode manuel → Téléchargements")

        elif watch_mode == "project":
            if not project_folder:
                print("[watchdog] Mode projet sans dossier")
                return
            watch_path = project_folder
            print("[watchdog] Mode manuel → Dossier projet")

        else:  # auto
            watch_path = project_folder or downloads_path
            print("[watchdog] Mode auto →", watch_path)

        self.stop()

        handler = DownloadEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(handler, watch_path, recursive=False)
        self.observer.start()

        self.watch_path = watch_path

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            print("[watchdog] Surveillance arrêtée")

        if self.zip_timer:
            self.zip_timer.stop()
            self.zip_timer = None
    
    def restart(self):
        self.stop()
        self.start()
    

    def process_pending_zips(self):
        if not self.pending_zips:
            return

        zip_path = self.pending_zips.pop(0)
        self.handle_zip(zip_path)
    
    def handle_zip(self, zip_path):
        ctx = self.get_context()
        project_name = ctx["project_name"]

        if not project_name:
            print("[watchdog] Projet vide → ZIP ignoré")
            return

        if project_name.lower() not in os.path.basename(zip_path).lower():
            print("[watchdog] ZIP ignoré (ne correspond pas au projet)")
            return

        if self._zip_in_progress == zip_path:
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
        print("[DEBUG] ZIP thread =", QThread.currentThread())

        try:
            size = os.path.getsize(self._zip_path)
        except FileNotFoundError:
            self.zip_timer.stop()
            self._zip_in_progress = None
            return

        if size == self._last_size:
            self.zip_timer.stop()

            ctx = self.get_context()
            show_add_banner(
                project_folder=str(ctx["project_folder"]),
                downloads_path=str(ctx["downloads_path"]),
                project_name=str(ctx["project_name"]),
                style_folder=str(ctx["style_folder"]),
                _zip_path=self._zip_path,
                dockwidget=None
            )

            self._zip_in_progress = None
            return

        self._last_size = size




