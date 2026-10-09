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

Ce module contient la définition de la classe ToolBar,
qui représente une barre d'outils personnalisable dans l'interface utilisateur de Task Coach.

La classe ToolBar hérite de la classe AuiToolBar de la bibliothèque wxPython et
utilise la classe UICommand pour définir les commandes qui apparaissent sur la barre d'outils.

La barre d'outils peut être personnalisée par l'utilisateur en utilisant
le menu "Personnaliser" dans le menu "Affichage".
Les choix de l'utilisateur sont enregistrés dans les préférences de l'application.

La classe MainToolBar est une sous-classe de ToolBar qui est utilisée
dans la fenêtre principale de Task Coach.

La classe ToolBar est également utilisée dans les tests unitaires pour
tester la fonctionnalité de la barre d'outils.


Voici comment les commandes de la barre d’outils (UICommand)
sont créées et injectées dans la fenêtre principale de Task Coach:
**Flux de création des UICommands de la barre d’outils**

    1-MainWindow.createToolBarUICommands() (dans mainwindow.py)
    C’est le point d’entrée principal pour la création de commandes.
    Cette méthode retourne une liste d’instances de sous-classes de UICommand, comme FileOpen, EffortStartButton, etc.

    2-ToolBar.uiCommands() (dans toolbar.py)
    Appelle MainWindow.createToolBarUICommands() pour obtenir les commandes.
    Il peut aussi utiliser un cache (self.__cache) pour éviter de les recréer inutilement.

    3-ToolBar.loadPerspective()
    Cette méthode :
        - filtre les commandes à afficher selon une chaîne perspective
        - appelle appendUICommands(...) avec cette liste

    4-UICommandContainerMixin.appendUICommands(...)
    Cette méthode, héritée par ToolBar, appelle ensuite pour chaque commande :
    self.appendUICommand(uiCommand)

    5-ToolBar.appendUICommand()
    C’est ici que chaque commande est ajoutée à la barre d’outils :
        - les None sont convertis en séparateurs
        - les int en espaceurs
        - les UICommand en éléments interactifs via uiCommand.appendToToolBar(...)

    6-UICommand.appendToToolBar(...)
    C’est là que chaque commande instancie un bouton avec icône, tooltip, etc.

    7-taskcoachlib/gui/dialog/toolbar.py
    C’est là que se trouve ToolBarEditor utilisé pour la personnalisation dynamique de la barre.
    Et c’est aussi une pièce centrale du mécanisme EditToolBarPerspective.

**Où sont définies les UICommand utilisées ?**

Les classes comme FileOpen, EditUndo, EffortStartButton sont des sous-classes de base_uicommand.UICommand définies dans :
    - uicommand.py
    - base_uicommand.py

Elles surchargent typiquement :
    - appendToToolBar(...)
    - doCommand(...) (le code exécuté quand on clique)

**Exemple concret**

Prenons FileOpen :
    - Instanciée dans MainWindow.createToolBarUICommands()
    - Ajoutée par appendToToolBar() dans la barre
      Cela crée un bouton avec icône, lié à FileOpen.doCommand()
    - Le clic exécute FileOpen.doCommand() → cela appelle la méthode du contrôleur de fichiers.

