# La fonction TP_to_XLSX esport la table attributaire de la couche séléctionné en excel, fait la somme des champs de types INT et float


from qgis.core import QgsVectorLayer, QgsProject, QgsFields, QgsFeature, QgsWkbTypes
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsVectorFileWriter

def TP_to_XLSX(layer, output_path):
    if not layer or not layer.isValid():
        print("Couche invalide")
        return False

    fields = layer.fields()
    field_names = [f.name() for f in fields]

    # Détection des champs numériques
    numeric_fields = []
    for f in fields:
        if f.type() in (QVariant.Int, QVariant.Double, QVariant.LongLong):
            numeric_fields.append(f.name())

    print("Champs numériques :", numeric_fields)

    # Calcul des totaux
    totals = {name: 0 for name in numeric_fields}

    for feat in layer.getFeatures():
        for name in numeric_fields:
            val = feat[name]
            if isinstance(val, (int, float)):
                totals[name] += val

    # Création d’une couche mémoire pour l’export
    mem_layer = QgsVectorLayer("None", "export", "memory")
    mem_provider = mem_layer.dataProvider()

    # Ajouter les champs
    mem_provider.addAttributes(fields)
    mem_layer.updateFields()

    # Copier les entités
    mem_provider.addFeatures(list(layer.getFeatures()))

    # Ajouter la ligne TOTAL
    total_feat = QgsFeature(mem_layer.fields())
    for name in field_names:
        if name in numeric_fields:
            total_feat[name] = totals[name]
        else:
            total_feat[name] = "TOTAL"

    mem_provider.addFeature(total_feat)

    # Export Excel via QGIS
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.driverName = "xlsx"

    result = QgsVectorFileWriter.writeAsVectorFormatV2(
        mem_layer,
        output_path,
        QgsProject.instance().transformContext(),
        options
    )

    if result[0] != QgsVectorFileWriter.NoError:
        print("Erreur export :", result)
        return False

    print("Export Excel terminé :", output_path)
    return True