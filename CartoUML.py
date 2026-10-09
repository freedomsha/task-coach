import os
import ast
from pathlib import Path

# Répertoire racine du projet (ajuste si nécessaire)
ROOT = Path("taskcoach")

def get_imports_from_file(filepath):
    """Parse un fichier Python et retourne la liste des imports (module/package)."""
    imports = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            node = ast.parse(f.read(), filepath)
            for n in ast.walk(node):
                if isinstance(n, ast.Import):
                    for alias in n.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(n, ast.ImportFrom):
                    if n.module:
                        imports.append(n.module.split('.')[0])
    except Exception as e:
        print(f"Erreur parsing {filepath}: {e}")
    return imports

# Construire les dépendances
dependencies = {}
for pyfile in ROOT.rglob("*.py"):
    rel = pyfile.relative_to(ROOT)
    module = str(rel).replace("/", ".").replace("\\", ".")[:-3]  # enlever ".py"
    dependencies[module] = get_imports_from_file(pyfile)

# Écriture en format PlantUML
with open("dependencies.puml", "w", encoding="utf-8") as f:
    f.write("@startuml\n")
    f.write("skinparam rankdir LR\n")
    for mod, deps in dependencies.items():
        for dep in deps:
            if dep in dependencies:  # on ne trace que si c'est interne au projet
                f.write(f"\"{mod}\" --> \"{dep}\"\n")
    f.write("@enduml\n")

print("Fichier dependencies.puml généré. Utilise PlantUML pour visualiser.")