"""

# D'après les logs et le code source que vous avez fournis, l'erreur AttributeError: 'str' object has no attribute 'IsOk' est explicite : la méthode MakeDisabledBitmap s'attend à recevoir un objet de type wx.Bitmap, mais elle reçoit une chaîne de caractères (str).
#
# Cela se produit généralement lorsqu'une commande UICommand (ici EditToolBarPerspective) n'a pas encore chargé son icône ou utilise un identifiant texte au lieu d'un objet bitmap réel au moment de l'ajout à la barre d'outils.
# Correction de MakeDisabledBitmap
#
# Le problème immédiat se situe dans la vérification de validité. Si bitmap est une chaîne, l'appel à .IsOk() échoue.
# Sécurisation de AddLabelTool
#
# La méthode AddLabelTool appelle MakeDisabledBitmap. Si cette dernière renvoie None ou si l'entrée est incorrecte, cela peut faire planter super().AddTool.
#
# Pourquoi cette erreur arrive-t-elle maintenant ?
#
#     Initialisation de EditToolBarPerspective : Dans loadPerspective, vous instanciez cette commande. Il est possible que dans votre version de Task Coach, cette commande spécifique ne charge pas son icône immédiatement ou utilise une icône système qui n'est pas résolue en wx.Bitmap avant l'appel à appendToToolBar.
#
#     Cycle de vie : Le log montre que l'erreur survient lors de la création des composants de la fenêtre principale. Si les ressources (images) ne sont pas encore chargées dans le cache global au moment où la barre d'outils est "réalisée", uiCommand.bitmap() pourrait renvoyer un nom de fichier ou une chaîne vide.
#
# Prochaine étape suggérée
#
# Une fois ces modifications appliquées, le programme ne devrait plus planter. Cependant, le bouton de personnalisation pourrait apparaître sans icône.
# Puisque l'erreur 'str' object has no attribute 'IsOk' survient dans la barre d'outils, cela signifie que la commande EditToolBarPerspective lui envoie son nom d'icône (une chaîne de caractères comme "edit") au lieu d'un objet image réel (wx.Bitmap).
# L'erreur vient du fait que, contrairement aux autres commandes, EditToolBarPerspective semble être instanciée ou utilisée avant que son nom d'icône ("cogwheel_icon") ne soit converti en un véritable objet wx.Bitmap.
#
# En examinant le fonctionnement habituel de Task Coach, les UICommand stockent souvent le nom de l'icône (une str) et ne la transforment en wx.Bitmap que via une méthode bitmap().
#
# Voici pourquoi cette commande précise pose problème et comment la corriger :
# 1. Pourquoi celle-ci et pas les autres ?
#
# Dans votre log, l'erreur survient ici : self.loadPerspective(window.getToolBarPerspective()) dans toolbar.py.
#
# La commande EditToolBarPerspective est un cas particulier : elle est souvent créée "à la volée" lors du chargement de la perspective de la barre d'outils. Si elle est créée sans passer par le mécanisme habituel qui convertit les noms en bitmaps (le artprovider), elle garde sa chaîne de caractères.
# 2. La solution dans uicommand.py
#
# Il faut s'assurer que la méthode bitmap() de la classe de base (ou de la commande elle-même) appelle bien l'artprovider si elle détecte qu'elle possède une chaîne au lieu d'un objet.
#

# from future import standard_library

# standard_library.install_aliases()
import logging
import wx

# from taskcoachlib.thirdparty import aui
# import aui2 as aui
from wx.lib.agw import aui
from taskcoachlib import operating_system

# from taskcoachlib.gui import uicommand
from taskcoachlib.gui.uicommand import (
    base_uicommand,
    uicommand,
    uicommandcontainer,
)

# from taskcoachlib.gui.uicommand import uicommand
# from taskcoachlib.gui.uicommand import uicommandcontainer

log = logging.getLogger(__name__)


class _Toolbar(aui.auibar.AuiToolBar):
    """
    Une classe interne qui représente une barre d'outils basée sur la classe AuiToolBar de la bibliothèque wxPython.

    Cette classe est utilisée comme base pour la classe ToolBar, qui ajoute des fonctionnalités de personnalisation à la barre d'outils.

    AuiToolBar est une barre d'outils entièrement dessinée par le propriétaire,
    parfaitement intégrée au système de mise en page AUI. Cela permet le glisser-déposer des barres d'outils,
    le comportement d'ancrage/flottant et la possibilité de définir des éléments de « débordement » dans la barre d'outils elle-même.

    Le thème par défaut utilisé est AuiDefaultToolBarArt, qui offre une apparence moderne et brillante.
    Le thème peut être modifié en appelant AuiToolBar.SetArtProvider.
    """

    def __init__(self, parent, style):
        #
        # super().__init__(parent, agwStyle=aui.AUI_TB_NO_AUTORESIZE)
        super().__init__(parent)

    def AddLabelTool(self, id, label, bitmap1, bitmap2, kind, **kwargs):
        """Ajoute un outil à la barre d'outils.

        Il s'agit de la version complète d'wx.lib.agw.aui.auibar.AuiToolBar.AddTool.

        Args:
            id:
            label:
            bitmap1:
            bitmap2:
            kind:
            **kwargs:

        Returns:

        """

        long_help_string = kwargs.pop("longHelp", "")
        short_help_string = kwargs.pop("shortHelp", "")
        # bitmap2 = self.MakeDisabledBitmap(bitmap1)
        # TypeError: _Toolbar.MakeDisabledBitmap() takes 1 positional argument but 2 were given
        # Attention ligne 63 déclaration de MakeDisabledBitmap. Ne pas mettre staticmethod.
        # On vérifie bitmap1 avant de tenter de générer bitmap2
        if bitmap1 and not isinstance(bitmap1, str):
            bitmap2 = self.MakeDisabledBitmap(bitmap1)
        else:
            # Si bitmap1 est une chaîne ou invalide, on utilise NullBitmap
            bitmap2 = wx.NullBitmap
            if isinstance(bitmap1, str):
                log.error(
                    f"AddLabelTool: bitmap1 pour '{label}' est une chaîne de caractères : {bitmap1}"
                )
                bitmap1 = wx.NullBitmap
        # auibar..AuiToolBar.AddTool ajoute un outil à la barre d'outils. Il s'agit de la version complète de :meth:`AddTool` :
        super().AddTool(
            id,
            label,
            bitmap1,
            bitmap2,
            kind,
            short_help_string,
            long_help_string,
            None,
            None,
        )
        # bitmap2 est un NoneType ! ?
        # File
        # "/home/sylvain/Téléchargements/src/TaskCoach2.7/TaskCoach-future2/lib/python3.12/site-packages/wx/lib/agw/aui/auibar.py", line
        # 1834, in AddTool
        # if not item.disabled_bitmap.IsOk():
        #     ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^ ^
        # AttributeError: 'NoneType' object has no attribute 'IsOk'
        #     def AddTool(self, tool_id, label, bitmap, disabled_bitmap, kind, short_help_string='', long_help_string='', client_data=None, target=None):
        #         """
        #         Ajoute un outil à la barre d'outils. Il s'agit de la version complète de :meth:`AddTool`.
        #
        #         :param integer `tool_id`: an integer by which the tool may be identified in subsequent operations;
        #         :param string `label`: the toolbar tool label;
        #         :param wx.Bitmap `bitmap`: the primary tool bitmap;
        #         :param wx.Bitmap `disabled_bitmap`: the bitmap to use when the tool is disabled. If it is equal to
        #          :class:`NullBitmap`, the disabled bitmap is automatically generated by greing the normal one;
        #         :param integer `kind`: the item kind. Can be one of the following:
        #
        #          ========================  =============================
        #          Item Kind                 Description
        #          ========================  =============================
        #          ``ITEM_CONTROL``          The item in the :class:`AuiToolBar` is a control
        #          ``ITEM_LABEL``            The item in the :class:`AuiToolBar` is a text label
        #          ``ITEM_SPACER``           The item in the :class:`AuiToolBar` is a spacer
        #          ``ITEM_SEPARATOR``        The item in the :class:`AuiToolBar` is a separator
        #          ``ITEM_CHECK``            The item in the :class:`AuiToolBar` is a toolbar check item
        #          ``ITEM_NORMAL``           The item in the :class:`AuiToolBar` is a standard toolbar item
        #          ``ITEM_RADIO``            The item in the :class:`AuiToolBar` is a toolbar radio item
        #          ========================  =============================
        #
        #         :param string `short_help_string`: this string is used for the tools tooltip;
        #         :param string `long_help_string`: this string is shown in the statusbar (if any) of the parent
        #          frame when the mouse pointer is inside the tool.
        #         :param PyObject `client_data`: whatever Python object to associate with the toolbar item.
        #         :param `target`: a custom string indicating that an instance of :class:`~wx.lib.agw.aui.framemanager.AuiPaneInfo`
        #          has been minimized into this toolbar.
        #          """

    # def GetToolState(self, toolId):
    def GetToolState(self, tool_id):
        """wx.lib.agw.aui.auibar.AuiToolBar.GetToolToggle indique si un outil est activé ou non.

        Args :
            tool_id (integer) : the toolbar item identifier.
        """
        # Cela s'applique uniquement à un outil qui a été spécifié comme outil toggle(à bascule).
        # return self.GetToolToggled(toolId)
        return self.GetToolToggled(tool_id)

    def SetToolBitmapSize(self, size):
        """Définit la taille par défaut de chaque bitmap d'outil. La taille bitmap par défaut est de 16 x 15 pixels.

        Args :
            size (wx.Size) : The size of the bitmaps in the toolbar.
        """
        self.__size = size
        # TODO : à remplacer par

    def GetToolBitmapSize(self):
        """Renvoie la taille du bitmap attendue par la barre d'outils.

        La taille bitmap par défaut est de 16 x 15 pixels.
        """
        return self.__size
        # TODO : à remplacer par wx.GetToolBitmapSize(self) inclut dans AuiToolBar
        return self.ToolBar.GetToolBitmapSize()
        return GetToolBitmapSize(self)

    def GetToolSize(self):
        """Renvoie la taille du bitmap.

        La taille bitmap par défaut est de 16 x 15 pixels.
        """
        return self.__size

    def SetMargins(self, *args):
        """
        Définissez les valeurs à utiliser comme marges pour la barre d'outils.

        Args :

            x (int) : marge gauche, marge droite et valeur de séparation inter-outils ;

            y (int) : marge supérieure, marge inférieure et valeur de séparation inter-outils.

        ou

            left (int) : la marge gauche de la barre d'outils;

            right (int) : la marge droite de la barre d'outils;

            top (int) : la marge supérieure de la barre d'outils;

            bottom (int) : la marge inférieure de la barre d’outils.
        """
        if len(args) == 2:
            super().SetMarginsXY(args[0], args[1])
        else:
            super().SetMargins(*args)

    # @staticmethod
    # def MakeDisabledBitmap(self, bitmap: wx.Bitmap) -> wx.Bitmap:
    def MakeDisabledBitmap(self, bitmap):
        """
        Crée une version en niveaux de gris d'un bitmap pour l'afficher en mode désactivé.

        Args :
            bitmap (wx.Bitmap) : Le bitmap à convertir.

        Returns :
            (wx.Bitmap) : Le bitmap converti en niveaux de gris.
        """
        # Penser à utiliser SetToolDisabledBitmap(self, tool_id, bitmap) qui
        # Définit le bitmap de l'outil désactivé pour l'outil identifié par tool_id.

        # Paramètres :

        # tool_id (entier) – l'identifiant de l'outil ;

        # bitmap (wx.Bitmap) – le nouveau bitmap désactivé pour l'élément de la barre d'outils.
        # Eviter que si bitmap.ConvertToImage() retourne un objet invalide, le retour plantera.
        # Sécurité : vérifier si le bitmap est bien un objet wx.Bitmap
        if isinstance(bitmap, str):
            log.error(
                "MakeDisabledBitmap a reçu une chaîne ('%s') au lieu d'un wx.Bitmap. Utilisation d'un bitmap nul.",
                bitmap,
            )
            return wx.NullBitmap
            # return bitmap
            # return artprovider.getBitmap(bitmap)

        if not bitmap or not bitmap.IsOk():
            log.error(
                "Le bitmap fourni est invalide ou None dans MakeDisabledBitmap"
            )
            return (
                wx.NullBitmap
            )  # Retourner un bitmap nul plutôt que None pour éviter des erreurs en aval
        else:
            # return bitmap.ConvertToImage().ConvertToGreyscale().ConvertToBitmap()
            try:
                return (
                    bitmap.ConvertToImage()
                    .ConvertToGreyscale()
                    .ConvertToBitmap()
                )
            except Exception as e:
                log.error(
                    "Erreur lors de la conversion du bitmap en niveaux de gris : %s",
                    e,
                )
                return bitmap


