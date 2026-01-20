from PyQt5.QtCore import QThread, pyqtSignal
import os, time
"""

class WatchdogThread(QThread):
    zipReady = pyqtSignal(str, str, str, str)



    def __init__(self, downloads_path, project_name, project_folder, style_folder):
        super().__init__()

        self.downloads_path = str(downloads_path)
        self.project_name = str(project_name)
        self.project_folder = str(project_folder)
        self.style_folder = str(style_folder)
        self.running = True

    def run(self):
        print("[watchdog-thread] démarrage…")

        while self.running:
            try:
                for file in os.listdir(self.downloads_path):
                    if not file.lower().endswith(".zip"):
                        continue

                    if self.project_name.lower() not in file.lower():
                        continue

                    zip_path = os.path.join(self.downloads_path, file)
                    print(f"[watchdog-thread] ZIP trouvé : {file}")

                    # attendre fin de téléchargement
                    stable = False
                    while not stable:
                        size1 = os.path.getsize(zip_path)
                        time.sleep(0.5)
                        size2 = os.path.getsize(zip_path)
                        stable = (size1 == size2)

                    print("[watchdog-thread] ZIP stable → émission du signal")
                    self.zipReady.emit(zip_path, self.project_folder, self.downloads_path, self.style_folder)

            except Exception as e:
                print("[watchdog-thread] ERREUR :", e)

        time.sleep(1)"""