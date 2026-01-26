from watchdog.events import FileSystemEventHandler


class DownloadEventHandler(FileSystemEventHandler):
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith(".zip"):
            print(f"[watchdog] Nouveau ZIP détecté : {event.src_path}")
            self.plugin.pending_zips.append(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        if event.dest_path.lower().endswith(".zip"):
            print(f"[watchdog] ZIP déplacé : {event.dest_path}")
            self.plugin.pending_zips.append(event.src_path)
