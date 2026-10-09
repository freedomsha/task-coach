# Task Coach

Task Coach est une application de bureau libre de gestion de tâches. Elle aide à organiser des projets complexes comme des listes simples, avec des tâches imbriquées, des échéances et le suivi du temps passé. L'application peut être utilisée à son niveau le plus simple ou avec ses fonctionnalités avancées.

Ce fork met en œuvre des améliorations et des corrections ciblées sur l'interface Tkinter, la gestion des vues et le rafraîchissement des listes de tâches, dans le cadre d'un effort de développement actif sur le projet.

## État du projet

Le projet est actuellement en développement actif, avec un focus particulier sur :

- la stabilisation de l'interface Tkinter,
- la correction des problèmes de rafraîchissement de l'arborescence des tâches,
- la gestion plus fiable des commandes UI et des menus dynamiques,
- l'amélioration de la lisibilité et de la maintenance du code.

Les derniers changements incluent des correctifs sur la création et la mise à jour des widgets de visualisation, la gestion des catégories, ainsi que l'amélioration de la logique de rendu et d'insertion des tâches.

## Fonctionnalités

- Organiser les tâches en projets et sous-tâches, avec prérequis et priorités.
- Suivre les dates de début et d'échéance, les rappels et les tâches récurrentes.
- Enregistrer le temps consacré aux tâches.
- Regrouper les tâches avec des catégories et leur associer des notes ou des pièces jointes.
- Enregistrer les données dans des fichiers Task Coach (`.tsk`) et importer ou exporter des données dans plusieurs formats.

## Prérequis

- Python 3.8 à 3.13.
- Les dépendances Python listées dans `requirements.txt`.
- Un environnement graphique de bureau.
- L'interface Tkinter est actuellement en cours de développement actif ; l'interface wxPython reste également disponible.

## Installation et lancement

Depuis la racine du dépôt, créez un environnement virtuel et installez les dépendances :

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

## Développement en cours

Le dépôt contient actuellement un travail de refactorisation et de correction sur plusieurs composants centraux :

- `taskcoach/taskcoachlib/guitk/` : interfaces Tkinter, menus, vues et widgets de rendu,
- `taskcoach/taskcoachlib/domain/` : modèle de données des tâches et catégories,
- `taskcoach/taskcoachlib/widgetstk/` : composants d'affichage des listes et arbres,
- `taskcoach/taskcoachlib/patterns/` : mécanismes d'observation et de mise à jour.

Les thèmes principaux du développement actuel sont :

- correction des boucles de mise à jour dans les arbres de tâches,
- nettoyage des variables et simplification du flux de création de widgets,
- amélioration de la robustesse des menus contextuels et des commandes UI,
- révision des mécanismes de rafraîchissement entre les modèles et les vues.

## Structure du dépôt

```text
.
├── README.md
├── requirements.txt
├── taskcoach/
│   ├── taskcoach.py
│   └── taskcoachlib/
├── tests/
├── taskcoach-iphone/
├── taskcoach-iphone-refactoring/
└── ...
```

## Tests et validation

Le dépôt inclut des scripts et des tests de validation. Pour lancer un test ciblé, vous pouvez utiliser les outils déjà présents dans le projet :

```bash
python run_single_test.py
```

Pour un usage plus avancé, vérifiez les scripts de test et les fichiers associés dans le dossier `tests/`.

## Contribution

Les contributions sont bienvenues. Avant de proposer des modifications :

1. créez une branche dédiée,
2. gardez les changements ciblés et explicites,
3. testez les chemins concernés par votre modification,
4. documentez les changements importants dans le code ou dans le README si nécessaire.

## Développement

Le code de l'application se trouve dans `taskcoach/`, notamment dans le paquet `taskcoach/taskcoachlib/`. Les dépendances de développement et d'exécution sont déclarées dans `requirements.txt`.

## Licence

Task Coach est distribué sous licence [GNU GPL version 3 ou ultérieure](https://www.gnu.org/licenses/gpl-3.0.html).
