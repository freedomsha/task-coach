"""
Task Coach - Your friendly task manager
Copyright (C) 2012 Task Coach developers <developers@taskcoach.org>

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

# Notre but est de créer la classe BalloonTipManager dans Tkinter, qui gérera l'affichage des info-bulles selon les paramètres de l'application, tout comme la version wxPython.
#
# Aperçu de la conversion de balloontips.py
#
# Le fichier original balloontips.py définit une classe BalloonTipManager qui hérite d'une classe de base et surcharge la méthode AddBalloonTip pour vérifier si l'info-bulle doit être affichée (en fonction des réglages de l'utilisateur) avant de l'ajouter. Il gère également l'événement de fermeture de la bulle (OnBalloonTipShow) pour mettre à jour ces réglages.
#
# Pour la version Tkinter, nous allons :
#
#     Hériter de la classe de base BalloonTipManager que tu as dans taskcoachlib.widgets.balloontip (que nous supposerons adaptée pour Tkinter).
#
#     Importer la classe BalloonTip depuis notre nouveau fichier balloontiptk.py.
#
#     Implémenter AddBalloonTip pour utiliser la classe BalloonTip (ou sa logique via super().AddBalloonTip) tout en gérant les paramètres (settings).

# Explication et implémentation
#
# 1. Structure du code
#
# Le fichier balloontips_tk.py contient une seule classe, BalloonTipManager, qui hérite de balloontip.BalloonTipManager.
#
# 2. La méthode AddBalloonTip
#
#     Vérification des réglages : La ligne if settings.getboolean("balloontips", name): est essentielle. Elle récupère le réglage pour cette info-bulle spécifique (name) dans la section "balloontips". Si le réglage est True, l'info-bulle est autorisée à s'afficher.
#
#     Appel du parent : super().AddBalloonTip(...) appelle la méthode correspondante dans la classe de base (balloontip.BalloonTipManager). Dans un environnement Task Coach bien migré, cette méthode parente sera celle qui crée et affiche réellement l'info-bulle, en utilisant notre classe BalloonTip de balloontiptk.py.
#
#     Icône (bitmap) : Dans l'original, l'icône était récupérée via wx.ArtProvider.GetBitmap("lamp_icon", ...). Dans cette conversion, j'ai simplifié en utilisant la variable bitmap telle quelle. Si ton code appelant fournit une image PIL valide (comme dans l'exemple if __name__ == "__main__": de balloontiptk.py), elle sera utilisée.
#
# 3. La méthode OnBalloonTipShow
#
#     Cette méthode est la logique métier de l'application. Dès que l'info-bulle a été montrée, elle appelle settings.setboolean("balloontips", name, False) pour désactiver immédiatement l'affichage futur de cette info-bulle spécifique. C'est le comportement typique d'une "nouveauté" ou d'un "tip" qui ne doit s'afficher qu'une seule fois.
#
# Instructions d'implémentation
#
#     Enregistre le code ci-dessus sous le nom de fichier balloontips_tk.py.
#
#     Assure-toi que les imports fonctionnent :
#
#         taskcoachlib.widgets.balloontip doit contenir la classe de base BalloonTipManager adaptée pour Tkinter.
#
#         balloontiptk doit être le fichier que nous venons de convertir, contenant la classe BalloonTip.
#
#     Tu devras t'assurer que le reste de Task Coach utilise cette nouvelle classe BalloonTipManager là où l'ancienne était utilisée, probablement lors de l'initialisation de l'interface utilisateur.

# Avec le fichier artprovidertk.py converti, nous pouvons maintenant rendre la classe BalloonTipManager dans Tkinter fonctionnelle en utilisant le nouveau système de gestion d'icônes.
# Explication des modifications
#
# L'objectif principal était de gérer l'icône, qui était codée en dur dans la version wxPython :
#
# bitmap=wx.ArtProvider.GetBitmap("lamp_icon", wx.ART_MENU, (16, 16))

# Importation : Nous importons art_provider_tk (l'instance singleton de ArtProviderTk) et la constante ART_MENU directement depuis votre fichier artprovidertk.py converti.
#
# Récupération de l'icône : La méthode GetBitmap de art_provider_tk est appelée avec l'ID d'icône 'lamp_icon', le contexte ART_MENU et la taille désirée (16, 16). Cette méthode devrait retourner un objet ImageTk.PhotoImage utilisable par la classe BalloonTip (implémentée dans balloontiptk.py).
#
# Héritage : La logique de la classe de base balloontip.BalloonTipManager est préservée,
# et nous utilisons super().AddBalloonTip pour lui déléguer l'affichage après avoir effectué la vérification des paramètres et récupéré l'icône.
#
# Désactivation : La méthode OnBalloonTipShow désactive l'info-bulle en utilisant settings.setboolean("balloontips", name, False), garantissant que le conseil ne s'affiche qu'une seule fois.
from taskcoachlib.widgetstk import (
    balloontiptk,
)  # Import de la classe de base BalloonTipManager
from taskcoachlib.widgetstk.balloontiptk import (
    BalloonTip,
)  # Import de notre classe Tkinter BalloonTip
from PIL import Image  # Nécessaire pour l'icône
import tkinter as tk  # On utilise tkinter ici, même si l'ArtProvider n'existe pas

# Importation de l'ArtProvider Tkinter et de la constante du client pour le menu
from taskcoachlib.guitk.artprovidertk import art_provider_tk, ART_MENU


class BalloonTipManager(balloontiptk.BalloonTipManager):
    """
    Gestionnaire d'info-bulles qui contrôle si une bulle doit être affichée
    en fonction des paramètres de l'utilisateur.

    Il vérifie les paramètres utilisateur avant d'afficher une info-bulle
    et utilise l'ArtProvider Tkinter pour l'icône.
    """

    def AddBalloonTip(
        self,
        settings,
        name,
        target,
        message=None,
        title=None,
        bitmap=None,
        getRect=None,
    ):
        """
        Ajoute et potentiellement affiche une info-bulle si elle est activée
        dans les paramètres de l'utilisateur.

        Args :
            settings: L'objet de configuration de Task Coach.
            name: Le nom unique de l'info-bulle dans les paramètres ("balloontips").
            target: Le widget Tkinter cible.
            message: Le message à afficher.
            title: Le titre de la bulle.
            bitmap: L'image PIL à afficher (simule wx.ArtProvider.GetBitmap).
            getRect: Fonction optionnelle pour obtenir la géométrie du widget cible.
        """
        # 1. Vérifie si l'info-bulle est activée dans les paramètres.
        #    On utilise settings.getboolean("section", "nom_du_setting")
        if settings.getboolean("balloontips", name):

            # --- Simulation de wx.ArtProvider.GetBitmap("lamp_icon", ...) ---
            # Dans Task Coach, 'lamp_icon' est souvent une petite image d'information.
            # En Tkinter/PIL, nous allons créer une image simple si aucune n'est fournie,
            # ou essayer de charger une image réelle si l'on a un mécanisme d'ArtProvider
            # (que nous n'avons pas ici, nous faisons simple).
            # Nous utilisons le 'bitmap' passé en argument si disponible.
            # Pour l'instant, on laisse 'bitmap' comme None pour ne pas casser
            # si l'image n'est pas trouvée (comme dans l'original qui utilisait 'lamp_icon').
            # Si le bitmap est None, la classe BalloonTip gérera son absence.

            # 2. Récupère le bitmap de l'icône de la lampe via le ArtProvider Tkinter
            #    L'icône "lamp_icon" est généralement utilisée pour les conseils/tips.
            #    On simule la taille (16, 16) et le contexte (ART_MENU) de l'original.
            lamp_bitmap = art_provider_tk.GetBitmap(
                "lamp_icon",
                ART_MENU,
                (16, 16)
            )

            # 3. Appelle la méthode AddBalloonTip de la classe de base (qui utilise
            #    notre classe BalloonTip de balloontiptk.py).
            #    Le 'target' doit être un widget Tkinter.
            #    Appelle la méthode de la classe de base avec le bitmap récupéré.
            #    Le 'bitmap' passé en argument original (s'il y en avait un) est ignoré
            #    pour forcer l'icône de la lampe.
            super().AddBalloonTip(
                target=target,
                message=message,
                title=title,
                # bitmap=wx.ArtProvider.GetBitmap("lamp_icon", wx.ART_MENU, (16, 16)),
                # bitmap=bitmap,  # On utilise le bitmap fourni si nécessaire
                bitmap=lamp_bitmap,  # Utilise l'icône de la lampe récupérée
                getRect=getRect,
                name=name,
                settings=settings,
            )

    def OnBalloonTipShow(self, name=None, settings=None):
        """
        Appelé lorsque l'info-bulle est affichée pour la première fois.
        Désactive le paramètre correspondant pour qu'elle ne s'affiche plus.
        """
        if settings and name:
            # 4. Met à jour le paramètre pour ne plus afficher cette info-bulle.
            settings.setboolean("balloontips", name, False)
