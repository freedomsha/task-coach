"""Task Coach - Your friendly task manager
Copyright (C) 2004-2016 Task Coach developers <developers@taskcoach.org>

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
#  Il est important de noter que KNotify est spécifique aux environnements KDE (Linux),
#  et qu'il interagit avec le système de notification de KDE via pcop et pydcop.
#  Une conversion directe vers Tkinter n'est pas possible
#  car Tkinter ne fournit pas d'interface directe
#  pour interagir avec le système de notification de KDE.
#  La solution suivante propose une alternative en
#  utilisant tkinter.messagebox pour afficher une notification à l'écran,
#  ce qui ne reproduit pas fidèlement la fonctionnalité de KNotify,
#  mais offre une notification visuelle de base.

# Explications de la conversion :
#
# Importation de tkinter et messagebox : On importe les modules nécessaires de Tkinter
#                                        pour créer une boîte de dialogue de message.
# Classe TkinterKNotifyNotifier :
# getName(): Retourne le nom du notifier.
# isAvailable(): Retourne True car Tkinter est généralement disponible.
#                Note : Cela ne vérifie pas si KNotify est réellement disponible.
# notify():
# tkinter.Tk().withdraw(): Crée une instance de Tk et la retire de l'écran.
#                          Ceci est nécessaire pour que messagebox fonctionne
#                          sans afficher une fenêtre Tkinter vide.
# messagebox.showinfo(title, summary): Affiche une boîte de dialogue
#                                      avec le titre et le contenu spécifiés.
#
# AbstractNotifier.register(TkinterKNotifyNotifier()):
# Enregistre le notifier pour qu'il puisse être utilisé par TaskCoach 1.
#
# Prochaines étapes :
#
# Testez le code : Intégrez ce code dans votre projet TaskCoach migré vers Tkinter
#                  et testez si les notifications apparaissent correctement.
# Implémentez les autres notifiers : Convertissez les fichiers notifier_growl.py,
#                                    notifier_windows.py et notifier_universal.py
#                                    de manière similaire,
#                                    en utilisant les fonctionnalités de Tkinter
#                                    pour les notifications (par exemple, messagebox,
#                                    ou des fenêtres personnalisées).
import tkinter
from tkinter import messagebox
from .notifier import AbstractNotifier


class TkinterKNotifyNotifier(AbstractNotifier):
    def __init__(self):
        super().__init__()
        self._available = True  # Tkinter est toujours disponible, mais KNotify peut ne pas l'être réellement.

    def getName(self):
        return "TkinterKNotify"

    def isAvailable(self):
        # Dans un environnement sans KDE, cela retournera toujours True, mais la notification utilisera une messagebox.
        return self._available

    def notify(self, title, summary, bitmap, **kwargs):
        # Affiche une notification Tkinter (messagebox)
        tkinter.Tk().withdraw()  # Masque la fenêtre principale Tkinter
        messagebox.showinfo(title, summary)

AbstractNotifier.register(TkinterKNotifyNotifier())
