# password.py pour Tkinter, converti de wxPython
"""
Task Coach - Your friendly task manager
Copyright (C) 2011 Task Coach developers <developers@taskcoach.org>

Task Coach is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Task Coach is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# La conversion de password.py est un peu plus délicate car elle s'appuie sur
# wx.GetPasswordFromUser et keyring, qui n'ont pas d'équivalent direct dans tkinter.
#
# Pour cette conversion, j'ai adapté la logique en utilisant tkinter.simpledialog.askstring
# pour le dialogue de mot de passe et une implémentation simplifiée de cache de mot de passe.
# L'utilisation du module keyring nécessite une installation et une configuration
# supplémentaires, donc je l'ai commentée dans la version Tkinter et j'ai remplacé
# sa logique par un simple dictionnaire en mémoire.

# J'ai converti le fichier password.py pour Tkinter. Les points clés de la conversion sont :
#
#     Remplacement des dialogues wxPython : J'ai utilisé tkinter.simpledialog.askstring pour demander un mot de passe à l'utilisateur, ce qui est l'équivalent le plus proche de wx.GetPasswordFromUser.
#
#     Simplification du stockage : La gestion du keyring (trousseau d'accès) a été commentée, car c'est une dépendance externe non standard. À la place, le code utilise un simple dictionnaire en mémoire pour le cache des mots de passe. C'est une solution plus simple pour cet environnement.
#
#     Logique de cache : La fonction _GetCachedPassword a été réimplémentée pour gérer la logique de réinitialisation et de stockage du mot de passe dans le cache en mémoire.
#
# Le code inclut une section de test qui montre comment les fonctions GetPassword fonctionnent en demandant, en cachant et en réinitialisant un mot de passe.

# TODO : A refaire !
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
from typing import Union, Dict
import os
import sys

# Le module 'keyring' n'est pas standard et nécessite une installation.
# Son utilisation est commentée pour simplifier.
try:
    import keyring
except ImportError:
    keyring = None

# Un cache pour les mots de passe en mémoire
_PASSWORDCACHE = {}


def _GetCachedPassword(domain: str, username: str, reset: bool = False) -> Union[str, None]:
    """
    Simule la logique de wx.GetPasswordFromUser et du cache en mémoire.
    """
    key = (domain, username)
    if reset and key in _PASSWORDCACHE:
        del _PASSWORDCACHE[key]

    if key not in _PASSWORDCACHE:
        # Utiliser simpledialog.askstring pour demander le mot de passe
        pwd = simpledialog.askstring(
            "Entrer le mot de passe",
            f"Veuillez entrer votre mot de passe pour {domain} ({username}).",
            show='*',
        )
        if not pwd:
            return None
        _PASSWORDCACHE[key] = pwd
    return _PASSWORDCACHE[key]


def GetPassword(domain: str, username: str, reset: bool = False) -> Union[str, None]:
    """
    Récupère le mot de passe, en utilisant le cache en mémoire ou en le demandant.
    La logique de keyring est commentée.
    """
    if keyring:
        try:
            if reset:
                keyring.set_password(domain, username, "")
            else:
                pwd = keyring.get_password(domain, username)
                if pwd:
                    return pwd
        except ImportError:
            # Gérer les bugs de secretstorage sur certaines plateformes
            return _GetCachedPassword(domain, username, reset)

    return _GetCachedPassword(domain, username, reset)


# --- Exemple d'utilisation ---
if __name__ == '__main__':
    # Initialiser une application Tkinter
    root = tk.Tk()
    root.withdraw()  # Cache la fenêtre principale

    # Simuler une demande de mot de passe
    domain = "exemple.com"
    username = "utilisateur123"

    print("Demande de mot de passe pour la première fois.")
    pwd1 = GetPassword(domain, username)
    if pwd1:
        print("Mot de passe récupéré (valeur masquée).")
    else:
        print("Mot de passe non fourni.")

    print("\nDeuxième demande de mot de passe (devrait être récupéré du cache).")
    pwd2 = GetPassword(domain, username)
    if pwd2:
        print("Mot de passe récupéré depuis le cache (valeur masquée).")

    print("\nDemande de mot de passe avec réinitialisation du cache.")
    pwd3 = GetPassword(domain, username, reset=True)
    if pwd3:
        print("Nouveau mot de passe récupéré (valeur masquée).")

    # Pour que la fenêtre de dialogue reste ouverte pendant le test
    # Ajoutez un mainloop si nécessaire, mais dans cet exemple, les boîtes de dialogue
    # sont modales et bloquent le programme.

    root.destroy()

