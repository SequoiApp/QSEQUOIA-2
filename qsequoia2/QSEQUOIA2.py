import importlib
import console
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication, Qgis
from qgis.PyQt.QtWidgets import QMessageBox,QFileDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
import yaml, timer

from qsequoia2.scripts.global_settings.global_settings import GlobalSettingsDialog
from qsequoia2.scripts.utils.variable import get_global_variable



from .resources import *

# Import the code for the DockWidget
from .QSEQUOIA2_dockwidget import QSEQUOIA2DockWidget
import os.path


from .scripts.tools_settings.PY.unload import unknown_data

from .scripts.utils.connect_label import connect_label

from .scripts.utils.get_download_folder import get_download_folder

from .scripts.utils.extract_files import extract_files

import sys

plugin_path = os.path.dirname(__file__)
watchdog_path = os.path.join(plugin_path, "watchdog_lib")

if watchdog_path not in sys.path:
    sys.path.insert(0, watchdog_path)

from watchdog.observers import Observer

from .scripts.utils.watchdog_handler import DownloadEventHandler





class QSEQUOIA2:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)


        # initialize locale
        locale_value = QSettings().value('locale/userLocale', 'en')
        locale = str(locale_value)[:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'QSEQUOIA2_{locale}.qm'
        )


        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QSEQUOIA2')

        # Trouver le chemins du dossier de téléchargement
        self.updating_project_name = False

        # Watchdog
        self.watch_mode = "auto"
        # valeurs possibles : "auto", "downloads", "project"


        self.observer = None
        self.watch_path = None


        self.current_project_name = None

        self.user_name = get_global_variable("user_full_name") or "Utilisateur QSEQUOIA2"
        print(" \nWelcome ! ", self.user_name)

        self.current_style_folder = get_global_variable("styles_directory") or None
        print(" \n==> Style folder at init:", self.current_style_folder)
        self.current_project_folder = None

        self.watcher = QTimer()
        self.watcher.timeout.connect(self.check_downloads)

        self.downloads_path = get_download_folder()
        print("Téléchargements :", self.downloads_path)
        self.connect_dialog = None

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_downloads)


        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'QSEQUOIA2')
        self.toolbar.setObjectName(u'QSEQUOIA2')

        #print "** INITIALIZING KARTENN_VPC"

        self.pluginIsActive = False
        self.dockwidget = None
        self.dlg = None



    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QSEQUOIA2', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):


        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QSEQUOIA2/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u''),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING QSEQUOIA2"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD QSEQUOIA2"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&QSEQUOIA-2'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING KARTENN_VPC"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = QSEQUOIA2DockWidget(current_project_folder= self.current_project_folder, current_project_name=self.current_project_name, 
                                                      downloads_path = self.downloads_path, current_style_folder = self.current_style_folder, iface=self.iface)


            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # icon du main
            icon_path = os.path.join(plugin_path, "icon.png")
             
            pixmap = QPixmap(icon_path)

            self.dockwidget.icon.setPixmap(pixmap)
            self.dockwidget.icon.setScaledContents(True)
            self.dockwidget.icon.setFixedSize(128, 128)

            # bouttons d'ajout de couches

            self.dockwidget.add_layers.clicked.connect(self.non_implemented_yet)
            self.dockwidget.add_layers.setIcon(QIcon(plugin_path + "/icons/add_data.svg"))

                                




            # show the dockwidget

            self.dockwidget.progressBar.setValue(10)
            print("Chargement… 10%")

            self.dockwidget.progressBar.setValue(50)
            print("Traitement… 50%")

            self.dockwidget.progressBar.setValue(100)
            print("Terminé !")

            # nom du projet

            self.dockwidget.name.setPlaceholderText("Nom du projet - ! idem Rsequoia2 !")
            self.dockwidget.name.textChanged.connect(self.on_project_name_changed)



            #global settings button

            self.dockwidget.setstyle.clicked.connect(self.open_global_settings)
            self.dockwidget.setstyle.setIcon(QIcon(plugin_path + "/icons/global_settings.svg"))

            self.dockwidget.project_folder.clicked.connect(self.set_projectFolder)





            # gestionnaire de connexion

            self.dockwidget.watchdog.clicked.connect(self.open_connect_label)
            self.dockwidget.watchdog.setIcon(QIcon(plugin_path + "/icons/watchdog_settings.svg"))



            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

    def non_implemented_yet(self):
        QMessageBox.information(
            self.dockwidget,
            "Non implémenté",
            "Cette fonctionnalité n'est pas encore implémentée."
        )


    def run_process(self):
        print("Démarrage du traitement…")
        self.dockwidget.progress_bar.setValue(0)

        # étape 1
        self.dockwidget.progress_bar.setValue(20)
        print("Étape 1 terminée")

        # étape 2
        self.dockwidget.progress_bar.setValue(60)
        print("Étape 2 terminée")

        # étape 3
        self.dockwidget.progress_bar.setValue(100)
        print("Traitement terminé")


    def set_projectFolder(self):
        path = QFileDialog.getExistingDirectory(self.dockwidget, "Select project Directory")

        if not path:
            print("No directory selected")
            self.current_project_folder = None
            self.current_project_name = None
            return

        print("Selected directory:", path)
        self.current_project_folder = path

        # extraction du nom du projet

        project_name = None

        for root, dirs, files in os.walk(self.current_project_folder):
            for filename in files:

                if "_matrice" in filename:
                    project_name = filename.split("_matrice")[0]
                    break

                if "_SEQ_PARCA_poly" in filename:
                    project_name = filename.split("_SEQ_PARCA_poly")[0]
                    break

            if project_name:
                break

        # fallback si rien trouvé
        if not project_name:
            project_name = os.path.basename(self.current_project_folder).split("_SIG")[0]
        if self.connect_dialog:
            self.connect_dialog.update_watch_path_label()

        
        self.current_project_name = project_name

        # Propager au DockWidget
        if self.dockwidget:
            self.dockwidget.current_project_name = self.current_project_name
            self.dockwidget.name.blockSignals(True)
            self.dockwidget.name.setText(self.current_project_name)
            self.dockwidget.name.blockSignals(False)

            # Propager aux onglets si nécessaire
            if hasattr(self.dockwidget, "tools_tab"):
                self.dockwidget.tools_tab.current_project_name = self.current_project_name


        self.current_project_name = project_name

        # mettre à jour l'UI de connect_label si elle est ouverte
        if self.connect_dialog:
            self.connect_dialog.update_watch_path_label()


        # redémarrer le watcher
        if self.watcher is not None:
            self.restart_watcher()

            print(f"Project name => {self.current_project_name}")

    
    def on_project_name_changed(self, text):

        # si le changement vient du code → on ignore
        if self.updating_project_name:
            return

        self.current_project_name = text
        print(f"Nom du projet défini manuellement : {text}")

        self.current_project_name = text

        # Propager au DockWidget
        if self.dockwidget:
            self.dockwidget.current_project_name = self.current_project_name
            self.dockwidget.name.blockSignals(True)
            self.dockwidget.name.setText(self.current_project_name)
            self.dockwidget.name.blockSignals(False)

            # Propager aux onglets si nécessaire
            if hasattr(self.dockwidget, "tools_tab"):
                self.dockwidget.tools_tab.current_project_name = self.current_project_name


        if text:  # éviter de lancer sur vide
            if self.watcher is not None:
                self.restart_watcher()
            else:
                print("Watcher non initialisé, rien à redémarrer.")



    def gest_style(self):
        path = QFileDialog.getExistingDirectory(self.dockwidget, "Select stylesDirectory")
        if path:
            print("Selected directory:", path)
            self.current_style_folder = path  # <--- ici on stocke le dossier
        else:
            print("No directory selected")
            self.current_style_folder = None
        
        
        self.current_style_folder = path

        if self.dockwidget:
            self.dockwidget.current_style_folder = self.current_style_folder
            if hasattr(self.dockwidget, "tools_tab"):
                self.dockwidget.tools_tab.current_style_folder = self.current_style_folder




    def open_global_settings(self):
        self.global_settings_dialog = GlobalSettingsDialog(plugin=self)
        self.global_settings_dialog.show()

        
    def open_connect_label(self):
        self.connect_dialog = connect_label(plugin=self)
        self.connect_dialog.show()


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
        if hasattr(self, "observer") and self.observer:
            self.observer.stop()
            self.observer.join()
            print("[watchdog] Surveillance arrêtée")
            self.observer = None



    def restart_watcher(self):
        self.stop_watcher()
        self.start_watcher()


    def check_downloads(self):
        extract_files(
            downloads_path=self.downloads_path,
            project_name=self.current_project_name,
            style_folder = self.current_style_folder,
            project_folder = self.current_project_folder,

            )

