# Points clés et considérations :
#
# Gestion des images :
# L’exemple comprend des espaces réservés pour le chargement d’images à l’aide de PIL (Pillow).
# Vous devrez installer Pillow (pip install Pillow) et adapter la logique de chargement
# et de désactivation des images à votre format d’image spécifique
# et à vos exigences de désactivation.

# createToolBarUICommands :
# Cette méthode, à l’origine dans MainWindow, devra être adaptée
# pour créer des instances de vos sous-classes UICommand compatibles avec Tkinter.
#
# Boîte de dialogue de personnalisation :
# La fonctionnalité ToolBarEditor doit être complètement réimplémentée
# à l’aide des boîtes de dialogue Tkinter.
# uniqueName :
# assurez-vous que vos sous-classes UICommand disposent d’une méthode uniqueName
# qui renvoie un identificateur de chaîne pour chaque commande.
# Ceci est utilisé pour conserver la perspective de la barre d’outils.
# Paramètres :
# L’objet settings (à l’origine pour stocker les paramètres spécifiques à wxPython)
# devra être adapté pour stocker et récupérer les données de configuration
# de la barre d’outils d’une manière compatible avec Tkinter
# (par exemple, en utilisant tkinter.filedialog
# ou un fichier de paramètres personnalisés).

# La solution : Séparer le parent (widget) du contrôleur (logique)
#
# Le constructeur ToolBar utilise son premier argument window à deux fins :
#     Comme parent pour le widget ttk.Frame (dans super().__init__(window, **kwargs)).
#     Comme contrôleur pour obtenir la logique métier (comme getToolBarPerspective()).
#
# Le parent (visuel) doit être self._sizer.
# Le contrôleur (logique) doit être self (l'instance de Viewer,
# ex: Noteviewer, qui a bien la méthode getToolBarPerspective définie dans basetk.py).
#
# Nous devons modifier ToolBar pour qu'il accepte ces deux informations distinctement.
# Modifie le constructeur __init__ de la classe ToolBar
# pour accepter un parent (pour Tkinter) et une window (pour la logique).
import tkinter as tk
from tkinter import ttk
import logging

# from PIL import Image, ImageTk # If you need more image format support
from taskcoachlib.guitk.uicommand import uicommandtk
from taskcoachlib.guitk.uicommand import uicommandcontainertk

# from taskcoachlib.guitk.dialog.toolbartk import ToolBarEditor  # Circular import

log = logging.getLogger(__name__)


