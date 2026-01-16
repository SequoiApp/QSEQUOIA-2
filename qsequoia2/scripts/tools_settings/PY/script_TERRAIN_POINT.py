print ("hello world")

#utile : https://pythonds.linogaliana.fr/content/manipulation/04a_webscraping_TP.html


#Objectif de ce script créer la couche Terrain_point, l'intégrer dans Qgis, lui appliquer le style,
#découper un raster de fond puis intégrer tout ca dans un ZIP pret a importer dans Qfield

# ATTENTION : ce script est un script pyqgis, il ne doit en aucun cas être executer avec le venv de KARTENN_main, mais avec le venv qgis !
# sinon ben qgis load failed dans le terminal...


#peut etre à l'avenir utiliser une BDD PG pour le stockage des données KARTENN


# à réadapter, faire un centroide dans chaques UA, si UA >10ha alors appliquer le maillage 1/200m

#programmer un .ui pour le terrain_point voir mon carnet


# V2.1 - Full Pyqgis pour le plugin

#par Alexandre Le Bars
#pour l'APP Kartenn
import os, glob
import shutil
import numpy as np

from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField,
    QgsVectorFileWriter,
    QgsSpatialIndex, QgsFillSymbol
)
from qgis.PyQt.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QPushButton, QMessageBox
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import QgsWkbTypes

