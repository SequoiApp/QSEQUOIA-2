from PyQt5.QtWidgets import QDialog
from .add_data_dialog import Ui_AddDataDialog
from itertools import chain

# Import from utils folder
from ...utils.layers import *

class AddDataDialog(QDialog):
    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.ui = Ui_AddDataDialog()
        self.ui.setupUi(self)

        self.SEQUOIA_CHECKBOX_KEY_MAP = {
            self.ui.cb_vector_parca: ['parca_polygon'],
            self.ui.cb_vector_ua: ['ua_polygon', 'ua_polygon_plt', 'ua_polygon_occup', 'ua_polygon_ame'],
            self.ui.cb_vector_sspf: ['sspf_polygon', 'sspf_polygon_plt'],
            self.ui.cb_vector_pf: ['pf_polygon', 'pf_line']
        }

        self.VECTOR_CHECKBOX_KEY_MAP = {
            self.ui.cb_vector_route: ['route_polygon', 'route_line'],
            self.ui.cb_vector_topo: ['topo_line'],
        }

        self.RASTER_CHECKBOX_KEY_MAP = {
            self.ui.cb_raster_plt: "plt",
            self.ui.cb_raster_plt_anc: "plt_anc",
            self.ui.cb_raster_irc: "irc",
            self.ui.cb_raster_rgb: "rgb",
            self.ui.cb_raster_mnh: "mnh",
            self.ui.cb_raster_mnt: "mnt",
            self.ui.cb_raster_scan25: "scan25",
        }

        self.WMTS_CHECKBOX_KEY_MAP = {
            # SCAN
            self.ui.cb_wmts_scan100: "wmts_scan1000",
            self.ui.cb_wmts_scan1000: "wmts_scan100",
            self.ui.cb_wmts_scan25: "wmts_scan25",
            self.ui.cb_wmts_scan25_grey: "wmts_scan25_grey",
            # ORTHO
            self.ui.cb_wmts_irc: "wmts_irc",
            self.ui.cb_wmts_rgb: "wmts_rgb",
            self.ui.cb_wmts_spot_2023: "wmts_spot_2023",
            # LIDAR
            self.ui.cb_wmts_lidar_mnt: "wmts_lidar_mnt",
            self.ui.cb_wmts_lidar_mnh: "wmts_lidar_mnh",
            # ORTHOHISTO
            self.ui.cb_wmts_histo_1950: "wmts_histo_1950",
            self.ui.cb_wmts_histo_1965: "wmts_histo_1965",
            self.ui.cb_wmts_histo_1980: "wmts_histo_1980",
            self.ui.cb_wmts_histo_2000: "wmts_histo_2000", 
            self.ui.cb_wmts_histo_2006: "wmts_histo_2006",
            self.ui.cb_wmts_histo_2011: "wmts_histo_2011",
            # AUTRES
            self.ui.cb_wmts_geol: "wmts_geol",
            self.ui.cb_wmts_pci: "wmts_pci",
        }
        
        self.TERRAIN_CHECKBOX_KEY_MAP = {
            self.ui.cb_terrain_expertise: "expertise_gpkg",
            self.ui.cb_terrain_inventaire: "inventaire",
            self.ui.cb_terrain_diag: "diag",
        }

        self._all_checkbox_maps = (
            self.SEQUOIA_CHECKBOX_KEY_MAP,
            self.VECTOR_CHECKBOX_KEY_MAP,
            self.RASTER_CHECKBOX_KEY_MAP,
            self.WMTS_CHECKBOX_KEY_MAP,
            self.TERRAIN_CHECKBOX_KEY_MAP,
        )
    
    def _reset_checkboxes(self):
        """Uncheck every checkbox in all our maps."""
        for chk in chain.from_iterable(m.keys() for m in self._all_checkbox_maps):
            chk.setChecked(False)
    
    def _add_sequoia(self):
        # flatten list of list
        sequoia_keys = [
            key
            for cb, key_list in self.SEQUOIA_CHECKBOX_KEY_MAP.items() if cb.isChecked()
            for key in key_list
        ]
        if sequoia_keys:
            load_vectors(*sequoia_keys, group_name="SEQUOIA")

    def _add_vector(self):
        # flatten list of list
        vector_keys = [
            key
            for cb, key_list in self.VECTOR_CHECKBOX_KEY_MAP.items() if cb.isChecked()
            for key in key_list
        ]
        if vector_keys:
            load_vectors(*vector_keys, group_name="VECTEUR")

    def _add_raster(self):
        raster_keys = [key for cb, key in self.RASTER_CHECKBOX_KEY_MAP.items() if cb.isChecked()]

        # Handle PLT_ANC separately
        if "plt_anc" in raster_keys:
            folder = get_path("raster_folder")
            plt_anc_rasters = [p for p in folder.glob("*.tif") if "PLT_ANC" in p.name.upper()]

            if len(plt_anc_rasters) > 1:
                root = QgsProject.instance().layerTreeRoot()
                group = root.findGroup("RASTER") or root.addGroup("RASTER")

                for path in plt_anc_rasters:
                    layer = QgsRasterLayer(str(path), path.stem)
                    if layer.isValid():
                        QgsProject.instance().addMapLayer(layer, False)
                        group.addLayer(layer)

                # Remove plt_anc from keys so load_rasters doesn't load it again
                raster_keys.remove("plt_anc")

        # Load other rasters normally
        if raster_keys:
            load_rasters(*raster_keys, group_name="RASTER")

    def _add_wms(self):
        # flatten list of list
        wmts_keys = [key for cb, key in self.WMTS_CHECKBOX_KEY_MAP.items() if cb.isChecked()]
        if wmts_keys:
            load_wmts(*wmts_keys, group_name="WMTS")

    def _add_terrain(self):
        # flatten list of list
        gpkg_keys = [key for cb, key in self.TERRAIN_CHECKBOX_KEY_MAP.items() if cb.isChecked()]
        if gpkg_keys:
            [load_gpkg(get_path(key), group_name="TERRAIN") for key in gpkg_keys]

    def accept(self):

        self._add_sequoia()
        self._add_vector()
        self._add_raster()
        self._add_wms()
        self._add_terrain()
        
        self._reset_checkboxes()

        super().accept()