# class ToolBar(ttk.Frame, uicommandcontainertk.UICommandContainerMixin):
class ToolBar(ttk.LabelFrame, uicommandcontainertk.UICommandContainerMixin):
    """A class that represents a customizable toolbar in the Task Coach UI."""

    # La classe ToolBar hérite de ttk.LabelFrame et de uicommandcontainertk.UICommandContainerMixin.
    # Elle reçoit un parent et un window (qui est le contrôleur) lors de son initialisation.
    # Elle appelle loadPerspective pour charger la configuration de la barre d'outils.
    # Dans loadPerspective, la méthode appendUICommands est appelée pour ajouter les commandes à la barre d'outils.

    # def __init__(self, window, settings, size=(32, 32), **kwargs):
    # CHANGEMENT : La signature accepte 'parent' (pour le widget) et 'window' (pour la logique)
    def __init__(self, parent, window, settings, size=(32, 32), **kwargs):
        # super().__init__(window, **kwargs)
        # CHANGEMENT : On passe 'parent' au constructeur de ttk.Frame
        super().__init__(parent, text="ToolBar", **kwargs)
        # log.debug(f"Initializing ToolBar in parent window: {type(window).__name__}, size: {size}")
        log.debug(
            f"ToolBar __init__ : initialise dans le parent widget: {parent}{type(parent).__name__}, controller window: {type(window).__name__}, avec des icones de taille: {size}"
        )
        self.parent = parent
        self.__window = window  # On garde 'window' pour la logique
        self.__settings = settings
        self.__visibleUICommands = []
        self.__cache = None
        self.__customizeId = None
        self.tool_bitmap_size = size  # Store the tool bitmap size

        self.tools = []  # Use a list to store the tools
        # self.load_perspective(window.getToolBarPerspective())
        # Cet appel fonctionne maintenant car self.__window est le Viewer
        self.loadPerspective(
            self.__window.getToolBarPerspective()
        )  # Appeler la méthode sur le contrôleur
        self.configure(
            relief="raised", borderwidth=1
        )  # Add border for visual appearance
        # La "bonne pratique" est la suivante :
        # si tu stockes une variable (window) dans une variable d'instance (self.__window),
        # c'est parce que tu as l'intention d'utiliser self.__window partout ailleurs dans la classe.
        #
        # Utiliser self.__window.get...() au lieu de window.get...() est plus cohérent.
        # Cela montre que la barre d'outils dépend de sa variable d'instance (self.__window) pour fonctionner,
        # et non d'une variable locale qui n'existe que dans __init__.
        # C'est plus propre et plus facile à maintenir si jamais on doit réorganiser le code.

    def loadPerspective(self, perspective, customizable=True, cache=True):
        """
        Charge une perspective de la barre d'outils à partir d'une chaîne de caractères.

        Args :
            perspective : Perspective de la barre d'outils sous forme de chaîne de caractères.
            customizable : Valeur booléenne indiquant si la barre d'outils est personnalisable.
            cache : Valeur booléenne indiquant si la mise en cache des commandes UI est activée.

        Returns :
            None
        """
        log.debug(
            f"ToolBar.load_perspective: Commence la toolbar avec la liste de perspective: {perspective}"
        )
        self.clear()
        commands = self._filterCommands(perspective, cache=cache)
        log.debug(
            f"ToolBar.load_perspective: La liste des commandes filtrées sont: {commands}"
        )
        self.__visibleUICommands = commands[:]

        if customizable:
            if 1 not in commands:
                commands.append(1)

                # from taskcoachlib.gui.dialog.toolbar import ToolBarEditor  #Needs to be converted
            log.debug(
                "ToolBar.loadPerspective : Ajout du bouton de personnalisation de la barre d'outils"
            )
            from taskcoachlib.guitk.dialog.toolbartk import ToolBarEditor

            uiCommand = (
                uicommandtk.EditToolBarPerspective(  # Needs to be converted
                    self, ToolBarEditor, settings=self.__settings
                )
            )
            commands.append(uiCommand)
            # self.__customizeId = uiCommand.id
            # if operating_system.isMac():
            #     commands.append(None)  # Errr...
        # self.add_separator()
        self.appendUICommands(*commands)
        log.debug(
            f"ToolBar.loadPerspective : Fin de la configuration de la barre d'outils:{self} qui devrait contenir les commandes: {self.__visibleUICommands}."
        )

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
        return ",".join(names)  # Utiliser ", ", non ?

    # def savePerspective(self, perspective: str):
    def savePerspective(self, perspective):
        """
        Enregistre la perspective actuelle de la barre d'outils dans les préférences de l'application.

        Args :
            perspective (str) : La perspective à enregistrer.
        """
        self.loadPerspective(perspective)
        self.__window.saveToolBarPerspective(perspective)

    def _filterCommands(
        self, perspective, cache=True
    ):  # Identique à la version wx.
        commands = []
        if perspective:
            index = {
                command.uniqueName(): command
                for command in self.uiCommands(cache=cache)
                if command is not None and not isinstance(command, int)
            }
            index["Separator"] = None
            index["Spacer"] = 1

            for class_name in perspective.split(", "):
                if class_name in index:
                    commands.append(index[class_name])
                else:
                    commands = list(self.uiCommands(cache=cache))
        return commands

    def clear(self):
        """Clears the toolbar and all its widgets."""
        for widget in self.winfo_children():
            widget.destroy()
        self.__visibleUICommands = []

    def detach(self):
        self.clear()
        self.__visibleUICommands = self.__cache = None

    # def appendUICommands(self, *commands):  # Méthode de appendUICommands ! Contenu dans UICommandContainerMixin
    #     """Appends multiple UI commands to the toolbar."""
    #     for command in commands:
    #         self.appendUICommand(command)

    def appendUICommand(self, ui_command):
        """Appends a single UI command to the toolbar."""
        if ui_command is None:
            # Separator
            # ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=2)
            ttk.Separator(self, orient=tk.HORIZONTAL).pack(
                side=tk.LEFT, padx=2
            )
            return
        # elif isinstance(ui_command, int):
        if isinstance(ui_command, int):
            # Spacer (using an empty label with weight)
            spacer = ttk.Label(self, text="")  # TODO : obtenir les images !
            spacer.pack(
                side=tk.LEFT, expand=True, fill=tk.X
            )  # Expand and fill
            return
        # else:
        # UICommand (create a button)
        try:
            before_children = list(self.winfo_children())
            # # Adapt appendToToolBar to create ttk.Button
            # button = ui_command.appendToToolBar(self)  # Pass the toolbar instance
            # # button = ttk.Button()
            # # button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2, pady=2)
            #
            # # On stocke l'ID dans le widget Tkinter lui-même pour le retrouver plus tard
            # button.ui_command_id = ui_command.id
            widget = ui_command.appendToToolBar(self)  # peut renvoyer None

            if widget is None:
                # Tentative de détection du widget créé (dernier nouvel enfant)
                after_children = list(self.winfo_children())
                new_children = [
                    w for w in after_children if w not in before_children
                ]
                if new_children:
                    widget = new_children[-1]
                    log.warning(
                        "ToolBar.appendUICommand : détecte un nouveau widget créé par appendToToolBar."
                    )
                elif hasattr(ui_command, "_widget"):
                    widget = getattr(ui_command, "_widget")
                    log.warning(
                        "ToolBar.appendUICommand : récupère ui_command._widget."
                    )
                else:
                    log.error(
                        "ToolBar.appendUICommand : appendToToolBar a renvoyé None et aucun widget détecté pour %r",
                        ui_command,
                    )
                    return

                    # Ne pas écrire directement sur l'objet widget (sécurisé):
            try:
                widget.ui_command_id = ui_command.id
            except Exception:
                # Widget ne permet pas nouveaux attributs -> garder le mapping séparé
                if not hasattr(self, "_tool_by_id"):
                    self._tool_by_id = {}
                self._tool_by_id[ui_command.id] = widget
                log.debug(
                    "ToolBar.appendUICommand : appendToToolBar(%r) returned %r",
                    ui_command,
                    widget,
                )

            # self.tools.append(button)
            self.tools.append(widget)
            log.info(
                f"ToolBar.appendUICommand : Les UICommands de ToolBar sont {self.tools}."
            )
        except Exception as e:
            log.error(
                f"ToolBar.appendUICommand : Error adding command {ui_command}: {e}"
            )
            raise
        # if button:  # TODO : gérer le bouton ?
        #     return button

    def uiCommands(self, cache=True):  # Identique à la version wx
        """Returns a list of UI commands to display on the toolbar."""
        if self.__cache is None or not cache:
            self.__cache = (
                self.__window.createToolBarUICommands()
            )  # needs to be converted
        return self.__cache

    def visibleUICommands(self):  # Identique à v. wx
        """Returns a list of the UI commands currently displayed on the toolbar."""
        return self.__visibleUICommands[:]

    def add_separator(self):
        # def appendSeparator(self):
        """
        Ajoute un séparateur à la barre d'outils.
        Cette méthode doit être implémentée par la classe qui utilise ce mixin.
        """
        # self.add_separator()
        # ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=2)
        # ttk.Separator(self, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, padx=2)  # Ne fonctionne pas directement ici !
        # ttk.Separator(self, orient=tk.HORIZONTAL).pack(
        #     side=tk.TOP, fill=tk.X, pady=2
        # )
        ttk.Separator(self, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, pady=2
        )  # SUPER !
        # raise NotImplementedError("La méthode 'AppendSeparator' doit être implémentée par la classe qui utilise ce mixin.")
        # raise NotImplementedError("La méthode 'Add_h_Separator' doit être implémentée par la classe qui utilise ce mixin.")

    def getToolWidget(self, tool_id):
        """Retrouve le widget dans la liste self.tools par son ID."""
        for tool in self.tools:
            # On vérifie si c'est un widget (pas un séparateur) et s'il a le bon ID
            if (
                hasattr(tool, "ui_command_id")
                and tool.ui_command_id == tool_id
            ):
                return tool
        return None

    def GetToolState(self, tool_id):
        """
        Vérifie si l'outil est enfoncé.
        GetToolWidget indique si un outil est activé ou non.

        Args :
            toolId/tool_id (integer) : the toolbar item identifier.
        """
        widget = self.getToolWidget(tool_id)
        if widget:
            return widget.cget("relief") == "sunken"
        return False

    def ToggleTool(self, tool_id, toggle):
        """Change le relief du widget trouvé dans la liste."""
        widget = self.getToolWidget(tool_id)
        if widget:
            widget.config(relief="sunken" if toggle else "raised")