def create_terrain(project_name: str, style_folder, dockwidget=None, iface=None):
    print(project_name)
    """
    Crée la structure TERRAIN pour un projet donné, copie les shapefiles,
    génère la grille de points, applique les styles QGIS et sauvegarde le projet.
    Tout en PyQGIS, sans geopandas.
    """
    layer = iface.activeLayer()  # récupère la couche active
    if layer is None:
        print("Aucune couche active sélectionnée")

        msg = QMessageBox(dockwidget)
        msg.setWindowTitle("Kartenn")
        msg.setText("pas de couches actives.")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        return

    # Vérifie que c'est une couche vectorielle sur disque
    if not layer or layer.dataProvider().name().lower() != "ogr":
        raise ValueError("La couche active n'est pas un shapefile/OGR")

    

    # Récupère le chemin complet du fichier
    base = layer.dataProvider().dataSourceUri()
    print("Chemin de la couche UA :", base)

    dossier_projet = os.path.dirname(base)
    print (dossier_projet)
    nom_projet = project_name

    if not nom_projet or not dossier_projet :

        raise ValueError("Nom du projet et chemin du projet doivent être fournis.")


    # 1️ Création du dossier TERRAIN
    chemin_complet = os.path.join(dossier_projet, f"{nom_projet}_TERRAIN")
    os.makedirs(chemin_complet, exist_ok=True)
    print(f"Création du dossier TERRAIN : {chemin_complet}")

    structure = {"1 RASTER": {}, "2 VECTEUR": {}}
    def creer_dossiers(base_path, structure):
        for dossier, sous_dossiers in structure.items():
            chemin_dossier = os.path.join(base_path, dossier)
            os.makedirs(chemin_dossier, exist_ok=True)
            print(f"Dossier créé : {chemin_dossier}")
            if isinstance(sous_dossiers, dict) and sous_dossiers:
                creer_dossiers(chemin_dossier, sous_dossiers)
    creer_dossiers(chemin_complet, structure)

    # 2️ Copier le template QGIS
    template_path = os.path.join(os.path.dirname(__file__), "../../../data/template/TERRAIN.qgz")
    dest_template = os.path.join(chemin_complet, f"{nom_projet}_TERRAIN.qgz")
    shutil.copyfile(template_path, dest_template)
    print(f"Template copié : {dest_template}")

    # 3️ Copier UA (si les noms de projet correspondent)

    dest = os.path.join(chemin_complet, "2 VECTEUR")
    os.makedirs(dest, exist_ok=True)

    ext = [".shp", ".dbf", ".prj", ".shx"]

    for e in ext:
        src = os.path.join(dossier_projet, f"{nom_projet}_UA_polygon{e}")
        print(src)
        dst = os.path.join(dest, f"{nom_projet}_UA_polygon{e}")

        # si un fichier manque → noms de projets différents
        if not os.path.exists(src):
            msg = QMessageBox(dockwidget)
            msg.setWindowTitle("Kartenn")
            msg.setText(
                "Les projets n'ont pas le même nom.\n"
                "Impossible de trouver la couche UA correspondante."
            )
            msg.setIcon(QMessageBox.Information)
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return

        shutil.copy(src, dst)

    print("UA copiée avec succès.")



    # 4️ Charger UA
    ua_path = os.path.join(dest, f"{nom_projet}_UA_polygon.shp" or f"{nom_projet}_UA_polygon.gpkg")
    ua_layer = QgsVectorLayer(ua_path, "UA", "ogr")
    if not ua_layer.isValid():
        raise FileNotFoundError(f"Couche UA invalide : {ua_path}")


    # 5️ Demande de l'espacement via PyQt (MODAL)
    spacing = None

    dialog = QDialog(dockwidget)
    dialog.setWindowTitle("Choisir l'espacement des points")
    dialog.setFixedSize(300, 150)

    layout = QVBoxLayout(dialog)

    combo = QComboBox(dialog)
    combo.addItems([str(i) for i in [50, 100, 150, 200, 250, 300, 400, 500]])
    combo.setCurrentIndex(0)
    layout.addWidget(combo)

    btn = QPushButton("Confirmer", dialog)
    layout.addWidget(btn)

    def confirmer():
        nonlocal spacing
        spacing = int(combo.currentText())
        dialog.accept()

    btn.clicked.connect(confirmer)

    # exécution BLOQUANTE
    if dialog.exec_() != QDialog.Accepted or spacing is None:
        QMessageBox.information(
            dockwidget,
            "Kartenn",
            "Aucun espacement sélectionné. Opération annulée."
        )
        return

    print(f"Espacement choisi : {spacing}")

    # 6️ Génération de la grille de points
    bounds = ua_layer.extent()
    xmin, ymin, xmax, ymax = bounds.xMinimum(), bounds.yMinimum(), bounds.xMaximum(), bounds.yMaximum()

    points_layer = QgsVectorLayer(f"Point?crs={ua_layer.crs().authid()}", f"{nom_projet}_TERRAIN_point", "memory")
    pr = points_layer.dataProvider()
    pr.addAttributes([QgsField("id", QVariant.Int)] + [QgsField(c, QVariant.String) for c in [
        "Essence_1","Essence_2","Type","Qualité","TSE_ESS2","Taillis_De","Taillis_Ex",
        "Station","Sanitaire","Stade_jeun","statut","Interventi","T_AMELIO","Qual_ensou","TSE_ESS1",
        "Hdec_gru_1","Essence_3","TSE_ESS3","observ","rege_tac"
    ]] + [QgsField(c, QVariant.Int) for c in [
        "%_ESS1","Date_Inter","age_T","%_ESS2","Age_PPT","GPB","GBM","GGB",
        "%Ess_tai1","%Ess_tai2","%Ess_tai3","Hdec_gru_2","%_ESS3","%couvert"
    ]])
    points_layer.updateFields()

    fid = 1
    index_ua = QgsSpatialIndex(ua_layer.getFeatures())
    for x in np.arange(xmin, xmax+spacing, spacing):
        for y in np.arange(ymin, ymax+spacing, spacing):
            point_geom = QgsGeometry.fromPointXY(QgsPointXY(x, y))
            # récupère les ids des polygones potentiellement concernés
            candidate_ids = index_ua.intersects(point_geom.boundingBox())
            # vérifie réellement si le point est dans un polygone
            inside = False
            for fid_candidate in candidate_ids:
                poly_feat = ua_layer.getFeature(fid_candidate)
                if poly_feat.geometry().contains(point_geom):
                    inside = True
                    break
            if inside:
                feat = QgsFeature(points_layer.fields())
                feat.setGeometry(point_geom)
                feat.setAttribute("id", fid)
                fid += 1
                pr.addFeature(feat)


    points_layer.updateExtents()
    print(f"{fid-1} points générés dans TERRAIN_point")


    # 7️ Sauvegarde GPKG
    points_gpkg_path = os.path.join(chemin_complet, "2 VECTEUR", f"{nom_projet}_TERRAIN_point.gpkg")
    QgsVectorFileWriter.writeAsVectorFormat(points_layer, points_gpkg_path, "UTF-8", points_layer.crs(), "GPKG")
    print("GPKG TERRAIN_point créé :", points_gpkg_path)

    # 8️ Ajout au projet QGIS et application des styles
    project = QgsProject.instance()


    # Nouveau projet pour TERRAIN
    project = QgsProject()
    
    # ------------------
    # Ajouter la couche UA
    # ------------------
    ua_layer = QgsVectorLayer(ua_path, "UA", "ogr")
    if not ua_layer.isValid():
        print(f"Erreur : UA invalide : {ua_path}")
    else:
        # Si pas de style QML, appliquer un style par défaut


        if ua_layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            symbol = QgsFillSymbol.createSimple({
                'color': '0,255,0,0',  # vert clair semi-transparent
                'outline_color': '0,100,0',  # contour vert foncé
                'outline_width': '0.2'
            })
            ua_layer.renderer().setSymbol(symbol)

            project.addMapLayer(ua_layer)
            print("Couche UA ajoutée au projet TERRAIN")

    #------------------------
    # TERRAIN_point layer
    #------------------------

    terrain_layer = QgsVectorLayer(points_gpkg_path, "TERRAIN_point", "ogr")
    if not terrain_layer.isValid():
        print(f"Erreur : TERRAIN_point invalide : {points_gpkg_path}")
    else:
        # recherche d'un QML contenant 'terrain' insensible à la casse
        terrain_style_path = None
        if style_folder and os.path.isdir(style_folder):
            for f in os.listdir(style_folder):
                if f.lower().endswith(".qml") and "terrain" in f.lower():
                    terrain_style_path = os.path.join(style_folder, f)
                    break

        if terrain_style_path:
            terrain_layer.loadNamedStyle(terrain_style_path)
            print(f"Style appliqué : {terrain_style_path}")
        else:
            print("Aucun QML contenant 'terrain' trouvé. Style par défaut appliqué.")

        project.addMapLayer(terrain_layer)

    # 9️ Champ "statut"
    if "statut" in [f.name() for f in terrain_layer.fields()]:
        terrain_layer.startEditing()
        for f in terrain_layer.getFeatures():
            f["statut"] = "Non-terminée"
            terrain_layer.updateFeature(f)
        terrain_layer.commitChanges()
        print("Champ 'statut' mis à jour")

    # ------------------
    # Sauvegarder le projet
    # ------------------
    project_path = os.path.join(chemin_complet, f"{nom_projet}_TERRAIN.qgz")
    project.write(project_path)
    os.startfile(chemin_complet)
    print(f"Projet TERRAIN sauvegardé : {project_path}")
    return project_path


