from watchdog.events import FileSystemEventHandler


class DownloadEventHandler(FileSystemEventHandler):
    """
    Handler watchdog pour QSEQUOIA2
    Déclenche check_downloads() dès qu'un fichier apparaît / change
    """

    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    def on_created(self, event):
        if event.is_directory:
            return
        print(f"[watchdog] Nouveau fichier : {event.src_path}")
        self.plugin.check_downloads()

    def on_moved(self, event):
        if event.is_directory:
            return
        print(f"[watchdog] Fichier déplacé : {event.dest_path}")
        self.plugin.check_downloads()
