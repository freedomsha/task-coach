# Task Coach

Task Coach est une application de bureau libre de gestion de tâches. Elle aide
à organiser des projets complexes comme des listes simples, avec des tâches
imbriquées, des échéances et le suivi du temps passé. L'application peut être
utilisée à son niveau le plus simple ou avec ses fonctions avancées.

## Fonctionnalités

- Organiser les tâches en projets et sous-tâches, avec prérequis et priorités.
- Suivre les dates de début et d'échéance, les rappels et les tâches récurrentes.
- Enregistrer le temps consacré aux tâches.
- Regrouper les tâches avec des catégories et leur associer des notes ou des
  pièces jointes.
- Enregistrer les données dans des fichiers Task Coach (`.tsk`) et importer ou
  exporter des données dans plusieurs formats.

## Prérequis

- Python 3.8 à 3.13.
- Les dépendances Python listées dans `requirements.txt`.
- Un environnement graphique de bureau. L'interface Tkinter est utilisée par
  défaut (en phase de développement); wxPython (de base) est également disponible.

## Installation et lancement

Depuis la racine du dépôt, créez un environnement virtuel et installez les
dépendances :

```bash
python -m venv .venv
```

Activez ensuite l'environnement virtuel :

```bash
# Linux / macOS
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Puis installez les dépendances et lancez l'application :

```bash
python -m pip install -r requirements.txt
python taskcoach/taskcoach.py
```

Pour sélectionner explicitement l'interface Tkinter ou wxPython :

```bash
python taskcoach/taskcoach.py --gui tk
python taskcoach/taskcoach.py --gui wx
```

Consultez les options disponibles avec :

```bash
python taskcoach/taskcoach.py --help
```

## Développement

Le code de l'application se trouve dans `taskcoach/`, notamment dans le paquet
`taskcoach/taskcoachlib/`. Les dépendances de développement et d'exécution sont
déclarées dans `requirements.txt`.

## Licence

Task Coach est distribué sous licence
[GNU GPL version 3 ou ultérieure](https://www.gnu.org/licenses/gpl-3.0.html).