# classe de base_uicommand.py ! : à transférer !
# class UICommand:  # Base class, needs conversion
#     """Base class for UI commands."""
#     def __init__(self, toolbar, command=None, tooltip=None, image_path=None):
#         self.toolbar = toolbar
#         self.command = command
#         self.tooltip = tooltip
#         self.image_path = image_path
#         self.normal_image = None   # To store the normal image
#         self.disabled_image = None  # To store the disabled image
#         self.button = None
#
#     def appendToToolBar(self, toolbar):
#         """Creates a ttk.Button for the toolbar."""
#         # Load the image
#         # image = Image.open(self.image_path)
#         # self.normal_image = ImageTk.PhotoImage(image) # Store the normal image
#
#         # # Create a disabled version (e.g., grayscale)
#         # disabled_image = image.convert('L')  # Convert to grayscale
#         # self.disabled_image = ImageTk.PhotoImage(disabled_image) # Store the disabled image
#
#         button = ttk.Button(toolbar,
#                             # image=self.normal_image,  # Use the normal image initially
#                             state=tk.NORMAL,        # Start as enabled
#                             command=self.do_command,
#                             # compound=tk.TOP          # To put image above text
#                             )
#
#         button.pack(side=tk.LEFT, padx=1, pady=1)  # Pack the button into the toolbar
#         self.button = button
#
#         return button  # Return the button instance
#
#     def do_command(self):
#         """Executes the command associated with the UI command."""
#         if self.command:
#             self.command()

# Example Usage (in your main application window):
# self.toolbar = ToolBar(self, self.settings, relief=tk.RAISED, bd=2)
# self.toolbar.pack(side=tk.TOP, fill=tk.X)
