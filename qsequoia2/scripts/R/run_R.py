import subprocess
import os

def run_r_script(project_name, dockwidget=None):
    """
    Appelle le script R en lui passant le nom du projet.
    Affiche les logs dans le dockwidget si fourni.
    """
    # chemin vers le script R
    r_script = os.path.join(os.path.dirname(__file__),"testing_file.R")
    
    # commande R
    cmd = ["Rscript", r_script, project_name]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("R stdout:\n", result.stdout)
        if dockwidget:
            dockwidget.append_log(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Erreur R:\n", e.stderr)
        if dockwidget:
            dockwidget.append_log(f"Erreur R: {e.stderr}")
