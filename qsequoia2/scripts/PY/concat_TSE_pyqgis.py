
#La fonction Build_PLT_TSE : 
#Concatène les colonnes TSE_ESS_1, TSE_ESS_2, TSE_ESS_3 et prend la dominante selon le %
#et écrit le résultat dans target_col (PLT_STR).
#- Si toutes les essences sont nulles, PLT_STR reste vide.

#crédit : Alexandre Le Bars

# ! utilisation hors de la console QGIS uniquement possible avec
#Kartenn !

# ! Pour commencer, selectionner votre couche 
# terrain_point dans le panneau de couche,
# # puis cliquez sur le petit play vert en haut !




from qgis.core import QgsField, edit
from qgis.utils import iface
from PyQt5.QtCore import QVariant


layer = iface.activeLayer()

print("Valide :", layer.isValid())
print("Editable :", layer.isEditable())
print("Provider :", layer.providerType())
print("ReadOnly :", layer.readOnly())

def build_PLT_TSE(layer, ess_cols=["TSE_ESS1","TSE_ESS2","TSE_ESS3"], pct_cols=["%Ess_tai1","%Ess_tai2","%Ess_tai3"],
                  dens_col="Taillis_De", exp_col="Taillis_Ex", target_col="PLT_TSE_F"):



    # Vérifier que la colonne cible existe, sinon la créer
    if target_col not in [f.name() for f in layer.fields()]:
        layer.dataProvider().addAttributes([QgsField(target_col, QVariant.String)])
        layer.updateFields()

    
    layer.startEditing()
    for feat in layer.getFeatures():
        dominant = None
        max_pct = -1

        for ess_col, pct_col in zip(ess_cols, pct_cols):
            if ess_col in feat.fields().names() and pct_col in feat.fields().names():
                ess = feat[ess_col]
                pct = feat[pct_col]

                if ess is None or str(ess).strip().upper() in ["", "NULL", "NONE"]:
                    continue

                # Conversion pct_val en int + comparaisont
                pct_val = str(pct).replace("%", "").strip().isdigit()
                if pct_val is not None and pct_val >max_pct :
                    dominant = str(ess)

        #récupération densité et exploitabilité
        dens = str(feat[dens_col]) if feat[dens_col] is not None else ""
        expl = str(feat[exp_col]) if feat[exp_col] is not None else ""

        if dens == "pd":
            densi = "3"
        elif dens == "md":
            densi = "2"
        elif dens == "d":
            densi = "1"
        else : densi =""
        
        if expl == "ne":
            exploi = "c"
        elif expl =="ie":
            exploi = "b"
        elif expl == "e":
            exploi = "a"
        else : exploi = ""

        if dominant : feat[target_col] =f"{dominant}-T{densi}{exploi}"
        else : feat [target_col] = None

        layer.updateFeature(feat)

    layer.commitChanges()

    print(f"Colonne {target_col} mise à jour.")
    