# class ToolBar(uicommandcontainer.UICommandContainerMixin, _Toolbar):
class ToolBar(_Toolbar, uicommandcontainer.UICommandContainerMixin):
    """
    Une classe qui représente une barre d'outils personnalisable dans l'interface utilisateur de Task Coach.

    Cette classe hérite de la classe _Toolbar et utilise la classe UICommand pour définir les commandes qui apparaissent sur la barre d'outils.

    La barre d'outils peut être personnalisée par l'utilisateur en utilisant le menu "Personnaliser" dans le menu "Affichage". Les choix de l'utilisateur sont enregistrés dans les préférences de l'application.

    La classe MainToolBar est une sous-classe de ToolBar qui est utilisée dans la fenêtre principale de Task Coach.
    """

    def __init__(self, window, settings, size: tuple = (32, 32)):
        """
        Initialise une nouvelle instance de la classe ToolBar.

        Args :
            window (Window) : La fenêtre parent de la barre d'outils.
            settings (Settings) : Les paramètres de configuration de l'application.
            size (tuple, optional) : La taille des icônes de la barre d'outils. La valeur par défaut est (32, 32).
        """
        log.debug(
            f"Initialisation de ToolBar dans la fenêtre parent : {type(window).__name__}, taille : {size}"
        )
        self.__window = window
        self.__settings = settings
        self.__visibleUICommands = list()
        self.__cache = None
        self.__customizeId = None
        # Définir la taille AVANT de charger la perspective ---
        self.__size = size
        super().__init__(window, style=wx.TB_FLAT | wx.TB_NODIVIDER)
        self.SetToolBitmapSize(size)
        if operating_system.isMac():
            # Extra margin needed because the search control is too high
            self.SetMargins(0, 7)
        # Maintenant loadPerspective peut accéder à self._size sans erreur
        self.loadPerspective(window.getToolBarPerspective())
        self.tools = []  # utiliser une liste pour stocker les outils

    def Clear(self):
        """Efface la barre d'outils et tous les contrôles qu'elle contient.

        Supprime tous les outils de AuiToolBar.
        Cette méthode est nécessaire car la méthode Clear de la classe AuiToolBar ne supprime pas les contrôles de la barre d'outils.
        """

        if self.__visibleUICommands:  # Peut-être aucun(None)
            for uiCommand in self.__visibleUICommands:
                log.debug(
                    "ToolBar.Clear : Suppression de l'élément UICommand %s",
                    uiCommand,
                )
                if uiCommand is not None and not isinstance(uiCommand, int):
                    uiCommand.unbind(self, uiCommand.id)

        idx = 0
        log.debug(
            "ToolBar.Clear : Nettoyage de la barre d'outils existante (Clear)"
        )
        while idx < self.GetToolCount():
            item = self.FindToolByIndex(idx)
            if item is not None and item.GetKind() == aui.ITEM_CONTROL:
                item.window.Destroy()
                self.DeleteToolByPos(idx)
            else:
                idx += 1

        super().Clear()

    def detach(self):
        self.Clear()
        self.__visibleUICommands = self.__cache = None

    # def getToolIdByCommand(self, commandName: str) -> int:
    def getToolIdByCommand(self, commandName):
        # Tracer la récupération d’un ID :
        log.debug(
            "ToolBar.getToolIdCommand : Recherche de l'ID d'outil pour la commande '%s'",
            commandName,
        )

        if commandName == "EditToolBarPerspective":
            return self.__customizeId

        for uiCommand in self.__visibleUICommands:
            if (
                isinstance(uiCommand, base_uicommand.UICommand)
                and uiCommand.uniqueName() == commandName
            ):
                return uiCommand.id
        return wx.ID_ANY

    # def _filterCommands(self, perspective: str, cache: bool = True) -> list:
    def _filterCommands(self, perspective, cache=True):
        commands = list()
        if perspective:
            index = dict(
                [
                    (command.uniqueName(), command)
                    for command in self.uiCommands(cache=cache)
                    if command is not None and not isinstance(command, int)
                ]
            )
            index["Separator"] = None
            index["Spacer"] = 1
            for className in perspective.split(
                ","
            ):  # TODO : avec ou sans espace ?
                if className in index:
                    commands.append(index[className])
        else:
            commands = list(self.uiCommands(cache=cache))
        return commands

    # def loadPerspective(self, perspective: str, customizable=True, cache=True):
    def loadPerspective(self, perspective, customizable=True, cache=True):
        log.debug(
            "ToolBar.loadPerspective : Chargement de la perspective de la barre d'outils : %s",
            perspective,
        )
        self.Clear()  # ?

        commands = self._filterCommands(perspective, cache=cache)
        self.__visibleUICommands = commands[:]

        if customizable:
            if 1 not in commands:
                commands.append(1)
            from taskcoachlib.gui.dialog.toolbar import ToolBarEditor

            log.debug(
                "ToolBar.loadPerspective : Ajout du bouton de personnalisation de la barre d'outils"
            )
            uiCommand = uicommand.EditToolBarPerspective(
                self, ToolBarEditor, settings=self.__settings
            )
            commands.append(uiCommand)
            self.__customizeId = uiCommand.id
        if operating_system.isMac():
            commands.append(None)  # Errr...

        log.debug(
            "ToolBar.loadPerspective : Commandes filtrées : %s",
            [str(c) for c in commands],
        )
        # Une fois les commandes créées par UICommands() et MainWindow.createToolBarUICommands()
        self.appendUICommands(*commands)
        self.Realize()  # Réalise la barre d'outils. Cette fonction doit être appelée après avoir ajouté des outils.
        # pour les faire apparaître !

    # def perspective(self) -> str:
    def perspective(self):
        """
        Retourne la perspective actuelle de la barre d'outils sous forme de chaîne de caractères.

        La perspective est une chaîne de caractères qui représente
        les commandes actuellement affichées sur la barre d'outils,
        dans l'ordre dans lequel elles apparaissent.
        """
        names = list()
        for uiCommand in self.__visibleUICommands:
            if uiCommand is None:
                names.append("Separator")
            elif isinstance(uiCommand, int):
                names.append("Spacer")
            else:
                names.append(uiCommand.uniqueName())
        return ",".join(names)  # TODO : Utiliser ", ", non ?

    # def savePerspective(self, perspective: str):
    def savePerspective(self, perspective):
        """
        Enregistre la perspective actuelle de la barre d'outils dans les préférences de l'application.

        Args :
            perspective (str) : La perspective à enregistrer.
        """
        self.loadPerspective(perspective)
        self.__window.saveToolBarPerspective(perspective)

    # def uiCommands(self, cache: bool = True):
    def uiCommands(self, cache=True):
        """
        Retourne une liste de commandes UI à afficher sur la barre d'outils.

        Cette méthode utilise la méthode createToolBarUICommands de la classe parent UICommandContainerMixin pour générer la liste de commandes UI.
        """
        if self.__cache is None or not cache:
            # La méthode suivante est appelée pour
            # Obtenir la liste des commandes UI à afficher sur la barre d’outils :
            self.__cache = self.__window.createToolBarUICommands()
            # Cela signifie que c’est la fenêtre principale (MainWindow) qui
            # fournit les commandes via sa méthode createToolBarUICommands()
            # qui retourne explicitement une liste d’instances de UICommand.
        return self.__cache

    def visibleUICommands(self):
        """
        Retourne une liste des commandes UI actuellement affichées sur la barre d'outils.
        """
        return self.__visibleUICommands[:]

    def getDefaultPerspective(self):
        """Get the default toolbar perspective from settings."""
        if hasattr(self.__window, "settingsSection"):
            section = self.__window.settingsSection()
        else:
            # MainWindow uses "view" section
            section = "view"
        return self.__settings.getDefault(section, "toolbarperspective")

    def AppendSeparator(self):
        """
        Ajoute un séparateur à la barre d'outils pour espacer les groupes d'outils.

        This little adapter is needed for
        uicommand.UICommandContainerMixin.appendUICommands"""
        self.AddSeparator()

    # def AppendStretchSpacer(self, proportion: int):
    def AppendStretchSpacer(self, proportion):
        """
        Ajoute un espaceur extensible à la barre d'outils.

        Args :
            proportion (int) : La proportion de l'espaceur extensible.
        """
        self.AddStretchSpacer(proportion)

    def appendUICommand(self, uiCommand):
        """
        Ajoute une commande UI à la barre d'outils.

        Args :
            uiCommand (uicommand.UICommand) : La commande UI à ajouter.
        """
        # # Cette méthode distingue :
        # #     - les None ➜ séparateurs
        # #     - les int ➜ espaceurs
        # #     - les objets hérités de UICommand ➜ ajoutés à la barre avec appendToToolBar()
        # # Déboggage :
        # # Ajoutez des débogage pour vérifier les paramètres
        # log.debug(
        #     f"ToolBar.appendUICommand : Adding UI Command: {uiCommand.menuText}"
        # )
        # # 1. Récupération de l'icône
        # # forcer la conversion de l'image juste avant l'ajout :
        # bmp = uiCommand.bitmap  # TypeError: 'str' object is not callable
        # if isinstance(bmp, str):
        #     # if isinstance(uiCommand.bitmap(), str):
        #     # On force la conversion si on a encore une chaîne
        #     from taskcoachlib.gui import artprovider
        #
        #     bmp = artprovider.IconProvider().getIconFromArtProvider(  # Attention il faut obtenir un Bitmap, pas une chaîne ni un wx.Icon
        #         bmp, self.__size
        #     )
        #     # bmp = artprovider.getBitmap(uiCommand.bitmap(), self._size)
        # else:
        #     bmp = uiCommand.bitmap()
        #
        # # 2. Détermination du type de bouton (Correction actuelle)
        # # On vérifie si la commande a une méthode kind(), sinon normal.
        # if hasattr(uiCommand, "kind") and callable(uiCommand.kind):
        #     kind_of_uicommand = uiCommand.kind()
        # else:
        #     kind_of_uicommand = wx.ITEM_NORMAL
        # # # Remplacer self.kind(uiCommand) par l'accès direct au type de la commande
        # # # Si uiCommand est un objet UICommand standard :
        # # kind_of_uicommand = (
        # #     uiCommand.kind() if hasattr(uiCommand, "kind") else wx.ITEM_NORMAL
        # # )
        # # Pourquoi cette erreur ?
        # # Dans les versions précédentes ou d'autres implémentations de barres d'outils
        # # (comme wx.ToolBar standard), il y avait parfois une fonction helper nommée kind.
        # # Ici, vous utilisez AuiToolBar, et il semble que la méthode kind ait été oubliée dans la classe
        # # ou que vous ayez copié un bout de code d'une classe parente sans la définir.
        # # Ensuite on utilise bmp au lieu de uiCommand.bitmap()
        # # 3. Ajout à la barre d'outils AUI
        # self.AddLabelTool(
        #     # uiCommand.id(),
        #     uiCommand.id,
        #     # uiCommand.menuText(),
        #     uiCommand.menuText,
        #     bmp,
        #     bmp,
        #     # self.kind(uiCommand),
        #     kind_of_uicommand,
        #     shortHelp=uiCommand.helpText,
        #     longHelp=uiCommand.getHelpText(),
        # )
        # # vous garantissez que AddLabelTool reçoit un objet wx.Bitmap (ou wx.NullBitmap), et jamais une str. L'appel à .IsOk() ne plantera donc plus.

        try:
            return uiCommand.appendToToolBar(self)
        except Exception as e:
            log.error(
                f"ToolBar.appendUICommand : Erreur lors de l'ajout de la commande {uiCommand} : {e}",
                stack_info=True,
            )
            raise
        # # Implémentation de la méthode appendUICommand
        # toolId = len(self.tools)  # Simule un ID unique pour l'outil
        # # self.__visibleUICommands[toolId] = uiCommand
        # self.tools.append(uiCommand)
        #
        # # Ajoutez des débogage pour vérifier que l'outil a été ajouté avec succès
        # log.debug(f"ToolBar.appendUICommand : Tool {uiCommand.menuText} ajouté avec l' ID: {toolId} retourné.")
        #
        # return toolId

    def GetToolPos(self, toolId):
        # if toolId in self.tools:
        #     return self.tools.index(toolId)
        if 0 <= toolId < len(self.tools):
            return toolId

        return wx.NOT_FOUND


