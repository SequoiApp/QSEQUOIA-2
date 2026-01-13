
from collections import defaultdict
import geopandas as gpd



# Fonction pour City & Owner
def get_grouped_values_from_shapefile(shapefile_path, value_field, filter_field, surface_field):
    # Lecture du shapefile
    gdf = gpd.read_file(shapefile_path)
    
    # Dictionnaire pour regrouper les valeurs
    group_dict = defaultdict(list)
    
    # Si filter_field est None, on va regrouper sous un groupe "No Filter"
    if filter_field is None:
        filter_field = "No Filter"
    
    # Parcours des entités du GeoDataFrame
    for _, row in gdf.iterrows():
        # Si filter_field est "No Filter", on n'utilise pas de champ de filtre
        filter_value = row[filter_field] if filter_field != "No Filter" else "No Filter"
        value = row[value_field]
        surface = row[surface_field]
        
        # Regroupement des valeurs par le champ de filtre (par exemple, DEP_CODE)
        group_dict[filter_value].append((value, surface))
    
    result_list = []
    
    # Pour chaque groupe, on agrège les valeurs par le champ de filtre
    for group, values in group_dict.items():
        # Dictionnaire pour accumuler les valeurs uniques par COM_CODE
        aggregated_values = defaultdict(float)
        
        for value, surface in values:
            aggregated_values[value] += surface
        
        # Trie les valeurs en fonction de la somme des surfaces
        sorted_values = sorted(aggregated_values.items(), key=lambda x: x[1], reverse=True)
        
        value_list = [v[0] for v in sorted_values]
        
        # Construction de la chaîne de caractères avec , et &
        if len(value_list) == 2:
            result_string = f"{value_list[0]} & {value_list[1]}"
        else:
            result_string = f"{', '.join(value_list[:-1])} & {value_list[-1]}" if len(value_list) > 1 else value_list[0]
        
        # Si filter_field était None, on ne veut pas afficher " (No Filter)"
        if filter_field != "No Filter":
            result_list.append(f"{result_string} ({group})")
        else:
            result_list.append(f"{result_string}")
    
    return "; ".join(result_list)
  
# Fonction pour Surface
def sum_surface_from_shapefile(shapefile_path, surface_field, filter_field=None, filter_value=None):
    # Lecture du shapefile
    gdf = gpd.read_file(shapefile_path)
    
    # Si un filter_field et un filter_value sont spécifiés, on filtre les données
    if filter_field and filter_value is not None:
        gdf = gdf[gdf[filter_field] == filter_value]
    
    # Si filter_field est None ou si aucun filtre n'est appliqué, on calcule la somme globale
    if filter_field is None or filter_value is None:
        total_surface = gdf[surface_field].sum()
        return total_surface
    
    # Si filter_field est spécifié mais filter_value est None, on groupe par ce champ
    surface_by_group = gdf.groupby(filter_field)[surface_field].sum()
    
    # Vérifier si filter_value est dans les indices et retourner la somme correspondante
    if filter_value in surface_by_group.index:
        return surface_by_group[filter_value]
    else:
        # Si la valeur n'existe pas dans les indices, retourner None
        return None
  
def get_formated_surface(surface_boisee, surface_non_boisee):
    surface_totale = surface_boisee + surface_non_boisee

    if surface_non_boisee > 0:
        surface_totale_ha = round(surface_totale / 10000, 4)
        surface_boisee_ha = round(surface_boisee / 10000, 4)
        formatted_surface = (
            f"Surface totale: {surface_totale_ha:.4f} ha | Surface boisée: {surface_boisee_ha:.4f} ha"
        )
    else:
        hectares = round(surface_boisee // 10000)
        ares = round((surface_boisee % 10000) // 100)
        centiares = round(surface_boisee % 100)
        formatted_surface = (
            f"Surface totale: {hectares} ha {ares:02} a {centiares:02} ca"
        )

    return formatted_surface
  



