# la fonction records_orchestrator sert à orchestré les fonctions de classification des points de terrain finalisé
# On commence par vérif si la couche et comme attendu via la fonction check_point_layer

# ALexandre le Bars

# Plugin Kartenn

from qgis.core import QgsVectorLayer, QgsField, QgsFeature, edit,QgsWkbTypes
from qgis.utils import iface
from PyQt5.QtCore import QVariant
from qgis.PyQt.QtWidgets import QMessageBox


from .concat_ESS_pyqgis import build_PLT_ESS
from .concat_TSE_pyqgis import build_PLT_TSE
from .create_PLT_STR_and_density import build_PLT_STR

def check_point_layer(layer):

    # 1) Couche valide ?
    if not layer or not layer.isValid():
        QMessageBox.critical(None, "Erreur", "Pas de couche sélectionnée ou couche invalide.")
        return False

    # 2) Couche de points ?
    if layer.geometryType() != QgsWkbTypes.PointGeometry:
        QMessageBox.critical(None, "Erreur", "La couche n'est pas une couche de points.")
        return False

    # 3) Contient des entités ?
    if layer.featureCount() == 0:
        QMessageBox.critical(None, "Erreur", "La couche est vide (0 entités).")
        return False

    # 4) Champs obligatoires
    required_fields = [
        "id","Essence_1","Essence_2","TSE_ESS2","Taillis_De","Taillis_Ex",
        "Station","Sanitaire","Stade_jeun","T_AMELIO","Qual_ensou","TSE_ESS1",
        "Hdec_gru_1","Essence_3","TSE_ESS3",
        "%_ESS1","Date_Inter","age_T","%_ESS2","Age_PPT","GPB","GBM","GGB",
        "%Ess_tai1","%Ess_tai2","%Ess_tai3","Hdec_gru_2","%_ESS3","%couvert"
    ]

    layer_fields = layer.fields().names()
    missing = [f for f in required_fields if f not in layer_fields]

    if missing:
        msg = "Les champs suivants sont manquants :\n\n" + "\n".join(missing)
        QMessageBox.critical(None, "Champs manquants", msg)
        return False

    return True


def records_orchestrator(project_name, style_folder, *, dockwidget=None, iface=None):

    layer = iface.activeLayer()

    # Vérification
    if not check_point_layer(layer):
        print("Couche invalide, arrêt du processus")
        return

    print("Couche OK, on continue le traitement")

    # 1) PLT_ESS
    print("Records_orchestrator indique ==> build de PLT_ESS")
    build_PLT_ESS(
        layer,
        ess_cols=["Essence_1","Essence_2","Essence_3"],
        pct_cols=["%_ESS1","%_ESS2","%_ESS3"],
        target_col="PLT_ESS_F",
        ess_rep="ESS_REP"
    )

    # 2) PLT_TSE
    print("Records_orchestrator indique ==> build de PLT_TSE")
    build_PLT_TSE(
        layer,
        ess_cols=["TSE_ESS1","TSE_ESS2","TSE_ESS3"],
        pct_cols=["%Ess_tai1","%Ess_tai2","%Ess_tai3"],
        dens_col="Taillis_De",
        exp_col="Taillis_Ex",
        target_col="PLT_TSE_F"
    )

    # 3) PLT_STR
    print("Records_orchestrator indique ==> build de PLT_STR")
    build_PLT_STR(
        layer,
        gtot="GTOT",
        target_col="PLT_STR",
        str_dens="PLT_STR_NH",
        concat_dens="PLT_REP_NH",
        plt_dens="PLT_NHA",
        plt_dm="PLT_DM"
    )

    # 4) Ouvrir la table attributaire
    iface.showAttributeTable(layer)