class MainToolBar(ToolBar):
    """
    Une sous-classe de ToolBar qui est utilisée dans la fenêtre principale de Task Coach.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialise une nouvelle instance de la classe MainToolBar, utilisée dans la fenêtre principale.

        Args :
            *args : Les arguments positionnels à passer à la méthode __init__ de la classe parent ToolBar.
            **kwargs : Les arguments par mot-clé à passer à la méthode __init__ de la classe parent ToolBar.
        """
        super().__init__(*args, **kwargs)
        self.Bind(
            wx.EVT_SIZE, self._OnSize
        )  # Je pense qu'il y a une erreur ici !
        self._is_resizing = False
        self._resize_timer = None
        self._resize_delay_ms = 50  # régler si nécessaire
        # Dernière taille initialisé avec la taille actuelle de la barre d'outils.
        # Cela nous servira de point de référence pour déterminer si un changement "véritable" s'est produit.
        # Permet de s'assurer qu'un nouvel événement de taille n'est planifié
        # que si la taille de la barre d'outils a effectivement changé,
        # plutôt que d'être déclenché par une cascade d'événements à partir d'un seul changement de taille.
        self._last_size = self.GetSize()

    # def _OnSize(self, event):
    #     """
    #     Gestionnaire d'événements pour le redimensionnement de la fenêtre.
    #
    #     Cette méthode ajuste la taille de la barre d'outils en fonction de la taille de la fenêtre parent.
    #
    #     Args :
    #         event (wx.SizeEvent) : L'événement de redimensionnement.
    #     """
    #     event.Skip()
    #     current_size = self.GetSize()
    #     if not self._is_resizing:
    #         return
    #     # # On Windows XP, the sizes are off by 1 pixel. I fear that this value depends
    #     # # on the user's config so let's take some margin.
    #     # if abs(event.GetSize()[0] - self.GetParent().GetClientSize()[0]) >= 10:
    #
    #     # Comparer la taille actuelle avec la dernière taille enregistrée :
    #     if current_size != self._last_size:
    #         # Mise à jour vers la nouvelle taille pour éviter les appels suivants si la taille reste la même.
    #         self._last_size = current_size
    #         # # A surveiller : Ces appels à wx.CallAfter sont parfois asynchrones et silencieux en cas d'échec.
    #         self._is_resizing = True
    #         log.debug(
    #             f"MainToolBar._OnSize : appel wx.CallAfter() sur self.getParent()={self.GetParent()}."
    #         )
    #         # CallAfter ne sera exécuté que si la taille a effectivement changé.
    #         wx.CallAfter(
    #             self.GetParent().SendSizeEvent
    #         )  # This function sends a dummy size event to the window allowing it to re-layout its children positions. Ne fonctionne pas sur MainWindow !
    #         log.debug(
    #             "MainToolBar._OnSize : L'appel wx.CallAfter(GetParent.SendSizeEvent) est passé."
    #         )
    #     self._is_resizing = False
    #     # # Voici une ventilation du problème :
    #     # #
    #     # # Lorsqu’un événement de taille se produit, la méthode _OnSize est déclenchée.
    #     # # Le code vérifie si la largeur de la barre d’outils est significativement
    #     # # différente de la largeur du client de sa fenêtre parente (une différence de 10 pixels ou plus).
    #     # #
    #     # # Si la condition est remplie, wx. CallAfter est utilisé pour planifier un nouveau SendSizeEvent pour la fenêtre parente.
    #     # #
    #     # # À son tour, ce SendSizeEvent déclenchera probablement à nouveau la méthode _OnSize, car la taille de la fenêtre a changé.
    #     # #
    #     # # Cela crée une boucle récursive : un événement size appelle _OnSize, qui planifie ensuite un autre événement size, et ainsi de suite.
    #     # #
    #     # # Le commentaire dans le code lui-même suggère que ce comportement était une solution de contournement
    #     # # pour un problème spécifique sous Windows XP, où les tailles étaient décalées d’un pixel.
    #     # # Cependant, dans votre environnement actuel, il semble que la méthode s’appelle elle-même à plusieurs reprises,
    #     # # ce qui conduit à la « boucle infinie » que vous observez.

    def _OnSize(self, event):
        """
        Gestionnaire d'événements pour le redimensionnement de la fenêtre.

        Cette méthode ajuste la taille de la barre d'outils en fonction de la taille de la fenêtre parent.

        Args :
            event (wx.SizeEvent) : L'événement de redimensionnement.
        """
        # log.debug(
        #     "MainToolBar._OnSize : appelé pour remettre la ToolBar à la taille de la fenêtre."
        # )
        event.Skip()
        current_size = self.GetSize()
        # if self._is_resizing:
        #     return
        # Comparer la taille actuelle avec la dernière taille enregistrée :
        # if current_size == self._last_size:
        #     self._resize_timer.

        # if current_size != self._last_size:
        #     # Mise à jour vers la nouvelle taille pour éviter les appels suivants si la taille reste la même.
        #     self._last_size = current_size
        #
        #     self._is_resizing = True
        #     log.debug(
        #         f"MainToolBar._OnSize : appel wx.CallAfter() sur self.getParent()={self.GetParent()}."
        #     )
        #     # wx.CallAfter(self._call_parent_send_size_and_unset_flag)
        #     log.debug(
        #         "MainToolBar._OnSize : L'appel wx.CallAfter(GetParent.SendSizeEvent) est passé."
        #     )
        if self._resize_timer is not None:
            # réarme le timer (cancel/restart) : CallLater retourne un objet, on l'arrêtera
            self._resize_timer.Stop()
            self._resize_timer = None
            # log.debug(
            #     "MainToolBar._OnSize: relance le timer pour le redimensionnement."
            # )
            self._resize_timer = wx.CallLater(
                self._resize_delay_ms, self._do_parent_send_size
            )
        # self._is_resizing = False
        # log.debug("MainToolBar._OnSize : terminé !")

    def _do_parent_send_size(self):
        self._resize_timer = None
        try:
            # log.debug(
            #     "MainToolBar._do_parent_send_size :  met à jour la nouvelle taille de fenêtre."
            # )
            self.GetParent().SendSizeEvent()
        except Exception as e:
            log.error(
                "MainToolBar._do_parent_send_size : Erreur en appelant SendSizeEvent depuis _do_parent_send_size: %s",
                e,
            )
        # log.debug(
        #     "MainToolBar._do_parent_send_size : ToolBar et fenêtre redimensionnées !"
        # )

    def _call_parent_send_size_and_unset_flag(self):
        try:
            # self.GetParent().SendSizeEvent()
            self._do_parent_send_size()
        finally:
            self._is_resizing = False
            # log.debug(
            #     "MainToolBar._call_parent_send_size_and_unset_flag : _is_resizing remis à False après SendSizeEvent !"
            # )

    def Realize(self):
        """wx.lib.agw.aui.auibar.AuiToolBar.Realize Réalise la barre d'outils.

        Cette fonction doit être appelée après avoir ajouté des outils.
        """
        #  limiter ou conditionner les CallAfter :
        #  si vous appelez SetMinSize et ensuite SendSizeEvent,
        #  assurez-vous que ces deux appels ne se déclenchent
        #  pas mutuellement en boucle sur certains systèmes.
        # voir wx.lib.agw.aui.auibar.AuiToolBar.SetAGWWindowStyleFlag
        self._agwStyle &= ~aui.AUI_TB_NO_AUTORESIZE
        super().Realize()
        self._agwStyle |= aui.AUI_TB_NO_AUTORESIZE
        # log.debug("MainToolBar.Realize : appel wx.CallAfter().")
        # # wx.CallAfter(self.GetParent().SendSizeEvent)
        # wx.CallAfter(self._call_parent_send_size_and_unset_flag)
        wx.CallAfter(self._do_parent_send_size)
        # log.debug("MainToolBar.Realize : L'appel wx.CallAfter(SendSizeEvent) est passé.")
        # w, h = self.GetParent().GetClientSizeTuple()
        w, h = self.GetParent().GetClientSize()
        # log.debug("MainToolBar.Realize : appel CallAfter(self.SetMinSize).")
        wx.CallAfter(self.SetMinSize, (w, -1))
        # Après les appels mise à jour pour nous assurer que notre suivi de taille est correct dès le départ.
        self._last_size = self.GetSize()
        # log.debug("MainToolBar.Realize : L'appel wx.CallAfter(SetMinSize) est passé.")
        # log.debug(
        #     "MainToolBar.Realize : Les appels wx.CallAfter(SendSizeEvent & SetMinSize) sont passé avec succès !"
        # )
