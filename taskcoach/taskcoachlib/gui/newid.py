"""
Task Coach - Your friendly task manager
Copyright (C) 2019 Task Coach developers <developers@taskcoach.org>

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

import logging
import wx

log = logging.getLogger(__name__)


# Le problème semble être lié à l'épuisement des identifiants uniques
# pour les éléments d'interface utilisateur dans wxPython.
# L'application utilise des identifiants négatifs générés automatiquement
# et il semble qu'ils soient utilisés au-delà de leurs limites.
class IdProvider(set):
    """
    Fournisseur d'identifiants pour les éléments d'interface utilisateur dans wxPython.

    Cette classe gère les identifiants uniques nécessaires pour les éléments d'interface
    utilisateur, en évitant les conflits et en assurant la disponibilité des identifiants.
    """

    # # ajout conseillé par chatgpt pour mieux gérer les identifiants (3 lignes)
    #
    # Compteur : Utilise un compteur pour générer des IDs positifs uniques.
    #            Le compteur commence à 1 et s'incrémente à chaque appel à get()
    #            si le set est vide.
    # Set pour les IDs : Stocke les IDs qui sont libérés avec put()
    #                    pour une réutilisation ultérieure.
    #
    # Utilisation d'un Dictionnaire pour Suivre les IDs :
    # Explication :
    #     Dictionnaire _ids : Utilise un dictionnaire pour suivre l'état des IDs,
    #     où la clé est l'ID et la valeur est 1 pour utilisé et 0 pour libre.
    #     Compteur : Utilise un compteur pour générer de nouveaux IDs positifs
    #     uniques si aucun ID libre n'est disponible.
    #     Méthode get : Cherche un ID libre dans le dictionnaire et
    #     le marque comme utilisé. Si aucun ID libre n'est trouvé,
    #     génère un nouvel ID et le marque comme utilisé.
    #     Méthode put : Marque un ID comme libre dans le dictionnaire.

    # def __init__(self):
    #     # # # super().__init__()
    #     # # self._ids = set()
    #     # self.ids = {}  # Dictionnaire pour suivre l'état des IDs
    #     # # self.counter = 1  # Commence à 1 pour éviter les IDs négatifs ou zéro

    # def get(self) -> int:
    def get(self):
        """
        Obtenir un nouvel identifiant unique.

        Cette méthode génère un nouvel identifiant unique en utilisant wx.NewIdRef()
        (pas wx.ID_ANY qui génère -1) et
        l'ajoute à l'ensemble des identifiants gérés par cette classe.

        Utilise wx.NewIdRef().GetId() pour générer un nouvel ID unique
        si le set est vide. Sinon, il retire et retourne un ID existant du set.

        Returns :
            (int) : Un nouvel identifiant unique.
        """
        if self:
            return self.pop()
        # # if self._ids:
        # #     return self._ids.pop()
        # # Cherche un ID libre dans le dictionnaire
        # for new_id, status in self._ids.items():
        #     if status == 0:  # Si l'ID est libre
        #         self._ids[new_id] = 1  # Marque l'ID comme utilisé
        #         return new_id

        # # # # return wx.NewId()
        # # # # méthode dépréciée
        # # # # Pour conserver une logique similaire à celle de wx.NewId(),
        # # # # utiliser wx.NewIdRef().GetId() pour générer des IDs uniques :
        # # # return wx.NewIdRef().GetId()
        # #
        # new_id = wx.NewId()
        # # new_id = wx.NewIdRef().GetId()  # Ne fonctionne pas !
        # new_id = wx.NewIdRef()
        new_id = wx.ID_ANY

        # Si aucun ID libre n'est trouvé, génère un nouvel ID
        # new_id = self.counter
        # self.counter += 1

        # # self._ids.add(new_id)
        # # self.add(new_id)
        # self._ids[new_id] = 1  # Marque le nouvel ID comme utilisé
        # log.debug(f"tclib.gui.newid.py IdProvider.get add: new_id = {new_id} for self: {self}")  # Ajout de journalisation
        return new_id
        # # return wx.NewIdRef()
        # return wx.ID_ANY

    # def put(self, id_: int):
    def put(self, id_):
        """
        Libérer un identifiant.

        Cette méthode retire l'identifiant spécifié de l'ensemble des identifiants gérés par
        cette classe, le rendant disponible pour une réutilisation future.

        Ajoute un ID au set s'il est valide (c'est-à-dire s'il est supérieur à 0)

        Args :
            id_ (int) : L'identifiant à libérer.
        """
        # log.info(f"IdProvider.put appelé avec id_={id_}")
        if id_ > 0:
            # if id_ != 0:
            self.add(id_)
            # self.ids.add(id_)
            # log.info(f"IdProvider.put : ajoute {id_} à {self}")
        # # nouveau code :
        # if id_ in self:
        # if id_ in self._ids:
        #     self._ids.remove(id_)
        #     self.remove(id_)
        #     self.ids[id_] = 0  # Marque l'ID comme libre
        #     print(f"tclib.gui.newid.py IdProvider.put remove: id_ = {id_} for self: {self}")  # Ajout de journalisation
        #     # Aucun besoin de faire autre chose, wx gère automatiquement les identifiants.


# Création d'une instance unique de IdProvider pour l'utilisation dans l'application.
IdProvider = IdProvider()
