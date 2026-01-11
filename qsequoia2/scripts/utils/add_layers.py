# la fonction add_layer récupère les couches ajoutées dans le dossier temporaire, 
# recherche les styles dans le dossier de style, les appliques, et ajoute les couches au projet courant



from qgis.core import QgsVectorLayer, QgsProject
import os

def add_layers(project_name, temp_folder, style_folder, project_folder):

    # Liste des types de couches : 
    ext = [".shp",".gpkg",".geojson"]

    # Liste des styles disponibles
    style_files = [f for f in os.listdir(temp_folder) if f.lower().endswith(".qml")]

    for layer_file in os.listdir(project_folder):

        _, extension = os.path.splitext(layer_file.lower())
        if extension not in ext:
            print(f"Ignoré (extension non autorisée) : {layer_file}")
            continue

        layer_path = os.path.join(temp_folder, layer_file)
        layer = QgsVectorLayer(layer_path, layer_file, "ogr")
        if not layer.isValid():
            print(f"\nadd_layers indique => couche invalide == {layer_file}")
            continue

        # Chercher un style correspondant

        applied = False
        for style_file in style_files:
            style_name = os.path.splitext(style_file)[0].lower()

            if style_name in layer_file.lower():
                style_path = os.path.join(style_folder, style_file)
                layer.loadNamedStyle(style_path)
                layer.triggerRepaint()
                applied = True
                break

        # Ajouter la couche (avec ou sans style)

        QgsProject.instance().addMapLayer(layer)
        print(f"add_layers indique => \n Couche ajouté == {layer}")







      


   # lecture des couches


   # recherche des styles avec le nom

   # application des styles et ajout des couches