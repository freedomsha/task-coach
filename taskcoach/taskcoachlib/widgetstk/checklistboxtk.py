"""
Task Coach - Your friendly task manager
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
# Ce code crée une classe CheckListBox pour Tkinter en utilisant une ttk.Treeview pour simuler le comportement d'une liste avec des cases à cocher. Il gère également l'association de données client à chaque élément de la liste, ce qui n'est pas une fonctionnalité native de Tkinter.

# Cette version en Python pour Tkinter est fonctionnellement similaire à l'originale pour wxPython, tout en utilisant les widgets et les méthodes appropriés pour Tkinter. Si vous avez d'autres widgets à convertir, faites-le moi savoir.

import logging
import tkinter as tk
from tkinter import ttk
from tkinter import Toplevel
from collections import OrderedDict

log = logging.getLogger(__name__)


class CheckListBox(ttk.Treeview):
    """
    Une implémentation de CheckListBox pour Tkinter, basée sur ttk.Treeview,
    qui permet d'associer des données client à chaque élément, une fonctionnalité
    non supportée nativement par la plupart des widgets de liste de Tkinter.
    """

    def __init__(self, master=None, **kwargs):
        """
        Initialise la CheckListBox.

        :param master: Le widget parent.
        :param kwargs: Arguments additionnels pour ttk.Treeview.
        """
        # Appeler le constructeur de la classe parente (ttk.Treeview)
        # On définit les colonnes : la première pour la case à cocher, la seconde pour le texte de l'élément.
        super().__init__(master, columns='item', **kwargs)

        self.heading("#0", text="")  # Entête de la première colonne (vide)(case à cocher)
        self.heading("item", text="Items")
        self.column("#0", width=30)
        self.column("item", width=300)

        # Dictionnaire pour stocker les données client, associées aux identifiants (IID)
        # de la Treeview.
        self.__clientData = OrderedDict()

        # Un dictionnaire pour stocker l'état (coché/décoché) de chaque élément.
        self.__checked_items = {}

        # Gérer les clics pour basculer l'état de la case à cocher
        self.bind("<Button-1>", self.on_item_click)

    def Append(self, item, clientData=None):
        """
        Ajoute un nouvel élément à la liste.

        :param item: Le texte de l'élément à ajouter.
        :param clientData: (optionnel) Les données client à associer à cet élément.
        :return: L'identifiant (IID) de l'élément inséré.
        """
        # Insérer l'élément dans la Treeview
        index = self.insert("", "end", text="☐", values=(item,))

        # Stocker les données client en utilisant l'IID comme clé
        if clientData is not None:
            self.__clientData[index] = clientData

        # Initialiser l'état non coché
        self.__checked_items[index] = False

        return index

    def Insert(self, item, position, clientData=None):
        """
        Insère un élément à une position spécifique.
        (Non implémenté, car la version wxPython de référence le lève aussi)
        """
        raise NotImplementedError("Insert is not needed at the moment.")

    def Delete(self, iid=None):
        """
        Supprime un élément de la liste en utilisant son IID.

        :param iid: L'identifiant de l'élément à supprimer.
        """
        if iid:
            # Supprimer l'élément de la Treeview
            self.delete(iid)

            # Supprimer les données associées
            if iid in self.__clientData:
                del self.__clientData[iid]
            if iid in self.__checked_items:
                del self.__checked_items[iid]
        else:
            # Si aucun IID n'est fourni, supprimer tous les éléments
            for item in self.get_children():
                self.Delete(item)

    def GetClientData(self, iid):
        """
        Récupère les données client associées à un élément.

        :param iid: L'identifiant de l'élément.
        :return: Les données client, ou None si aucune n'est trouvée.
        """
        return self.__clientData.get(iid)
        # return self.__clientData.get(iid) if index in self.__clientData else None

    def Clear(self):
        """
        Vide complètement la liste.
        """
        self.Delete()

    def on_item_click(self, event):
        """
        Gestionnaire d'événement de clic pour basculer l'état de la case à cocher.
        """
        # Identifier l'élément cliqué
        iid = self.identify_row(event.y)
        if not iid:
            return

        # Basculer l'état
        if self.__checked_items.get(iid) is not None:
            self.__checked_items[iid] = not self.__checked_items[iid]

            # Mettre à jour le texte de la case à cocher dans la Treeview
            if self.__checked_items[iid]:
                self.item(iid, text="☑")  # Caractère Unicode pour une case cochée
            else:
                self.item(iid, text="☐")  # Caractère Unicode pour une case vide

    def GetItemCount(self):
        """
        Retourne le nombre d'éléments dans la liste.
        """
        return len(self.get_children())

    def IsChecked(self, iid):
        """
        Vérifie si un élément est coché.

        :param iid: L'identifiant de l'élément.
        :return: True si l'élément est coché, False sinon.
        """
        return self.__checked_items.get(iid, False)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test CheckListBox Tkinter")

    def on_delete():
        selected_item = clb.selection()
        if selected_item:
            clb.Delete(selected_item[0])

    def on_clear():
        clb.Clear()

    def print_data():
        for iid in clb.get_children():
            text = clb.item(iid, 'values')[0]
            data = clb.GetClientData(iid)
            is_checked = clb.IsChecked(iid)
            print(f"Item: '{text}', Checked: {is_checked}, Client Data: {data}")

    frame = ttk.Frame(root, padding="10")
    # frame.pack(fill=tk.BOTH, expand=True)
    frame.pack(fill="both", expand=True)

    clb = CheckListBox(frame, height=10)
    # clb.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    clb.pack(fill="both", expand=True, padx=5, pady=5)

    # Ajouter des éléments avec et sans données client
    clb.Append("Tâche 1: Migrer TaskCoach", clientData={"id": 1, "status": "en cours"})
    clb.Append("Tâche 2: Apprendre Tkinter", clientData={"id": 2, "status": "terminé"})
    clb.Append("Tâche 3: Vérifier le code")
    clb.Append("Tâche 4: Finir le projet")

    button_frame = ttk.Frame(frame)
    # button_frame.pack(fill=tk.X, padx=5, pady=5)
    button_frame.pack(fill="x", padx=5, pady=5)

    delete_btn = ttk.Button(button_frame, text="Supprimer sélection", command=on_delete)
    # delete_btn.pack(side=tk.LEFT, padx=5)
    delete_btn.pack(side="left", padx=5)

    clear_btn = ttk.Button(button_frame, text="Tout effacer", command=on_clear)
    # clear_btn.pack(side=tk.LEFT, padx=5)
    clear_btn.pack(side="left", padx=5)

    print_btn = ttk.Button(button_frame, text="Afficher les données", command=print_data)
    # print_btn.pack(side=tk.LEFT, padx=5)
    print_btn.pack(side="left", padx=5)

    root.mainloop()
