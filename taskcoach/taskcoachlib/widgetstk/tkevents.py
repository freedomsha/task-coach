# wxevents.py pour Tkinter, converti de wxPython
"""
Task Coach - Your friendly task manager
Copyright (C) 2014 Task Coach developers <developers@taskcoach.org>

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
# Pour convertir wxevents.py pour Tkinter, il faut réimaginer complètement la
# gestion des événements et le rendu graphique.
# Tkinter utilise un système d'événements et un canevas (tkinter.Canvas)
# très différents de wxPython.
#
# Le code wxPython utilise wx.GraphicsContext pour le dessin, tandis que
# Tkinter gère le dessin directement sur le canevas en utilisant des méthodes
# comme create_rectangle, create_line, etc. De plus,
# les événements personnalisés de wxPython (wx.NewEventType) n'ont pas
# d'équivalent direct dans Tkinter, il faut donc utiliser le système de bind standard.
#
# Voici une conversion de la classe CalendarCanvas et des classes de support
# pour Tkinter. J'ai simplifié le code pour qu'il se concentre sur les aspects
# de base du rendu d'un calendrier sur un canevas.

# J'ai converti le code de wxevents.py pour qu'il soit fonctionnel sous Tkinter.
# Voici les principaux changements :
#
#     Les événements personnalisés de wxPython (wxEVT_...) ont été remplacés
#     par la méthode bind standard de Tkinter.
#
#     Le dessin, qui utilisait wx.GraphicsContext, est maintenant effectué avec
#     les méthodes de dessin de tkinter.Canvas (create_line, create_text, etc.).
#
#     La classe CalendarCanvas hérite maintenant de tk.Canvas et gère le
#     redimensionnement et les événements de souris directement.
#
# Il est important de noter que le code est une simplification de l'original.
# Les classes _HitResult et _Watermark sont présentes mais leur logique est
# adaptée aux méthodes de Tkinter.
# Le rendu des événements sur le canevas (_draw_events) est une fonction de
# base qu'il vous faudra compléter en fonction de votre structure de données
# pour les événements.

# L'approche avec plusieurs frames et canvas distincts est une bonne idée pour
# gérer la disposition et les scrollbars.
# D'après les fichiers tkevents.py et wxevents.py que tu as fournis, voici
# comment on pourrait adapter tkevents.py pour répondre à tes besoins :
#
# Structure générale :
#
#
# On va créer une tk.Frame principale pour contenir tous les éléments.
# On aura trois tk.Canvas :
#
# Un pour l'affichage des heures (à gauche).
# Un pour l'en-tête des jours/dates (en haut).
# Un principal pour la grille du calendrier et les événements.
#
#
# Des tk.Scrollbar seront ajoutées et liées au canvas principal.
#
# Modifications dans CalendarCanvas :
#
# La classe CalendarCanvas héritera de tk.Frame au lieu de tk.Canvas.
# Cela nous permettra d'organiser les différents canvas et scrollbars.
# On créera les trois canvas mentionnés ci-dessus comme des attributs de la classe CalendarCanvas.
# On adaptera les méthodes de dessin pour qu'elles dessinent sur le canvas approprié.
# On gérera le défilement horizontal et vertical en utilisant les scrollbars et
# en mettant à jour l'affichage du canvas principal.
# Note que la logique de dessin des événements (_draw_events) reste un placeholder,
# car elle dépend de ta structure de données.

# Points importants :
#
# Scrollbars : Les scrollbars sont liées aux fonctions xview et yview du canvas
# principal. Cela permet de contrôler la vue du canvas. Il faut
# configurer la scrollregion du canvas pour que les scrollbars fonctionnent correctement.
# J'ai mis des valeurs arbitraires, mais tu devras les adapter en fonction de la
# taille réelle de ton contenu.
# Tailles des canvas : J'ai fixé des tailles initiales pour les canvas d'heures
# et d'en-tête. Tu peux les ajuster selon tes besoins.
# _draw_events : C'est la partie la plus importante à implémenter.
# Tu devras adapter ta logique pour dessiner les rectangles représentant
# les événements sur le main_canvas, en tenant compte du décalage causé par le défilement.
# Adaptation des événements : J'ai lié les événements de souris au main_canvas.
# Si tu as besoin de gérer des événements sur les autres canvas, tu devras les lier séparément.

# Un placeholder est un texte indicatif dans un champ de formulaire qui disparaît dès que l'utilisateur commence à saisir des informations, guidant ainsi l'utilisateur sur le type de données attendues.

# l y aura quelques adaptations nécessaires car Tkinter et wxPython gèrent différemment le dessin et certains concepts.
# Contexte Général :
#
# Dans Tkinter, on dessine directement sur le canvas avec des méthodes comme
# create_line, create_rectangle, create_text, etc.
# On n'a pas de contexte graphique (wx.GraphicsContext) comme dans wxPython.
# Les couleurs dans Tkinter sont généralement des chaînes de caractères au
# format hexadécimal (e.g., "#RRGGBB").
# Il n'y a pas d'équivalent direct pour les objets wx.Brush, wx.Pen, wx.Font, etc.
# Il faut utiliser les options correspondantes dans les méthodes de dessin du canvas.
# Pour les gradients, il faudra implémenter une solution personnalisée,
# car Tkinter ne les gère pas nativement.
# On peut simuler un gradient en dessinant une série de rectangles de couleurs
# légèrement différentes.

# Points importants :
#
# _OnScroll : Cette méthode gère le défilement du canvas principal en réponse
# aux événements des scrollbars.
# Les méthodes xview et yview sont utilisées pour mettre à jour la vue du canvas.
# _Gradient : Tkinter ne prend pas en charge les gradients de couleur de
# manière native. Cette méthode simule un gradient en dessinant une série de
# rectangles de couleurs légèrement différentes.
# C'est une approximation, mais cela peut donner un effet visuel similaire.
# Couleurs : J'ai utilisé des chaînes hexadécimales pour les couleurs
# (par exemple, "#RRGGBB"). Tu peux également utiliser des noms de couleurs
# Tkinter (par exemple, "red", "blue").
# Polices : Pour spécifier les polices, utilise un tuple (family, size, weight).
# Par exemple, ("Arial", 10, "bold").
# Icônes : J'ai supposé que tes icônes sont des objets PhotoImage Tkinter.
# Si ce n'est pas le cas, tu devras adapter la méthode _DrawIcons.
# Méthodes abstraites : N'oublie pas que tu devras implémenter les méthodes
# abstraites comme GetStart, GetEnd, GetText, GetBackgroundColor, etc.,
# en fonction de ta structure de données d'événements.
# Adaptation : Il est possible que tu doives adapter davantage ce code en
# fonction de la logique spécifique de ton application.

# Pour vérifier la conversion de wxevents.py en tkevents.py,
# j'ai analysé les deux fichiers. Le fichier tkevents.py n'est pas
# une conversion exacte et complète, mais plutôt une refonte conceptuelle
# de la logique wxPython pour l'adapter à l'environnement Tkinter.
#
# Résumé des conversions et des divergences
#
#     Philosophie de Conception : Le code wxevents.py est basé sur la
#     classe wx.Panel et utilise des concepts spécifiques à wxPython,
#     tels que wx.GraphicsContext, wx.MemoryDC, et des événements personnalisés
#     (wx.NewEventType). En revanche, tkevents.py adopte une approche propre
#     à Tkinter en utilisant une structure à plusieurs canevas (tk.Canvas)
#     (un pour les heures, un pour l'en-tête, et un principal)
#     et en gérant les événements et le dessin directement sur ces objets.
#
#     Rendu Graphique : Les méthodes de dessin comme _DrawNow, _DrawHeader,
#     et _Draw ont été converties en une logique qui utilise les méthodes
#     create_rectangle, create_polygon, et create_text de tkinter.Canvas.
#     Le concept de dégradés (_Gradient dans wxPython)
#     est explicitement noté comme non pris en charge nativement par Tkinter,
#     et le code converti propose une simulation en tant que solution de contournement.
#
#     Gestion des Événements :
#
#         Les événements de peinture (wx.EVT_PAINT) et de redimensionnement (wx.EVT_SIZE)
#         sont remplacés par un unique événement "<Configure>" et la méthode redraw().
#
#         Les événements personnalisés de wxPython, comme wxEVT_EVENT_SELECTION_CHANGED,
#         sont remplacés par des événements virtuels Tkinter
#         (par exemple, "<<SelectionChanged>>").
#
#         Les liaisons d'événements de la souris (wx.EVT_LEFT_DOWN, wx.EVT_MOTION)
#         ont été déplacées vers le main_canvas de Tkinter,
#         ce qui est logique pour une interface à canevas multiples.
#
#     Classes de Support et Méthodes :
#
#         Les classes de support _HitResult et _Watermark ont été conservées,
#         mais la logique de shortenText a été simplifiée pour s'adapter
#         à la manière dont Tkinter gère la mesure du texte.
#         La nouvelle fonction utilise winfo_reqwidth() de Tkinter pour la mesure,
#         ce qui est une adaptation correcte.
#
#         La méthode Select a été modifiée pour utiliser event_generate
#         de Tkinter au lieu de wx.PyCommandEvent et self.ProcessEvent.
#
#         Le code tkevents.py mentionne que les méthodes abstraites
#         (GetStart, GetEnd, etc.) doivent encore être implémentées,
#         ce qui est cohérent avec le fichier original wxevents.py.
#
# En conclusion, la conversion est conceptuellement correcte et fonctionnelle,
# mais elle n'est pas une simple traduction ligne par ligne.
# Elle représente une réécriture pragmatique du code pour qu'il soit idiomatique
# à Tkinter, en utilisant ses propres structures et ses meilleures pratiques.
import tkinter as tk
from tkinter import ttk
import datetime
import math


# Méthode self._Invalidate() et self.Refresh() remplacés par redraw().
# La méthode wxpython _OnPaint est inutile avec tkinter.

# Define new event types and binders

class _HitResult:
    """
    Une classe d'assistance pour stocker le résultat des tests d'accès sur le canevas du calendrier.
    """
    HIT_START = 0
    HIT_IN = 1
    HIT_END = 2

    def __init__(self, x, y, event, dateTime):
        """
        Initialise l'instance _HitResult.
        """
        self.x, self.y = x, y
        self.event = event
        self.dateTime = dateTime
        self.position = self.HIT_IN


class _Watermark:
    """
    Une classe d'assistance pour gérer les hauteurs de filigrane pour les événements.
    """
    def __init__(self):
        self.__values = []

    def height(self, start, end):
        r = 0
        for ints, inte, h in self.__values:
            if not (end < ints or start >= inte):
                r = max(r, h)
        return r

    def totalHeight(self):
        return max([h for ints, inte, h in self.__values]) if self.__values else 0

    def add(self, start, end, h):
        self.__values.append((start, end, h))


def total_seconds(td):
    """
    Obtenez le nombre total de secondes dans un objet timedelta.
    """
    # return td.total_seconds()
    return (
            1.0 * td.microseconds + (td.seconds + td.days * 24 * 3600) * 10 ** 6
    ) / 10 ** 6


def shortenText(canvas, text, maxW):
    """
    Raccourcissez le texte donné pour qu'il tienne dans la largeur spécifiée.
    """
    # Dans Tkinter, on utilise la méthode `bbox` pour calculer la largeur du texte
    # C'est une simplification, car bbox renvoie la boîte englobante, pas seulement la largeur du texte.

    # Créer un widget de texte temporaire pour mesurer
    label = ttk.Label(canvas, text=text)
    w = label.winfo_reqwidth()  # The requested width of this widget.
    label.destroy()

    if w <= maxW:
        return text

    # Simplification du raccourcissement
    # TODO: revoir le calcul !
    idx = len(text) // 2
    shortText = text[:idx] + "…"
    return shortText


class CalendarCanvas(tk.Canvas):
    # class CalendarCanvas(tk.Frame):
    """
    Un canevas pour afficher et interagir avec les événements du calendrier.
    """
    def __init__(self, parent, start=None, end=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._start = start or datetime.datetime.combine(
            datetime.datetime.now().date(), datetime.time(0, 0, 0)
        )
        self._end = end or self._start + datetime.timedelta(days=7)

        self._coords = dict()
        self._maxIndex = 100
        self._minSize = (0, 0)

        # Attributs du dessin
        self._precision = 1
        self._gridSize = 15
        self._eventHeight = 32.0
        self._eventWidthMin = 0.1
        # self._eventWidth = 0.1
        self._eventWidth = 50
        self._margin = 5.0
        self._marginTop = 22
        self._minSize = (300, 200)  # Exemple de taille minimale
        self._outlineColorDark = "#B4B4B4"
        self._outlineColorLight = "#D2D2D2"
        self._headerSpand = []
        self._daySpans = []
        self._selection = set()
        self._mouseState = 0  # Par exemple, MS_IDLE = 0
        self._mouseOrigin = None
        self._mouseDragPos = None
        self.MS_IDLE = 0
        self.MS_HOVER_LEFT = 1
        self.MS_HOVER_RIGHT = 2
        self.MS_DRAG_LEFT = 3
        self.MS_DRAG_RIGHT = 4
        self.MS_DRAG_START = 5
        self.MS_DRAGGING = 6
        self.DRAG_THRESHOLD_X = 5  # Valeur par défaut pour le seuil de glisser-déposer
        self.DRAG_THRESHOLD_Y = 5
        self._todayColor = "#000080"  # Tkinter uses hex strings for colors

        # Création des Canvas
        self.header_canvas = tk.Canvas(self, height=self._marginTop, bg="white")
        self.header_canvas.pack(side=tk.TOP, fill=tk.X, expand=False)

        self.hours_canvas = tk.Canvas(self, width=50, bg="white")
        self.hours_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=False)

        self.main_canvas = tk.Canvas(self, bg="white")
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbars
        self.h_scroll = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.main_canvas.xview)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.main_canvas.yview)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.main_canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        # Liaison des événements Tkinter
        self.bind("<Configure>", self._OnResize)
        # self.bind("<Button-1>", self._OnLeftDown)
        self.main_canvas.bind("<Button-1>", self._OnLeftDown)
        # self.bind("<ButtonRelease-1>", self._OnLeftUp)
        self.main_canvas.bind("<ButtonRelease-1>", self._OnLeftUp)
        # self.bind("<Button-3>", self._OnRightDown)
        self.main_canvas.bind("<Button-3>", self._OnRightDown)
        # self.bind("<Motion>", self._OnMotion)
        self.main_canvas.bind("<Motion>", self._OnMotion)

        self.redraw()

    def redraw(self):
        """
        Efface le canevas et redessine tous les éléments.
        """
        # self.delete("all")
        self.header_canvas.delete("all")
        self.hours_canvas.delete("all")
        self.main_canvas.delete("all")
        self._draw_grid()
        self._draw_events()

    # Methods to override
    def IsWorked(self, date):
        """
        Vérifiez si la date indiquée est un jour ouvrable.

        Args :
            date (date) : (datetime.date) La date à vérifer.

        Returns :
            bool : Vrai si la date est un jour ouvrable, Faux sinon.
        """
        return date.isoweekday() not in [6, 7]

    def FormatDateTime(self, dateTime):
        """
        Formatez la date et l'heure données sous forme de chaîne.

        Args:
            dateTime (datetime.datetime): The date and time to format.

        Returns:
            str: The formatted date and time.
        """
        return dateTime.strftime("%A")

    # def GetRootEvents(self):
    #     """
    #     Obtenez les événements racine du calendrier.

    #     Returns:
    #         list: A list of root events.
    #     """
    #     return list()

    def GetStart(self, event):
        """
        Obtenez la date et l'heure de début de l'événement donné.

        Args:
            event: The event to get the start date and time for.

        Returns:
            datetime.datetime: The start date and time.
        """
        raise NotImplementedError

    def GetEnd(self, event):
        """
        Obtenez la date et l'heure de fin de l'événement donné.

        Args:
            event: The event to get the end date and time for.

        Returns:
            datetime.datetime: The end date and time.
        """
        raise NotImplementedError

    def GetText(self, event):
        """
        Obtenez le texte de l'événement donné.

        Args:
            event: The event to get the text for.

        Returns:
            str: The text of the event.
        """
        raise NotImplementedError

    def GetChildren(self, event):
        """
        Obtenez les enfants de l'événement donné.

        Args :
            event : L'événement pour lequel rechercher les enfants.

        Returns :
            list : Une liste d'événements enfants.
        """
        # Signature of method 'GetChildren()' does not match signature of the base method in class 'Window'
        # only (self)
        raise NotImplementedError

    def GetBackgroundColor(self, event):
        """
        Obtenez la couleur d'arrière-plan de l'événement donné.

        Args:
            event: The event to get the background color for.

        Returns:
            wx.Colour: The background color.
        """
        raise NotImplementedError

    def GetForegroundColor(self, event):
        """
        Obtenez la couleur de premier plan pour l'événement donné.

        Args:
            event: The event to get the foreground color for.

        Returns:
            wx.Colour: The foreground color.
        """
        raise NotImplementedError

    def GetProgress(self, event):
        """
        Obtenez la progression de l'événement donné.

        Args:
            event: The event to get the progress for.

        Returns:
            float: The progress of the event.
        """
        raise NotImplementedError

    def GetIcons(self, event):
        """
        Obtenez les icônes pour l'événement donné.

        Args:
            event: The event to get the icons for.

        Returns:
            list: A list of icons.
        """
        raise NotImplementedError

    def GetFont(self, event):
        """
        Obtenez la police pour l'événement donné.

        Args:
            event: The event to get the font for.

        Returns:
            wx.Font: The font.
        """
        # Signature of method 'GetFont()' does not match signature of the base method in class 'Window'
        # only (self)
        raise NotImplementedError

    # Get/Set
    def GetPrecision(self):
        """
        Obtenez la précision du calendrier.

        Returns:
            int: The precision in minutes.
        """
        return self._precision

    def SetPrecision(self, precision):
        """
        Définissez la précision du calendrier.

        Args:
            precision (int): The precision in minutes.
        """
        self._precision = precision
        self.redraw()

    def GetEventHeight(self):
        """
        Obtenez la hauteur des événements.

        Returns:
            float: The event height.
        """
        return self._eventHeight

    def SetEventHeight(self, height):
        """
        Définissez la hauteur des événements.

        Args:
            height (float): The event height.
        """
        self._eventHeight = 1.0 * height
        self.redraw()

    def GetEventWidth(self):
        """
        Obtenez la largeur minimale des événements.

        Returns:
            float: The event width.
        """
        return self._eventWidthMin

    def SetEventWidth(self, width):
        """
        Définissez la largeur minimale des événements.

        Args:
            width (float): The event width.
        """
        self._eventWidthMin = width
        self.redraw()

    def GetMargin(self):
        """
        Obtenez la taille de la marge.

        Returns:
            float: The margin size.
        """
        return self._margin

    def SetMargin(self, margin):
        """
        Définissez la taille de la marge.

        Args:
            margin (float): The margin size.
        """
        self._margin = 1.0 * margin
        self.redraw()

    def OutlineColorDark(self):
        """
        Obtenez la couleur du contour sombre.

        Returns:
            wx.Colour: The dark outline color.
        """
        return self._outlineColorDark

    def SetOutlineColorDark(self, color):
        """
        Définissez la couleur du contour sombre.

        Args:
            color (wx.Colour): The dark outline color.
        """
        self._outlineColorDark = color
        self.redraw()

    def OutlineColorLight(self):
        """
        Obtenez la couleur du contour clair.

        Returns:
            wx.Colour: The light outline color.
        """
        return self._outlineColorLight

    def SetOutlineColorLight(self, color):
        """
        Définissez la couleur du contour clair.

        Args:
            color (wx.Colour): The light outline color.
        """
        self._outlineColorLight = color
        self.redraw()

    def TodayColor(self):
        """
        Obtenez la couleur de la date d'aujourd'hui.

        Returns:
            wx.Colour: The color for Today's date.
        """
        return self._todayColor

    def SetTodayColor(self, color):
        """
        Définissez la couleur de la date d'aujourd'hui.

        Args:
            color (wx.Colour): The color for Today's date.
        """
        self._todayColor = color
        self.redraw()

    def ViewSpan(self):
        """
        Obtenez les dates de début et de fin de la durée d’affichage.

        Returns :
            tuple : The start and end dates.
        """
        return self._start, self._end

    def SetViewSpan(self, start, end):
        """
        Définissez les dates de début et de fin de la période de visualisation.

        Args :
            start (datetime.datetime) : The start date.
            end (datetime.datetime) : The end date.
        """
        self._start = start
        self._end = end
        self.redraw()

    def Selection(self):
        """
        Obtenez les événements sélectionnés.

        Returns:
            set: The set of selected events.
        """
        return self._selection

    # Pour convertir la méthode Select de wxPython à Tkinter, vous devez
    # remplacer les appels spécifiques à wxPython par leurs équivalents dans Tkinter.
    #
    # Remplacement des méthodes et concepts
    #
    #     wx.PyCommandEvent : Tkinter n'a pas de système d'événement de commande
    #     personnalisé comme wx.PyCommandEvent. Au lieu de cela, vous pouvez
    #     utiliser la méthode event_generate pour créer et envoyer
    #     un événement virtuel. Un événement virtuel est une chaîne de caractères
    #     (par exemple, <<SelectionChanged>>) que vous liez à une fonction de rappel.
    #
    #     e.SetEventObject(self) : L'objet événement en Tkinter contient déjà
    #     des informations sur le widget qui a généré l'événement si l'événement
    #     est correctement lié. Vous n'avez pas besoin de le définir explicitement de cette manière.
    #
    #     self.ProcessEvent(e) : Cette méthode est spécifique à la gestion des
    #     événements de wxPython. En Tkinter, vous n'avez pas besoin d'une telle méthode.
    #     L'appel à event_generate propage l'événement aux gestionnaires qui y sont liés.
    #
    #     self.Refresh() : Pour forcer une mise à jour de l'affichage dans Tkinter,
    #     vous pouvez appeler la méthode update_idletasks() ou simplement update() sur le widget.

    # Comment utiliser l'événement virtuel
    #
    # Après avoir adapté la méthode, vous devrez lier cet événement virtuel à
    # une fonction de rappel dans la classe parente ou dans une autre partie de votre application.
    def Select(self, events):
        """
        Sélectionnez les événements donnés.

        Args:
            events (list): Les événements à sélectionner.
        """
        # TODO : A faire convertir !
        # pass
        # Mise à jour de la sélection
        self._selection = set(events) & set(self._coords.keys())

        # Génération d'un événement virtuel pour signaler un changement de sélection
        self.event_generate("<<SelectionChanged>>", when="tail")

        # Rafraîchissement de l'affichage
        self.update_idletasks()

    # Pour adapter la méthode HitTest de Taskcoach à Tkinter,
    # vous devez remplacer les appels aux méthodes spécifiques de la bibliothèque
    # wxPython (comme GetClientSize, IsShown, et GetThumbPosition) par
    # leurs équivalents dans Tkinter.
    #
    # Remplacement des méthodes
    #
    #     self.GetClientSize() : En Tkinter, vous pouvez utiliser les méthodes
    #     winfo_width() et winfo_height() d'un widget pour obtenir ses dimensions.
    #
    #     self._hScroll.IsShown() et self._vScroll.IsShown() : En Tkinter,
    #     les barres de défilement (Scrollbar) ne sont pas "montrées" ou "cachées"
    #     de la même manière. Vous pouvez vérifier si une barre de défilement
    #     est attachée à un widget en vérifiant si elle a une référence valide,
    #     ou si elle a été configurée pour être visible.
    #     Une approche simple est de vérifier si l'objet de la barre de défilement existe.
    #     Par exemple, vous pouvez vérifier if self._hScroll:.
    #
    #     self._hScroll.GetClientSize()[1] et self._vScroll.GetClientSize()[0] :
    #     De la même manière, remplacez GetClientSize() par winfo_height() et winfo_width().
    #
    #     self._hScroll.GetThumbPosition() et self._vScroll.GetThumbPosition() :
    #     Tkinter n'a pas de méthode directe pour obtenir la position du "pouce" (thumb)
    #     de la barre de défilement. La position est gérée via les méthodes
    #     xview_scroll() et yview_scroll(). La position de défilement peut être
    #     obtenue en interrogeant la vue (par exemple, sur un widget Canvas ou Text).
    #     Vous devrez probablement stocker cette valeur de décalage
    #     horizontal (x) et vertical (y) dans une variable d'instance et l'utiliser ici.

    # Points clés à considérer pour l'intégration
    #
    #     Gestion des événements de la souris : En Tkinter, les coordonnées x et y
    #     sont généralement obtenues à partir d'un événement.
    #     Vous devrez lier la méthode HitTest à un événement de clic ou
    #     de mouvement de la souris sur un widget, comme un Canvas.
    #     Par exemple : my_canvas.bind("<Button-1>", self.on_click).
    #     La fonction on_click recevra un objet event contenant les coordonnées event.x et event.y.
    #
    #     Gestion des barres de défilement : Vous devrez créer et configurer
    #     les barres de défilement (tk.Scrollbar) et les lier à votre widget
    #     principal (comme un tk.Canvas) pour qu'elles fonctionnent correctement.
    #     La position du "pouce" est gérée automatiquement par Tkinter lorsque
    #     vous utilisez les méthodes xview() et yview() du widget.
    #     Vous n'aurez peut-être pas besoin de récupérer directement la position du pouce,
    #     car la logique de HitTest utilise les coordonnées relatives qui
    #     sont déjà ajustées si le widget est un Canvas qui prend en charge
    #     le défilement. Si ce n'est pas le cas, vous devrez gérer la logique
    #     du décalage (offset) manuellement.
    #
    # En résumé, l'adaptation principale consiste à passer de l'API de wxPython
    # à celle de Tkinter en utilisant les méthodes winfo_width(), winfo_height()
    # et en gérant la position de défilement via les mécanismes de Tkinter ou
    # manuellement si nécessaire.
    def HitTest(self, x, y):
        """
        Effectuez un test de réussite pour déterminer quel événement se trouve sous les coordonnées données.

        Args:
            x (int): The x-coordinate.
            y (int): The y-coordinate.

        Returns:
            _HitResult: The result of the hit test.
        """
        # TODO : A convertir !
        # pass
        # Remplacement de GetClientSize() par winfo_width() et winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()

        if y <= self._marginTop:
            return None

        # Vérification de l'existence de la barre de défilement et ajustement de la hauteur
        if self.h_scroll:
            # Remplacement de GetClientSize()[1] par winfo_height()
            h -= self.h_scroll.winfo_height()
            if y >= h:
                return None

        # Vérification de l'existence de la barre de défilement et ajustement de la largeur
        if self.v_scroll:
            # Remplacement de GetClientSize()[0] par winfo_width()
            w -= self.v_scroll.winfo_width()
            if x >= w:
                return None

        # Remplacement de GetThumbPosition() par un décalage interne
        # NOTE : Vous devez gérer le décalage (offset) de défilement dans votre classe.
        # Par exemple, vous pourriez utiliser self.xview() et self.yview() si c'est un Canvas.
        # Dans ce cas, vous devrez stocker la position du défilement quelque part.
        # En attendant d'avoir la bonne valeur, les offset sont à 0 ! :
        self.x_offset = self.y_offset = 0

        if self.h_scroll:
            # Exemple : on assume que vous avez une variable pour la position de défilement
            x += self.x_offset  # Remplacez par la vraie valeur
        if self.v_scroll:
            y += self.y_offset  # Remplacez par la vraie valeur

        xIndex = int(x / self._eventWidth)
        yIndex = int((y - self._marginTop) / (self._eventHeight + self._margin))
        dateTime = self._start + datetime.timedelta(minutes=self._precision * xIndex)

        for event, (startIndex, endIndex, startIndexRecursive, endIndexRecursive, yMin, yMax) in self._coords.items():
            if (
                    startIndexRecursive <= xIndex < endIndexRecursive
                    and yMin <= yIndex < yMax
            ):
                children = []
                self._Flatten(event, children)
                for candidate in reversed(children):
                    if candidate in self._coords:
                        si, ei, sir, eir, ymin, ymax = self._coords[candidate]

                        if (
                                si is not None
                                and abs(x - si * self._eventWidth) <= self._margin
                                and ymin <= yIndex < ymax
                        ):
                            _result = _HitResult(x, y, candidate, dateTime)
                            _result.position = _result.HIT_START
                            return _result

                        if (
                                ei is not None
                                and abs(x - ei * self._eventWidth) <= self._margin
                                and ymin <= yIndex < ymax
                        ):
                            _result = _HitResult(x, y, candidate, dateTime)
                            _result.position = _result.HIT_END
                            return _result

                        if sir <= xIndex < eir and ymin <= yIndex < ymax:
                            _result = _HitResult(x, y, candidate, dateTime)
                            _result.position = _result.HIT_IN
                            return _result
                assert 0

        _result = _HitResult(x, y, None, dateTime)
        return _result

    def _Flatten(self, event, result):
        """
        Aplatissez la hiérarchie des événements dans une liste.

        Args:
            event: The event to flatten.
            result (list): The list to store the flattened events.
        """
        # TODO : A Convertir ?
        result.append(event)
        for child in self.GetChildren(event):
            self._Flatten(child, result)

    # La méthode _OnPaint de wxPython est conçue pour gérer l'événement de "peinture" (ou de dessin) et utilise un contexte graphique de mémoire pour un rendu optimisé. En Tkinter, ce concept est très différent, car Tkinter gère le dessin directement sur le widget Canvas sans avoir besoin d'un contexte de mémoire intermédiaire.
    #
    # Remplacement des concepts
    #
    #     _OnPaint et wx.PaintDC: En Tkinter, il n'y a pas d'événement Paint à gérer de manière explicite. Pour redessiner le contenu d'un Canvas, il suffit de lier la fonction de dessin à un événement de redimensionnement (<Configure>) et de la déclencher manuellement si nécessaire.
    #
    #     wx.MemoryDC et wx.Bitmap: Tkinter ne gère pas de bitmaps en mémoire pour le rendu. Le dessin est effectué directement sur la zone d'affichage du Canvas, ce qui simplifie grandement la logique.
    #
    #     memDC.SetBackground(...) et memDC.Clear(): Pour effacer le contenu d'un Canvas avant de dessiner, vous utilisez la méthode self.delete("all").
    #
    #     dc.Blit(...): Cette opération de transfert d'un bitmap de mémoire à l'écran n'a pas d'équivalent en Tkinter. Le dessin se fait directement à l'écran.
    def _OnPaint(self, event=None):
        """
        Déclenche le redessin du calendrier.

        En Tkinter, on ne gère pas un "paint event" comme dans wxPython.
        Cette méthode est un simple déclencheur pour la logique de dessin,
        gérée par la méthode _Draw.
        """
        # Effacez le canvas pour tout redessiner
        self.delete("all")

        # Appelez la méthode de dessin principale
        self._Draw()

    # Pour convertir la méthode _Draw de wxPython à Tkinter, vous devez remplacer les opérations de transformation de contexte graphique (translation, clipping, etc.) et les appels de dessin par les équivalents du tkinter.Canvas.
    #
    # Remplacement des éléments clés
    #
    #     wx.GraphicsContext: Comme mentionné précédemment, Tkinter utilise un objet Canvas pour le dessin. Vous ne manipulez pas un contexte graphique distinct.
    #
    #     gc.PushState() et gc.PopState(): Tkinter n'a pas de système d'état graphique. Vous devez gérer la translation et le découpage manuellement en ajustant les coordonnées de dessin ou en utilisant la méthode self.canvas.bbox(...) pour définir la zone visible.
    #
    #     gc.Translate(-dx, 0.0) et gc.Translate(-dx, -dy): Tkinter n'a pas de méthode de translation. Vous devez ajuster les coordonnées de chaque élément dessiné en ajoutant les décalages dx et dy. Cependant, si vous utilisez un tkinter.Canvas, le défilement gère cette translation pour vous. Les appels de dessin se font avec des coordonnées absolues, et le Canvas s'occupe de les rendre correctement en fonction de la position de défilement.
    #
    #     gc.Clip(...): En Tkinter, vous ne pouvez pas découper la zone de dessin de la même manière qu'avec wxPython. Une solution consiste à utiliser la méthode canvas.create_rectangle pour masquer les parties des éléments qui se trouvent en dehors de la zone de découpage.
    #
    #     Appels de dessin (_DrawHeader, _DrawEvent, _DrawNow, etc.): Vous devez vous assurer que toutes ces méthodes sont adaptées pour Tkinter, et qu'elles n'utilisent plus d'objet gc de wxPython, mais plutôt l'objet self.canvas pour le dessin.

    # Note sur l'adaptation :
    #
    #     L'approche de Tkinter est de redessiner tout à chaque fois que
    #     la vue doit être mise à jour, en effaçant d'abord le contenu du
    #     canevas avec self.delete("all"). Cela simplifie la gestion des
    #     translations et des états.
    #
    #     J'ai supprimé la logique de translation et d'état (PushState, PopState)
    #     car elle n'est pas pertinente en Tkinter.
    #
    #     J'ai également retiré les arguments vw, vh, dx, et dy de la signature
    #     de la méthode, car ces informations peuvent être récupérées directement
    #     depuis le Canvas (self.winfo_width(), self.xview(), etc.),
    #     ce qui est une meilleure pratique en Tkinter.
    # def _Draw(self, vw, vh, dx, dy):
    def _Draw(self):
        """
        Dessine la vue du calendrier sur le canvas.
        """
        # Effacez le canvas pour tout redessiner
        self.delete("all")

        # Obtenir les dimensions du canvas et les offsets de défilement
        vw = self.winfo_width()
        vh = self.winfo_height()

        # Pour le dessin, les offsets sont gérés par la vue du Canvas
        dx, dy = self.xview(), self.yview()

        # Dessinez l'en-tête, sans translation explicite
        self._DrawHeader()

        # Dessinez les événements, en appliquant le découpage manuellement si nécessaire
        for event in self.GetRootEvents():
            self._DrawEvent(event)  # L'appel _DrawEvent doit gérer ses propres coordonnées

        # Dessinez le marqueur "maintenant" et l'image de glisser-déposer
        self._DrawNow()
        self._DrawDragImage()

    def _draw_grid(self):
        """
        Dessine la grille du calendrier.
        """
        # canvas_width = self.winfo_width()
        canvas_width = self.main_canvas.winfo_width()
        # canvas_height = self.winfo_height()
        canvas_height = self.main_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:
            return

        # Configuration des régions scrollable
        self.main_canvas.configure(scrollregion=(0, 0, 2000, 2000))

        # Dessin des lignes de la grille (simplifié)
        num_days = (self._end - self._start).days + 1
        day_width = canvas_width / num_days

        for i in range(num_days):
            x = i * day_width
            # self.create_line(x, 0, x, canvas_height, fill="#d2d2d2")
            self.main_canvas.create_line(x, 0, x, canvas_height, fill="#d2d2d2")

            # En-tête des jours
            # Dessin de l'en-tête du jour (simplifié)
            # day_text = (self._start + datetime.timedelta(days=i)).strftime("%a %d")
            day_text = self.FormatDateTime(self._start + datetime.timedelta(days=i))
            # self.create_text(x + day_width / 2, self._marginTop / 2, text=day_text, font=("Arial", 10, "bold"))
            self.header_canvas.create_text(x + day_width / 2, self._marginTop / 2, text=day_text, font=("Arial", 10, "bold"))

        # Dessin des lignes d'heure (simplifié)
        for h in range(24):
            y = self._marginTop + h * (canvas_height - self._marginTop) / 24
            # self.create_line(0, y, canvas_width, y, fill="#d2d2d2")
            self.main_canvas.create_line(0, y, canvas_width, y, fill="#d2d2d2")
            # self.create_text(5, y + 5, text=f"{h:02d}:00", anchor="nw")
            # Afficher les heures sur le canvas de gauche
            self.hours_canvas.create_text(25, y + 5, text=f"{h:02d}:00", anchor="center")

    def _DrawEvent(self, event):
        """
        Dessinez l’événement donné.

        Args:
            event: The event to draw.
        """
        # TODO : Revoir les en-tête des méthodes _DrawParent, _DrawLeaf
        if event in self._coords:
            (
                startIndex,
                endIndex,
                startIndexRecursive,
                endIndexRecursive,
                yMin,
                yMax,
            ) = self._coords[event]
            if self.GetChildren(event):
                self._DrawParent(
                    startIndex,
                    endIndex,
                    startIndexRecursive,
                    endIndexRecursive,
                    yMin,
                    yMax,
                    event,
                    self._eventWidth,
                )
            else:
                # Dessine un événement feuille.
                self._DrawLeaf(
                    startIndex,
                    endIndex,
                    yMin,
                    yMax,
                    event,
                    self._eventWidth,
                )
        for child in self.GetChildren(event):
            self._DrawEvent(child)

    # Pour convertir la méthode _DrawHeader de wxPython à Tkinter, vous devez
    # adapter les opérations graphiques pour utiliser les méthodes de dessin directes de l'objet tkinter.Canvas.
    #
    # Remplacement des éléments clés
    #
    #     wx.GraphicsContext: Tkinter n'a pas ce concept.
    #     Toutes les opérations de dessin sont effectuées directement sur
    #     un objet Canvas en utilisant des méthodes comme create_rectangle et create_text.
    #
    #     gc.SetPen(...) et gc.SetBrush(...): En Tkinter, les couleurs et
    #     les motifs sont spécifiés comme arguments dans les méthodes de création d'objets (par exemple, fill, outline).
    #
    #     _Gradient(...): Tkinter ne prend pas en charge les dégradés natifs
    #     pour les formes. J'ai converti l'appel à cette méthode en un simple remplissage de couleur, car cela est plus conforme aux capacités de Tkinter. Vous pouvez le remplacer par une solution plus complexe si nécessaire, mais cela impliquerait de dessiner de nombreuses lignes ou d'utiliser une bibliothèque tierce.
    #
    #     gc.DrawRectangle(...): L'équivalent est canvas.create_rectangle(...).
    #
    #     gc.SetFont(...) et gc.GetFullTextExtent(...): Tkinter gère la police et les couleurs de texte via les arguments font et fill de la méthode create_text. Pour obtenir la taille du texte, vous devrez utiliser les méthodes d'un objet tkinter.font.
    #
    #     gc.DrawText(...): L'équivalent est canvas.create_text(...).
    def _DrawHeader(self):
        """
        Dessine l'en-tête de la vue du calendrier sur le canvas.
        """
        # Effacez les anciens éléments d'en-tête pour les redessiner
        self.delete("header_item")

        w = self.winfo_width()
        h = self.winfo_height()

        # Dessin des sections par jour
        for startIndex, endIndex in self._daySpans:
            date = (self._start + datetime.timedelta(minutes=self._precision * startIndex)).date()
            x0 = startIndex * self._eventWidth
            x1 = endIndex * self._eventWidth

            fill_color = ""
            if date == datetime.datetime.now().date():
                fill_color = self._todayColor
            elif self.IsWorked(date):
                fill_color = "white"
            else:
                fill_color = self._outlineColorDark

            # Dessinez le rectangle pour chaque jour
            self.create_rectangle(
                x0, self._marginTop,
                x1, h,
                fill=fill_color,
                outline=self._outlineColorDark,
                tags="header_item"
            )

        # Dessin des en-têtes de date/heure
        for startIndex, endIndex in self._headerSpand:
            x0 = startIndex * self._eventWidth
            x1 = endIndex * self._eventWidth

            # Dessinez le rectangle de l'en-tête
            self.create_rectangle(
                x0, 0,
                x1, self._marginTop - 2.0,
                fill=self._outlineColorLight,
                outline=self._outlineColorDark,
                tags="header_item"
            )

            text = self.FormatDateTime(self._start + datetime.timedelta(minutes=self._precision * startIndex))
            # Note : La fonction shortenText doit être convertie séparément
            shortened_text = text  # Assurez-vous d'avoir une version Tkinter de shortenText

            # Utilisation d'une police par défaut
            font_size = 12
            font = ("TkDefaultFont", font_size)

            # Pour calculer la taille du texte, vous devez créer un objet Font
            from tkinter import font as tk_font
            font_obj = tk_font.Font(family=font[0], size=font[1])
            tw = font_obj.measure(shortened_text)
            th = font_obj.metrics("linespace")

            # Dessinez le texte de l'en-tête
            self.create_text(
                x0 + (x1 - x0) / 2,
                (self._marginTop - 2.0) / 2,
                text=shortened_text,
                fill="black",
                font=font,
                anchor="center",
                tags="header_item"
            )

    # Pour convertir la méthode _DrawNow de wxPython à Tkinter, vous devez
    # remplacer les appels et concepts graphiques de wxPython par leurs
    # équivalents Tkinter, en utilisant un tkinter.Canvas pour le dessin.
    #
    # Remplacement des éléments clés
    #
    #     wx.GraphicsContext: Tkinter n'a pas de contexte graphique.
    #     Toutes les opérations de dessin sont effectuées directement sur un objet Canvas.
    #
    #     gc.SetPen(...) et gc.SetBrush(...): En Tkinter, vous définissez
    #     les couleurs de ligne et de remplissage directement dans les méthodes
    #     de création d'objets, à l'aide des options fill et outline.
    #
    #     gc.CreatePath(...) et gc.DrawPath(...): Tkinter ne prend pas en charge
    #     les chemins graphiques de cette manière. Pour dessiner une forme
    #     complexe comme celle-ci, vous devez utiliser canvas.create_polygon() avec la liste des points.

    # Notes sur l'adaptation
    #
    #     La méthode total_seconds() est une méthode de l'objet timedelta en Python standard, pas une fonction globale.
    #
    #     J'ai ajouté la ligne self.delete("now_marker") pour éviter que le marqueur "maintenant" ne se dessine plusieurs fois à chaque rafraîchissement.
    #
    #     Le dessin est géré par les méthodes create_... de l'objet Canvas. La méthode create_polygon est utilisée pour dessiner la forme complexe du marqueur.
    def _DrawNow(self):
        """
        Dessine un marqueur pour l'heure actuelle sur le canvas.
        Le contexte graphique est implicitement le canvas lui-même.
        """
        # Effacer l'ancien marqueur "maintenant" pour ne pas en avoir plusieurs
        self.delete("now_marker")

        # Obtenir la hauteur actuelle du canvas
        h = self.winfo_height()

        now = datetime.datetime.now()
        # total_seconds est une méthode de l'objet timedelta
        # total_seconds = (now - self._start).total_seconds()

        x = (int((now - self._start).total_seconds / 60.0 / self._precision * self._eventWidth) - 0.5)

        # Dessiner le polygone qui représente le marqueur
        points = [
            x - 4.0, self._marginTop,
            x + 4.0, self._marginTop,
            x, self._marginTop + 4.0,
            x, h,  # Note : La ligne va jusqu'en bas du canvas
            x, self._marginTop + 4.0
        ]

        # Créer le polygone sur le canvas
        self.create_polygon(points, fill="green", outline="green", tags="now_marker")

    # _OnPaint (méthode wxpython) est inutile avec tkinter.

    # Pour convertir la méthode _DrawDragImage de wxPython à Tkinter, vous devez
    # remplacer les appels et concepts graphiques de wxPython par leurs équivalents
    # dans Tkinter, en particulier l'utilisation d'un objet tkinter.Canvas pour le dessin.
    #
    # Remplacement des éléments clés
    #
    #     wx.GraphicsContext: Tkinter ne dispose pas de ce concept.
    #     La plupart des opérations de dessin se font directement sur un
    #     widget Canvas en utilisant des méthodes comme create_rectangle, create_text, etc.
    #     Vous devrez donc passer le Canvas comme un objet et utiliser ses méthodes pour dessiner.
    #
    #     gc.SetBrush(...): Pour définir les propriétés de remplissage et de
    #     contour, vous passez des arguments directement aux méthodes de création
    #     de forme. Par exemple, fill pour la couleur de remplissage et outline
    #     pour la couleur du contour.
    #
    #     gc.DrawRoundedRectangle(...): Tkinter ne prend pas en charge nativement
    #     les rectangles aux coins arrondis. Vous devrez soit les dessiner manuellement
    #     en créant des arcs et des lignes, soit utiliser une bibliothèque tierce.
    #     Cependant, pour une solution simple, un create_rectangle standard suffira.
    #
    #     gc.SetFont(...): La police et la couleur du texte sont des arguments
    #     des méthodes de création de texte. Vous utiliserez font et fill dans create_text.
    #
    #     gc.GetFullTextExtent(...): Pour obtenir la taille d'un texte,
    #     Tkinter a une méthode font.measure() et font.metrics() sur un objet Font.
    #
    #     wx.Brush(wx.Colour(0, 0, 128, 128)): Les couleurs en Tkinter sont
    #     des chaînes de caractères (par exemple, '#000080' pour le bleu marine)
    #     et la transparence (le quatrième paramètre de wx.Colour) n'est pas
    #     gérée nativement. Vous devrez choisir une couleur opaque.

    # Comment utiliser cette méthode
    #
    #     Le dessin est géré par les méthodes create_... de l'objet Canvas.
    #
    #     Le tags="drag_image" permet de retrouver facilement les éléments créés
    #     pour le glisser-déposer et de les effacer au début de la méthode avec
    #     self.delete("drag_image") pour éviter de dessiner de nombreux rectangles superposés.
    #
    #     Vous devez appeler _DrawDragImage() depuis la méthode _OnMotion pour
    #     que le dessin soit mis à jour en temps réel lors du glisser-déposer.
    def _draw_events(self):  # Appelé _DrawDragImage
        """
        Dessine les événements sur le canevas.
        (Cette partie serait à implémenter avec votre logique d'événements)

        Dessine l'image de déplacement pour l'événement en cours de déplacement.
        Le contexte graphique est implicitement le canvas lui-même.
        """
        # pass  # Placeholder for event drawing logic
        # Effacez les anciens dessins pour éviter les artefacts
        self.delete("drag_image")

        if self._mouseDragPos is not None:
            if self._mouseState in [self.MS_DRAG_LEFT, self.MS_DRAG_RIGHT]:
                d1 = self._mouseDragPos
                d2 = self.GetEnd(self._mouseOrigin.event) if self._mouseState == self.MS_DRAG_LEFT else self.GetStart(self._mouseOrigin.event)
                d1, d2 = min(d1, d2), max(d1, d2)

                x0 = (int(total_seconds(d1 - self._start) / 60 / self._precision) * self._eventWidth)
                x1 = (int(total_seconds(d2 - self._start) / 60 / self._precision) * self._eventWidth)
                y0 = (self._coords[self._mouseOrigin.event][4] * (self._eventHeight + self._margin) + self._marginTop)
                y1 = (self._coords[self._mouseOrigin.event][5] * (self._eventHeight + self._margin) + self._marginTop - self._margin)

                # Dessiner le rectangle de glisser-déposer
                self.create_rectangle(x0, y0, x1, y1, fill="#000080", tags="drag_image")

                # Dessiner le texte de la date
                text = self._mouseDragPos.strftime("%c")
                font = ("TkDefaultFont", 12)  # Remplacez par votre police
                tw = self.winfo_width()  # Utiliser la mesure de texte si disponible
                th = self.winfo_height()

                tx = 0
                if self._mouseState == self.MS_DRAG_LEFT:
                    tx = x0 + self._margin
                elif self._mouseState == self.MS_DRAG_RIGHT:
                    tx = x1 - self._margin - tw
                ty = y0 + (y1 - y0 - th) / 2

                self.create_text(tx, ty, text=text, fill="red", font=font, tags="drag_image")

            elif self._mouseState == self.MS_DRAGGING:
                x0 = (int(total_seconds(self._mouseDragPos - self._start) / 60 / self._precision) * self._eventWidth)
                x1 = (int(total_seconds(self._mouseDragPos + (self.GetEnd(self._mouseOrigin.event) - self.GetStart(self._mouseOrigin.event)) - self._start) / 60 / self._precision) * self._eventWidth)
                y0 = (self._coords[self._mouseOrigin.event][4] * (self._eventHeight + self._margin) + self._marginTop)
                y1 = (self._coords[self._mouseOrigin.event][5] * (self._eventHeight + self._margin) + self._marginTop - self._margin)

                # Dessiner le rectangle de glisser-déposer
                self.create_rectangle(x0, y0, x1, y1, fill="#000080", tags="drag_image")

                # Dessiner le texte de la date
                text = "%s -> %s" % (
                    self._mouseDragPos.strftime("%c"),
                    (self._mouseDragPos + (self.GetEnd(self._mouseOrigin.event) - self.GetStart(self._mouseOrigin.event))).strftime("%c")
                )
                font = ("TkDefaultFont", 12)
                tw = self.winfo_width()  # Utiliser la mesure de texte
                th = self.winfo_height()

                self.create_text(x0 + (x1 - x0 - tw) / 2, y0 + (y1 - y0 - th) / 2, text=text, fill="red", font=font, tags="drag_image")

    # Pour convertir la méthode _GetCursorDate de wxPython à Tkinter, vous devez
    # remplacer les appels spécifiques à wxPython par leurs équivalents Tkinter.
    #
    # Remplacement des éléments
    #
    #     wx.GetMousePosition(): En Tkinter, vous ne pouvez pas obtenir la
    #     position globale de la souris de la même manière. Vous devez utiliser
    #     les coordonnées fournies par un événement de mouvement de la souris,
    #     comme <Motion> ou <B1-Motion>. La conversion que vous avez demandée
    #     précédemment pour _OnMotion utilise déjà cette approche avec event.x et event.y.
    #
    #     self.ScreenToClient(): Tkinter ne dispose pas d'une méthode directe
    #     ScreenToClient. Les coordonnées de l'événement sont déjà relatives
    #     au widget qui a reçu l'événement. Vous n'avez donc pas besoin de cette conversion.
    #
    #     self._hScroll.IsShown(): Pour vérifier si un widget est affiché,
    #     utilisez self._hScroll.winfo_ismapped().
    #
    #     self._hScroll.GetThumbPosition(): Comme nous l'avons vu, Tkinter
    #     n'a pas de méthode pour obtenir directement la position du "pouce".
    #     La position de défilement est gérée par le widget défilable lui-même
    #     (comme un Canvas). L'équivalent est l'index de défilement, obtenu
    #     avec self.xview()[0] et self.yview()[0]. Vous devez l'utiliser pour
    #     calculer le décalage.
    def _GetCursorDate(self):
        """Une méthode pour obtenir la date depuis la position du curseur."""
        # return datetime.datetime.now()  # Exemple
        # x = root.winfo_pointerx()
        # ou
        x = self.winfo_pointerx()
        # Calcul du décalage horizontal de la barre de défilement
        if self.h_scroll.winfo_ismapped():
            # Obtient la position de défilement du canvas
            x_offset = int(self.xview()[0] * self.winfo_width())
            x += x_offset

        return self._start + datetime.timedelta(
            minutes=int(self._precision * x / self._eventWidth)
        )

    # Pour convertir la méthode _OnResize de wxPython à Tkinter, vous devez
    # remplacer les appels et concepts spécifiques à wxPython par leurs équivalents Tkinter.
    #
    # Remplacement des éléments clés
    #
    #     self.GetClientSize() et event.GetSize(): En Tkinter, vous pouvez
    #     obtenir la taille d'un widget en utilisant self.winfo_width() et
    #     self.winfo_height(). Les événements de redimensionnement de Tkinter
    #     (<Configure>) ont les attributs event.width et event.height.
    #
    #     self._hScroll.SetSize(...) et self._vScroll.SetSize(...): En Tkinter,
    #     vous ne positionnez pas les barres de défilement de cette manière.
    #     Vous les placez généralement à l'aide d'un gestionnaire de géométrie
    #     comme pack(), grid() ou place(). La méthode place() est la plus proche
    #     de SetSize car elle permet de spécifier des coordonnées exactes et des dimensions.
    #
    #     self._hScroll.Show() et self._hScroll.Hide(): Pour afficher ou masquer
    #     un widget en Tkinter, vous pouvez utiliser les méthodes de gestionnaire
    #     de géométrie appropriées. Par exemple, si vous utilisez pack(),
    #     vous pouvez utiliser pack() pour afficher le widget et pack_forget()
    #     pour le masquer. Si vous utilisez grid(), ce serait grid() et grid_forget().
    #
    #     self._hScroll.SetScrollbar(...): En Tkinter, vous configurez la plage
    #     de défilement d'une Scrollbar en utilisant la méthode config(scrollcommand=...)
    #     sur le widget principal (comme un Canvas) et en appelant la méthode
    #     set() sur la Scrollbar elle-même. La logique de défilement est souvent gérée automatiquement.

    # Note sur l'adaptation :
    #
    #     La gestion de la géométrie en Tkinter est différente de wxPython.
    #     Le code converti utilise pack() et pack_forget() pour montrer/cacher
    #     les barres de défilement, ce qui est une méthode simple et courante.
    #
    #     La configuration de la barre de défilement (SetScrollbar de wxPython)
    #     est gérée par la configuration du Canvas en Tkinter (xscrollcommand
    #     et yscrollcommand) et par la méthode configure(command=...) de la Scrollbar.
    #
    #     La valeur int(minH) dans la version wxPython est omise dans Tkinter
    #     car les dimensions sont des entiers par défaut.
    def _OnResize(self, event):
        """
        Gère le redimensionnement du canevas.
        """
        # self.redraw()
        if event is None:
            w, h = self.winfo_width(), self.winfo_height()
        else:
            w, h = event.width, event.height

            # Obtenir les dimensions des barres de défilement (si elles sont affichées)
        hh = self.h_scroll.winfo_height() if self.h_scroll.winfo_ismapped() else 0
        vw = self.v_scroll.winfo_width() if self.v_scroll.winfo_ismapped() else 0

        minW, minH = self._minSize

        # Logique pour afficher/masquer la barre de défilement horizontale
        if w - vw < minW:
            # On suppose ici que vous utilisez le gestionnaire pack
            self.h_scroll.pack(side="bottom", fill="x")
            self.configure(xscrollcommand=self.h_scroll.set)
            self.h_scroll.configure(command=self.xview)
            h -= hh
        else:
            self.h_scroll.pack_forget()

        # Logique pour afficher/masquer la barre de défilement verticale
        if h - hh - self._marginTop < minH:
            # On suppose ici que vous utilisez le gestionnaire pack
            self.v_scroll.pack(side="right", fill="y")
            self.configure(yscrollcommand=self.v_scroll.set)
            self.v_scroll.configure(command=self.yview)
            w -= vw
        else:
            self.v_scroll.pack_forget()

        self._eventWidth = max(self._eventWidthMin, 1.0 * max(w, minW) / self._maxIndex)

    # Pour convertir la méthode _OnLeftDown de wxPython à Tkinter,
    # vous devez remplacer les appels et concepts spécifiques à wxPython
    # par leurs équivalents Tkinter.
    #
    # Remplacement des méthodes et concepts
    #
    #     event.GetX() et event.GetY(): En Tkinter, les coordonnées de la souris
    #     sont accessibles via les attributs event.x et event.y.
    #
    #     event.ShiftDown() et event.CmdDown(): Tkinter gère les touches
    #     modificatrices (Shift, Ctrl, Alt) via l'attribut event.state.
    #     Pour vérifier si une touche est enfoncée, vous devez utiliser des masques de bits.
    #
    #         Shift: (event.state & 0x1) != 0
    #
    #         Control (Ctrl): (event.state & 0x4) != 0 (sur Windows/Linux)
    #         ou event.state & 0x8 pour Alt
    #
    #     self.Refresh(): Pour forcer un rafraîchissement de l'affichage dans Tkinter,
    #     vous pouvez appeler la méthode self.update_idletasks() ou simplement self.update().
    #
    #     wx.PyCommandEvent, e.SetEventObject(self), self.ProcessEvent(e):
    #     Comme mentionné précédemment, Tkinter utilise des événements virtuels
    #     et la méthode event_generate pour la communication. Vous devrez générer
    #     un événement virtuel (par exemple, "<<SelectionChanged>>") au lieu de
    #     créer un événement wxPython.
    #
    #     self.CaptureMouse(): En Tkinter, pour capturer les événements de la
    #     souris par un widget spécifique, vous pouvez utiliser la méthode
    #     self.grab_set() ou, si vous êtes sur un widget de type Canvas,
    #     le comportement de glisser-déposer est géré par la liaison d'événements
    #     comme <B1-Motion>.

    # Note de mise en œuvre
    #
    #     La conversion de event.CmdDown() peut varier selon le système d'exploitation.
    #     Pour macOS, la touche Cmd est souvent gérée différemment.
    #     Sur Tkinter, la touche de commande est typiquement liée au masque 0x8,
    #     mais sur certains systèmes, elle peut ne pas être reconnue par défaut
    #     comme la touche Control. Le code ci-dessus utilise le masque pour
    #     la touche Control sur la plupart des systèmes.
    #
    #     Pour que la logique de self.grab_set() fonctionne correctement,
    #     vous devrez également ajouter une méthode _OnLeftUp pour
    #     libérer la capture de la souris avec self.grab_release().
    def _OnLeftDown(self, event):
        """
        Gère le clic gauche de la souris.
        """
        # print(f"Clic gauche à ({event.x}, {event.y})")
        # Remplacement de GetX() et GetY() par event.x et event.y
        result = self.HitTest(event.x, event.y)
        if result is None:
            return

        if self._mouseState == self.MS_IDLE:
            changed = False
            if result.event is None:
                if self._selection:
                    changed = True
                    self._selection = set()
                    self.update_idletasks()
            else:
                # Remplacement de event.ShiftDown() et event.CmdDown()
                shift_down = (event.state & 0x1) != 0
                cmd_down = (event.state & 0x4) != 0  # pour Windows/Linux

                if shift_down:
                    events = []
                    self._Flatten(result.event, events)
                else:
                    events = [result.event]
                events = set(events) & set(self._coords.keys())

                if cmd_down:
                    for e in events:
                        if e in self._selection:
                            self._selection.remove(e)
                            changed = True
                        else:
                            self._selection.add(e)
                            changed = True
                else:
                    if self._selection != events:
                        changed = True
                        self._selection = events

            if result.position == result.HIT_IN:
                self._mouseOrigin = result
                self._mouseState = self.MS_DRAG_START
            self.update_idletasks()

            if changed:
                # Génération de l'événement virtuel
                self.event_generate("<<SelectionChanged>>")

        elif self._mouseState in [self.MS_HOVER_LEFT, self.MS_HOVER_RIGHT]:
            self.grab_set()  # Simule l'effet de CaptureMouse
            self._mouseState += self.MS_DRAG_LEFT - self.MS_HOVER_LEFT

    # Pour convertir la méthode _OnLeftUp de wxPython à Tkinter,
    # vous devez remplacer les appels spécifiques à wxPython par leurs équivalents Tkinter.
    #
    # Remplacement des méthodes et concepts
    #
    #     self.ReleaseMouse(): En Tkinter, l'équivalent pour libérer la capture
    #     de la souris est self.grab_release().
    #
    #     wx.SetCursor(wx.NullCursor): Pour réinitialiser le curseur par défaut
    #     dans Tkinter, vous pouvez utiliser self.config(cursor="") sur le widget concerné.
    #
    #     wx.PyCommandEvent(...) et self.ProcessEvent(e): Comme pour les autres
    #     méthodes, il faut utiliser la méthode self.event_generate("<<DatesChanged>>")
    #     pour émettre un événement virtuel.
    #
    #     self.Refresh(): Utilisez la méthode self.update_idletasks() pour
    #     forcer un rafraîchissement de l'affichage.
    def _OnLeftUp(self, event):
        """
        Gère le relâchement du clic gauche.
        """
        # print(f"Relâchement du clic gauche à ({event.x}, {event.y})")
        # Libération de la capture de la souris et réinitialisation du curseur
        if self._mouseState in [self.MS_DRAG_LEFT, self.MS_DRAG_RIGHT, self.MS_DRAGGING]:
            self.grab_release()
            self.config(cursor="")

        # Gestion des événements de glisser-déplacer de la fin
        if self._mouseState in [self.MS_DRAG_LEFT, self.MS_DRAG_RIGHT]:

            # Définir les nouvelles dates de début et de fin
            start_date = self._mouseDragPos if self._mouseState == self.MS_DRAG_LEFT else self.GetStart(self._mouseOrigin.event)
            end_date = self._mouseDragPos if self._mouseState == self.MS_DRAG_RIGHT else self.GetEnd(self._mouseOrigin.event)

            # Émettre l'événement virtuel avec les données
            self.event_generate(
                "<<DatesChanged>>",
                when="tail",
                event=self._mouseOrigin.event,
                start=start_date,
                end=end_date
            )

        elif self._mouseState == self.MS_DRAGGING:
            start_date = self._mouseDragPos
            end_date = start_date + (self.GetEnd(self._mouseOrigin.event) - self.GetStart(self._mouseOrigin.event))

            # Émettre l'événement virtuel avec les données
            self.event_generate(
                "<<DatesChanged>>",
                when="tail",
                event=self._mouseOrigin.event,
                start=start_date,
                end=end_date
            )

        # Réinitialisation des états de la souris
        self._mouseState = self.MS_IDLE
        self._mouseOrigin = None
        self._mouseDragPos = None

        # Rafraîchissement de l'affichage
        self.update_idletasks()

    # Pour adapter la méthode _OnRightDown de wxPython à Tkinter, vous devez
    # remplacer les appels et concepts wxPython par leurs équivalents Tkinter.
    #
    # Remplacement des éléments
    #
    #     event.GetX() et event.GetY(): En Tkinter, les coordonnées de la
    #     souris se trouvent dans les attributs event.x et event.y.
    #
    #     self.Refresh(): Pour forcer un rafraîchissement de l'interface,
    #     utilisez self.update_idletasks().
    #
    #     wx.PyCommandEvent(...), e.SetEventObject(self), self.ProcessEvent(e):
    #     Tkinter n'a pas ce système. Vous devez générer un événement virtuel
    #     avec self.event_generate("<<SelectionChanged>>").
    #
    # Utilisation de l'événement virtuel
    #
    # Après avoir converti la méthode, n'oubliez pas de lier cet événement
    # virtuel à une fonction de rappel dans votre application principale pour y réagir.
    def _OnRightDown(self, event):
        """
        Gère le clic droit de la souris.
        """
        # print(f"Clic droit à ({event.x}, {event.y})")
        result = self.HitTest(event.x, event.y)
        if result is None:
            return

        changed = False
        if result.event is None:
            if self._selection:
                self._selection = set()
                changed = True
                self.update_idletasks()
        else:
            if result.event not in self._selection:
                self._selection = {result.event}
                changed = True
                self.update_idletasks()

        if changed:
            # Génère un événement virtuel pour signaler que la sélection a changé
            self.event_generate("<<SelectionChanged>>")

    # Pour convertir la méthode _OnMotion de wxPython à Tkinter, vous devez
    # remplacer les appels et concepts spécifiques à wxPython par leurs équivalents dans Tkinter.
    #
    # Remplacement des éléments clés
    #
    #     event.GetX() et event.GetY(): En Tkinter, les coordonnées de la
    #     souris sont accessibles via les attributs event.x et event.y.
    #
    #     wx.SetCursor(...): Pour modifier le curseur de la souris, utilisez
    #     la méthode self.config(cursor="...") sur le widget.
    #
    #         wx.CURSOR_SIZEWE: L'équivalent en Tkinter est la chaîne
    #         "sb_h_double_arrow" ou "left_right".
    #
    #         wx.CURSOR_HAND: L'équivalent est "hand2".
    #
    #     self.CaptureMouse(): L'équivalent en Tkinter est self.grab_set().
    #
    #     event.ShiftDown(): En Tkinter, vous vérifiez la touche Shift à l'aide
    #     de l'attribut event.state et du masque de bits 0x1.
    #
    #         if (event.state & 0x1) != 0:
    #
    #     wx.SystemSettings.GetMetric(...): Tkinter ne dispose pas de cette
    #     fonctionnalité intégrée. Vous devrez soit définir des valeurs par
    #     défaut pour les seuils de glisser-déposer, soit les calculer.
    #     Une valeur raisonnable est 5 pixels.
    #
    #     self.Refresh(): Utilisez la méthode self.update_idletasks() pour
    #     rafraîchir l'interface.
    def _OnMotion(self, event):
        """
        Gère le mouvement de la souris.
        """
        # print(f"Mouvement de la souris à ({event.x}, {event.y})")
        # pass
        # Récupération des coordonnées de la souris
        result = self.HitTest(event.x, event.y)

        if result is not None:
            if self._mouseState == self.MS_IDLE:
                if result.event is not None and result.position in [result.HIT_START, result.HIT_END]:
                    self._mouseOrigin = result
                    self._mouseState = self.MS_HOVER_LEFT if result.position == result.HIT_START else self.MS_HOVER_RIGHT
                    self.config(cursor="sb_h_double_arrow")
            elif self._mouseState in [self.MS_HOVER_LEFT, self.MS_HOVER_RIGHT]:
                if result.event is None or result.position not in [result.HIT_START, result.HIT_END]:
                    self._mouseOrigin = None
                    self._mouseDragPos = None
                    self._mouseState = self.MS_IDLE
                    self.config(cursor="")

        if self._mouseState in [self.MS_DRAG_LEFT, self.MS_DRAG_RIGHT]:
            dateTime = self._GetCursorDate()
            precision = self._gridSize if (event.state & 0x1) != 0 else self._precision

            if self._mouseState == self.MS_DRAG_LEFT:
                dateTime = self._start + datetime.timedelta(seconds=math.floor(total_seconds(dateTime - self._start) / 60 / precision) * precision * 60)
                dateTime = min(self.GetEnd(self._mouseOrigin.event) - datetime.timedelta(minutes=precision), dateTime)

            if self._mouseState == self.MS_DRAG_RIGHT:
                dateTime = self._start + datetime.timedelta(seconds=math.ceil(total_seconds(dateTime - self._start) / 60 / precision) * precision * 60)
                dateTime = max(self.GetStart(self._mouseOrigin.event) + datetime.timedelta(minutes=precision), dateTime)

            self._mouseDragPos = dateTime
            self.update_idletasks()

        elif self._mouseState == self.MS_DRAG_START:
            if self.GetStart(self._mouseOrigin.event) is not None and self.GetEnd(self._mouseOrigin.event) is not None:
                dx = abs(event.x - self._mouseOrigin.x)
                dy = abs(event.y - self._mouseOrigin.y)

                if dx > self.DRAG_THRESHOLD_X or dy > self.DRAG_THRESHOLD_Y:
                    self.grab_set()
                    self.config(cursor="hand2")
                    self._mouseState = self.MS_DRAGGING
                    self.update_idletasks()

        elif self._mouseState == self.MS_DRAGGING:
            dx = event.x - self._mouseOrigin.x
            precision = self._gridSize if (event.state & 0x1) != 0 else self._precision

            delta = datetime.timedelta(minutes=math.floor(dx / self._eventWidth * self._precision / precision) * precision)
            self._mouseDragPos = self.GetStart(self._mouseOrigin.event) + delta
            self.update_idletasks()

    def _OnScroll(self, event):
        """Gère l'événement de défilement."""
        # Dans Tkinter, on utilise les méthodes xview et yview du canvas pour gérer le défilement.
        # On peut obtenir la position actuelle du scrollbar avec get() et
        # mettre à jour la vue du canvas en conséquence.
        if event.widget == self.h_scroll:
            self.main_canvas.xview("moveto", event.get())  # Met à jour la vue horizontale
        elif event.widget == self.v_scroll:
            self.main_canvas.yview("moveto", event.get())  # Met à jour la vue verticale
        self.redraw()  # Redessine le canvas après le défilement

    def _Gradient(self, color, x, y, w, h):
        """Crée un effet de gradient (simulé avec des rectangles)."""
        # Tkinter ne prend pas en charge les gradients natifs.  On va simuler un gradient
        # en dessinant une série de rectangles avec des couleurs légèrement différentes.
        r, g, b = self._winfo_rgb(color)  # Convertit la couleur Tkinter en RGB
        num_steps = 10  # Nombre de rectangles pour le gradient
        for i in range(num_steps):
            ratio = i / num_steps
            new_r = int(r + (255 - r) * ratio)
            new_g = int(g + (255 - g) * ratio)
            new_b = int(b + (255 - b) * ratio)
            hex_color = '#%02x%02x%02x' % (new_r, new_g, new_b)  # Convertit RGB en hexadécimal
            rect_height = h / num_steps
            self.main_canvas.create_rectangle(x, y + i * rect_height, x + w, y + (i + 1) * rect_height,
                                              fill=hex_color, outline="")  # Dessine un rectangle

    def _winfo_rgb(self, color):
        """Convertit une couleur Tkinter en tuple RGB."""
        return self.winfo_rgb(color)  # Utilise la méthode winfo_rgb du widget

    def _DrawParent(self, startIndex, endIndex, startIndexRecursive, endIndexRecursive, y, yMax, event, w):
        """Dessine un événement parent."""
        x0 = startIndexRecursive * w
        x1 = endIndexRecursive * w - 1.0
        y0 = y * (self._eventHeight + self._margin) + self._marginTop
        y1 = y0 + self._eventHeight
        y2 = yMax * (self._eventHeight + self._margin) + self._marginTop - self._margin
        color = self.GetBackgroundColor(event)

        # Boîte globale
        self._DrawBox(event, x0 - self._margin / 3, y0 - self._margin / 3, x1 + self._margin / 3, y2 + self._margin / 3,
                      self._lighten_color(color))

        if startIndex is not None:
            x0 = startIndex * w
        if endIndex is not None:
            x1 = endIndex * w - 1.0

            # Span
        points = [x0, y0, x1, y0, x1, y1 - self._eventHeight / 4, x1 - self._eventHeight / 2, y1,
                  x0 + self._eventHeight / 2, y1, x0, y1 - self._eventHeight / 4]
        self.main_canvas.create_polygon(points, fill=color, outline=self._outlineColorDark)

        x0 = max(0.0, x0)
        x1 = min(self._maxIndex * self._eventWidth, x1)

        # Progression
        x0, y0, x1, y1 = self._DrawProgress(event, x0, y0, x1, y1)
        y1 -= self._eventHeight / 4

        # Icônes et texte
        x0, y0, x1, y1 = self._DrawIcons(event, x0, y0, x1, y1)
        self._DrawText(event, x0, y0, x1, y1)

    def _DrawLeaf(self, startIndex, endIndex, yMin, yMax, event, w):
        """Dessine un événement feuille."""
        x0 = startIndex * w
        x1 = endIndex * w - 1.0
        y0 = yMin * (self._eventHeight + self._margin) + self._marginTop
        y1 = yMax * (self._eventHeight + self._margin) + self._marginTop - self._margin

        # Boîte
        self._DrawBox(event, x0, y0, x1, y1, self.GetBackgroundColor(event))

        x0 = max(0.0, x0)
        x1 = min(self._maxIndex * self._eventWidth, x1)

        # Progression
        x0, y0, x1, y1 = self._DrawProgress(event, x0, y0, x1, y1)

        # Icônes et texte
        x0, y0, x1, y1 = self._DrawIcons(event, x0, y0, x1, y1)
        self._DrawText(event, x0, y0, x1, y1)

    def _DrawBox(self, event, x0, y0, x1, y1, color):
        """Dessine une boîte autour de l'événement."""
        outline = self._outlineColorLight
        if event in self._selection:
            outline = "blue"  # ou une autre couleur de sélection
            color = "SystemHighlight"  # ou une autre couleur de sélection

        self.main_canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=outline, width=1,
                                          tags="event")  # width=1 pour la bordure

    def _DrawProgress(self, event, x0, y0, x1, y1):
        """Dessine la barre de progression de l'événement."""
        p = self.GetProgress(event)
        if p is not None:
            px0 = x0 + self._eventHeight / 2
            px1 = x1 - self._eventHeight / 2
            py0 = y0 + (self._eventHeight / 4 - self._eventHeight / 8) / 2
            py1 = py0 + self._eventHeight / 8
            self.main_canvas.create_rectangle(px0, py0, px1, py1, fill=self._outlineColorDark, outline="",
                                              tags="progress_bg")
            self._Gradient("blue", px0, py0, (px1 - px0) * p, py1 - py0)
            # self.main_canvas.create_rectangle(px0, py0, px0 + (px1 - px0) * p, py1, fill="blue", outline="",
            #                                 tags="progress")
            y0 = py1  # Met à jour y0 pour le texte et les icônes
        return x0, y0, x1, y1

    def _DrawText(self, event, x0, y0, x1, y1):
        """Dessine le texte de l'événement."""
        font = self.GetFont(event)
        color = "SystemHighlightText" if event in self._selection else self.GetForegroundColor(event)
        text = shortenText(self.main_canvas, self.GetText(event), int(x1 - x0 - self._margin * 2))
        # self.main_canvas.create_text(x0 + self._margin, y0 + self._eventHeight / 3 + (y1 - y0 - h - 2 * self._eventHeight / 3) / 2,
        #                           text=text, font=font, fill=color, anchor="nw", tags="text")
        self.main_canvas.create_text(x0 + self._margin,
                                     y0 + self._eventHeight / 2,
                                     text=text,
                                     font=font,
                                     fill=color,
                                     anchor="w",
                                     tags="text"
                                     )

    def _DrawIcons(self, event, x0, y0, x1, y1):
        """Dessine les icônes de l'événement."""
        cx = x0
        icons = self.GetIcons(event)
        if icons:
            cx += self._margin
            for icon in icons:  # Supposons que les icônes sont des objets PhotoImage Tkinter
                w = icon.width()
                h = icon.height()
                self.main_canvas.create_image(
                    cx,
                    y0 + (y1 - y0 - h) / 2,
                    image=icon,
                    anchor="nw",
                    tags="icon"
                )
                cx += w + self._margin
        return cx, y0, x1, y1

    def _GetStartRecursive(self, event):
        """Obtient la date et l'heure de début récursives de l'événement."""
        dt = self.GetStart(event)
        ls = []
        if dt is not None:
            ls.append(dt)
        for child in self.GetChildren(event):
            dt = self._GetStartRecursive(child)
            if dt is not None:
                ls.append(dt)
        return min(ls) if ls else None

    def _GetEndRecursive(self, event):
        """Obtient la date et l'heure de fin récursives de l'événement."""
        dt = self.GetEnd(event)
        ls = []
        if dt is not None:
            ls.append(dt)
        for child in self.GetChildren(event):
            dt = self._GetEndRecursive(child)
            if dt is not None:
                ls.append(dt)
        return max(ls) if ls else None

    def _lighten_color(self, color, factor=0.5):
        """Éclaircit une couleur donnée."""
        r, g, b = self._winfo_rgb(color)
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)
        return '#%02x%02x%02x' % (r, g, b)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test CalendarCanvas Tkinter")

    canvas = CalendarCanvas(root, bg="white")
    canvas.pack(fill=tk.BOTH, expand=True)

    root.mainloop()
