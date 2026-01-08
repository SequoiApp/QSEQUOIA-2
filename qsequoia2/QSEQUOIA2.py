import importlib
import console
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsApplication, Qgis
from qgis.PyQt.QtWidgets import QMessageBox,QFileDialog
from PyQt5.QtCore import QTimer
import yaml, timer



from .resources import *

# Import the code for the DockWidget
from .QSEQUOIA2_dockwidget import QSEQUOIA2DockWidget
import os.path


from .scripts.PY.unload import unknown_data

from .scripts.utils.connect_label import connect_label

from .scripts.utils.get_download_folder import get_download_folder

from .scripts.utils.extract_files import extract_files


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
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QSEQUOIA2_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QSEQUOIA2')

        # Trouver le chemins du dossier de téléchargement
        self.watcher = None
        self.current_project_name = None
        self.current_style_folder = None
        self.watcher = None
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
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

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
                self.dockwidget = QSEQUOIA2DockWidget()


            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget

            self.dockwidget.progressBar.setValue(10)
            print("Chargement… 10%")

            self.dockwidget.progressBar.setValue(50)
            print("Traitement… 50%")

            self.dockwidget.progressBar.setValue(100)
            print("Terminé !")

            # nom du projet

            self.dockwidget.project_name.setPlaceholderText("Nom du projet - ! idem CARTO-FUTAIE ou SEQUOIA!")
            self.dockwidget.project_name.textChanged.connect(self.on_project_name_changed)

            #gestionnaire de style

            self.dockwidget.setstyle.clicked.connect(self.gest_style)




            # gestionnaire de connexion

            self.dockwidget.btn_connect.clicked.connect(self.open_connect_label)

            #Appel des process

            self.dockwidget.iface = self.iface
            self.dockwidget.functionsLibrary.itemClicked.connect(self.call_functions)


            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()


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



    def on_project_name_changed(self, text):
        self.current_project_name = text
        project_name = self.current_project_name
        print(f"Nom du projet défini : {project_name}")
        
        if self.current_project_name:  # éviter de lancer sur vide
            if self.watcher is not None:
                self.restart_watcher()
            else:
                self.start_watcher()



    def gest_style(self):
        path = QFileDialog.getExistingDirectory(self.dockwidget, "Select stylesDirectory")
        if path:
            print("Selected directory:", path)
            self.current_style_folder = path  # <--- ici on stocke le dossier
        else:
            print("No directory selected")
            self.current_style_folder = None
    
    def open_connect_label(self):
        self.connect_dialog = connect_label(plugin=self)
        self.connect_dialog.show()

    def start_watcher(self):
        if not self.current_project_name:
            print("Nom de projet vide → surveillance impossible")
            return

        print("Surveillance activée pour :", self.current_project_name)

        # Première exécution immédiate
        self.check_downloads()

        # Puis toutes les secondes
        self.timer.start(1000)

    def stop_watcher(self):
        self.timer.stop()
        print("Surveillance arrêtée")


    def restart_watcher(self):
        self.stop_watcher()
        self.start_watcher()


    def check_downloads(self):
        extract_files(
            downloads_path=self.downloads_path,
            project_name=self.current_project_name,
            style_folder = self.current_style_folder
        )


#-------------------------------------------------------------------------
# Import des fonctions externes et appel en fonction de l'item cliqué
#-------------------------------------------------------------------------


        # Fonction d'appel des fonctions externes python

    def call_functions(self, item, column):

        plugin_dir = os.path.dirname(__file__)
        yaml_path = os.path.join(plugin_dir, "scripts", "actions.yaml")

        with open(yaml_path, "r", encoding="utf-8") as f:
            action_config = yaml.safe_load(f)["actions"]

        project_name = getattr(self, "current_project_name", "DefaultProject")
        style_folder = getattr(self, "current_style_folder", None)
        label = item.text(0)
        # --- Catégories globales : on ne fait rien ---
        if label in ["Outils en ligne", "Utilitaire python", "Gestion de projets"]:
            print(f"Clique sur un label de catégorie : {label}")
            return

        # --- Vérifie que le label existe ---
        action = action_config.get(label)
        if action is None:
            unknown_data(parent=self.dockwidget)
            return

        # --- Lecture du flag ---
        skip_check = action.get("skip_check", False)

        # --- Vérifications ---
        if not skip_check:

            if not project_name or project_name in [
                "Nom du projet - doit être le même que CARTO FUTAIE ou RSEQUOIA",
                "DefaultProject"
            ]:
                QMessageBox.information(
                    self.dockwidget,
                    "Nom absent",
                    "Merci de renseigner le nom du projet."
                )
                return

            if not style_folder:
                QMessageBox.information(
                    self.dockwidget,
                    "Kartenn",
                    "Pas de dossier de styles sélectionné, veuillez cliquer sur 🔧."
                )
                return

        else:
            # Neutralisation des valeurs manquantes
            project_name = project_name or ""
            style_folder = style_folder or ""

        # --- Appel dynamique ---
        mod_name = action["module"]
        func_name = action["function"]
        print(f"Appel de la fonction {func_name} du module {mod_name}")

        module = importlib.import_module(mod_name)
        func = getattr(module, func_name)

        func(project_name, style_folder, dockwidget=self.dockwidget, iface=self.iface)


        #appel des fonctions R



    def call_R_functions(self, item, column):
        project_name = getattr(self, "current_project_name", "DefaultProject")
        
        if item.text(0) == "📊 Test R":
            run_r_script(project_name, dockwidget=self.dockwidget)
