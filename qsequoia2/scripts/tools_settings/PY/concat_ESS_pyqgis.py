
#La fonction Build_PLT_ESS : 
#Concatène les colonnes ESS_1, ESS_2, ESS_3 selon leurs pourcentages
#et écrit le résultat dans target_col (PLT_ESS).
#- Si % < 20, l'essence est mise entre parenthèses.
#- Si toutes les essences sont nulles, PLT_ESS reste vide.
# Enfin, la collone ESS_REP est créée avec la répartitions des essences concaténées

#crédit : Alexandre Le Bars

# ! utilisation hors de la console QGIS uniquement possible avec
#Kartenn !

# ! Pour commencer, selectionner votre couche 
# terrain_point dans le panneau de couche,
# puis cliquez sur le petit play vert en haut !



from qgis.core import QgsVectorLayer, QgsField, QgsFeature, edit
from qgis.utils import iface
from PyQt5.QtCore import QVariant

layer = iface.activeLayer()

print("Valide :", layer.isValid())
print("Editable :", layer.isEditable())
print("Provider :", layer.providerType())
print("ReadOnly :", layer.readOnly())

def build_PLT_ESS(layer, ess_cols=["Essence_1","Essence_2","Essence_3"], pct_cols=["%_ESS1","%_ESS2","%_ESS3"], target_col="PLT_ESS_F",ess_rep="ESS_REP"):


    # Vérifier que la colonne cible existe, sinon la créer
    if target_col not in [f.name() for f in layer.fields()]:
        layer.dataProvider().addAttributes([QgsField(target_col, QVariant.String)])
        layer.updateFields()

    layer.startEditing()
    for feat in layer.getFeatures():
        ess_list = []
        for ess_col, pct_col in zip(ess_cols, pct_cols):
            if ess_col in feat.fields().names() and pct_col in feat.fields().names():
                ess = feat[ess_col]
                pct = feat[pct_col]

                if ess is None or str(ess).strip().upper() in ["", "NULL", "NONE"]:
                    continue
                    # Vérifier si pct est une chaîne de chiffres
                if isinstance(pct, str):
                    pct_val = float(pct.replace("%", "").strip())
                elif isinstance(pct, (int, float)):
                    pct_val = float(pct)
                else:
                    pct_val = None

                if pct_val is not None and pct_val < 20:
                    ess_list.append(f"({ess})")
                else:
                    ess_list.append(str(ess))


        # Concaténer uniquement si au moins une essence existe
        if ess_list:
            feat[target_col] = "-".join(ess_list)
        else:
            feat[target_col] = None

        layer.updateFeature(feat)
    layer.commitChanges()

    print(f"Colonne {target_col} mise à jour.")

