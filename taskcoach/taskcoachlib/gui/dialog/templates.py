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

Classe principale : TemplatesDialog

Cette classe implémente une boîte de dialogue pour la gestion des modèles de tâches dans l'application Task Coach. Elle permet de visualiser, modifier et supprimer des modèles de tâches existants, ainsi que d'en créer de nouveaux.

Fonctionnalités principales

    Affichage d'une liste d'arborescence pour parcourir les modèles de tâches.
    Edition des propriétés d'un modèle de tâche sélectionné (sujet, dates de début, d'échéance, d'achèvement et de rappel).
    Suppression d'un modèle de tâche sélectionné.
    Déplacement d'un modèle de tâche vers le haut ou le bas dans la liste.
    Ajout d'un nouveau modèle de tâche.
    Sauvegarde des modifications apportées aux modèles de tâches.

Classes et méthodes utilisées

    TimeExpressionEntry : Une classe dérivée de wx.TextCtrl permettant la saisie et la validation d'expressions temporelles.
    createTemplateList : Crée la liste d'arborescence pour afficher les modèles de tâches.
    createTemplateEntries : Crée les champs d'édition pour les propriétés d'un modèle de tâche.
    enableEditPanel : Active ou désactive les champs d'édition en fonction de la sélection d'un modèle.
    appendTemplate : Ajoute un modèle de tâche et ses enfants à la liste d'arborescence.
    onValueChanged : Gère les modifications apportées aux champs d'édition d'un modèle de tâche.
    OnSelectionChanged : Gère la sélection d'un modèle de tâche dans la liste, met à jour les champs d'édition et active/désactive les boutons de suppression et de déplacement.
    onDelete : Supprime le modèle de tâche sélectionné.
    OnUp : Déplace le modèle de tâche sélectionné vers le haut dans la liste.
    OnDown : Déplace le modèle de tâche sélectionné vers le bas dans la liste.
    onAdd : Ajoute un nouveau modèle de tâche vide à la liste.
    ok : Sauvegarde les modifications apportées aux modèles de tâches lors de la validation de la boîte de dialogue.

Méthodes liées à l'interface utilisateur :

    createTemplateList, createTemplateEntries, createButton : Ces méthodes sont responsables de la construction de l'interface graphique de la boîte de dialogue, en créant les différents éléments tels que la liste d'arborescence, les champs de saisie et les boutons.
    enableEditPanel : Active ou désactive les champs d'édition en fonction de la sélection de l'utilisateur.
    appendTemplate : Ajoute un nouveau nœud à l'arbre des modèles de tâches.

Méthodes liées à la gestion des modèles de tâches :

    onValueChanged, OnSelectionChanged : Ces méthodes gèrent les événements utilisateur, tels que la modification du contenu d'un champ de saisie ou la sélection d'un élément dans la liste. Elles mettent à jour l'état interne de l'application en conséquence.
    onDelete, OnUp, OnDown, onAdd : Ces méthodes permettent à l'utilisateur de modifier la structure de l'arbre des modèles de tâches en supprimant, déplaçant ou ajoutant des éléments.
    ok : Cette méthode est appelée lorsque l'utilisateur clique sur le bouton "OK" de la boîte de dialogue. Elle sauvegarde les modifications apportées aux modèles de tâches.
"""
import logging

import wx
from taskcoachlib.domain.task import Task
from taskcoachlib import persistence, operating_system
from taskcoachlib.persistence import templatelist
from taskcoachlib.i18n import _
from taskcoachlib.thirdparty.deltaTime import nlTimeExpression
from wx.lib import sized_controls

log = logging.getLogger(__name__)


class TimeExpressionEntry(wx.TextCtrl):
    """Une classe dérivée de wx.TextCtrl permettant la saisie et la validation
    d'expressions temporelles (par exemple, "demain", "dans 2 jours", "14h").

    Elle fournit une indication visuelle (couleur de fond) si l'expression
    saisie n'est pas une expression temporelle valide.
    """

    @staticmethod
    def isValid(value):
        """
        Vérifie si la chaîne de caractères fournie est une expression temporelle valide.

        Une expression vide est considérée comme valide.

        Args :
            value (str) : La chaîne de caractères à valider comme expression temporelle.

        Returns :
            (bool) : True si l'expression est valide ou vide, False sinon.
        """
        if value:
            try:
                # Tente d'analyser la chaîne comme une expression temporelle
                # (nécessite l'importation de nlTimeExpression)
                res = nlTimeExpression.parseString(value)
            except Exception as e:
                # Enregistre l'exception si l'analyse échoue
                logging.exception(f"Exception: {e}", exc_info=True)
                return False  # pylint: disable=W0702 L'expression est invalide
            return "calculatedTime" in res  # Vérifie si le résultat contient un temps calculé
        return True  # Une chaîne vide est toujours valide.

    def _onTextChanged(self, event):
        """
        Gère l'événement de modification du texte dans le contrôle.

        Met à jour la couleur de fond du contrôle pour indiquer
        si l'expression temporelle saisie est valide ou non.

        Args :
            event (wx.EVT_TEXT) : L'événement de modification du texte.
        """
        event.Skip()  # Permet à d'autres gestionnaires d'événements de traiter l'événement
        self.SetBackgroundColour(
            self.__defaultColor  # Couleur par défaut si valide
            if self.isValid(self.GetValue())  # Vérifie la validité de la valeur actuelle
            else self.__invalidColor  # Couleur d'erreur si invalide
        )

    # Déplacer _onTextChanged et isValid avant __init__ pour s'assurer
    # qu'elles soient liées à des événements dans __init_.
    def __init__(self, *args, **kwargs):
        """
        Initialise une nouvelle instance de TimeExpressionEntry.

        Configure les couleurs par défaut et d'erreur, et lie le gestionnaire
        d'événements de modification du texte.

        Args:
            *args: Arguments positionnels passés à wx.TextCtrl.__init__.
            **kwargs: Arguments nommés passés à wx.TextCtrl.__init__.
        """
        super().__init__(*args, **kwargs)

        self.__defaultColor = self.GetBackgroundColour()  # Couleur de fond initiale
        self.__invalidColor = wx.Colour(255, 128, 128)  # Couleur rouge clair pour les erreurs

        # Ajoutez ces lignes de débogage
        log.warning(f"DEBUG - Type de self._onTextChanged: {type(self._onTextChanged)}")
        log.warning(f"DEBUG - Est-ce que self._onTextChanged est callable ? {callable(self._onTextChanged)}")
        # Fin des lignes de débogage

        # Lie l'événement de modification du texte à la méthode _onTextChanged.
        # Cette ligne est le point de l'AssertionError si _onTextChanged n'est pas callable.
        # wx.EVT_TEXT(self, wx.ID_ANY, self._onTextChanged)
        self.Bind(wx.EVT_TEXT, wx.ID_ANY, self._onTextChanged)
        # Cette AssertionError signifie que la fonction ou méthode passée
        # à self.Bind() (qui doit être le gestionnaire d'événement)
        # n'est ni callable (c'est-à-dire une fonction, une méthode
        # ou un objet avec un __call__ défini) ni None.
        # Au moment où cette ligne est exécutée,
        # self._onTextChanged n'est pas une méthode ou une fonction valide
        # de l'instance TimeExpressionEntry.
        #
        # Les raisons les plus courantes pour cela sont :
        #     _onTextChanged n'est pas définie du tout dans la classe TimeExpressionEntry.
        #     _onTextChanged est mal orthographiée.
        #     _onTextChanged est définie plus tard dans le code de la classe (après l'appel à self.Bind()).
        #     TimeExpressionEntry hérite d'une autre classe qui devrait définir _onTextChanged, mais il y a un problème avec l'initialisation de cette classe parente (par exemple, super().__init__() non appelé ou mal appelé).


class TemplatesDialog(sized_controls.SizedDialog):
    """Cette classe implémente une boîte de dialogue pour la gestion des modèles de tâches dans l'application Task Coach.

        Elle permet de visualiser, modifier et supprimer des modèles de tâches existants, ainsi que d'en créer de nouveaux.

    Fonctionnalités principales

        Affichage d'une liste d'arborescence pour parcourir les modèles de tâches.
        Edition des propriétés d'un modèle de tâche sélectionné (sujet, dates de début, d'échéance, d'achèvement et de rappel).
        Suppression d'un modèle de tâche sélectionné.
        Déplacement d'un modèle de tâche vers le haut ou le bas dans la liste.
        Ajout d'un nouveau modèle de tâche.
        Sauvegarde des modifications apportées aux modèles de tâches.

    Classes et méthodes utilisées

        TimeExpressionEntry : Une classe dérivée de wx.TextCtrl permettant la saisie et la validation d'expressions temporelles.
        createTemplateList : Crée la liste d'arborescence pour afficher les modèles de tâches.
        createTemplateEntries : Crée les champs d'édition pour les propriétés d'un modèle de tâche.
        enableEditPanel : Active ou désactive les champs d'édition en fonction de la sélection d'un modèle.
        appendTemplate : Ajoute un modèle de tâche et ses enfants à la liste d'arborescence.
        onValueChanged : Gère les modifications apportées aux champs d'édition d'un modèle de tâche.
        OnSelectionChanged : Gère la sélection d'un modèle de tâche dans la liste, met à jour les champs d'édition et active/désactive les boutons de suppression et de déplacement.
        onDelete : Supprime le modèle de tâche sélectionné.
        OnUp : Déplace le modèle de tâche sélectionné vers le haut dans la liste.
        OnDown : Déplace le modèle de tâche sélectionné vers le bas dans la liste.
        onAdd : Ajoute un nouveau modèle de tâche vide à la liste.
        ok : Sauvegarde les modifications apportées aux modèles de tâches lors de la validation de la boîte de dialogue.
    """

    def __init__(self, settings, *args, **kwargs):
        self.settings = settings
        self._changing = False
        super().__init__(
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER, *args, **kwargs
        )
        pane = self.GetContentsPane()
        pane.SetSizerType("vertical")
        self.createInterior(pane)
        self._buttonSizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        self.SetButtonSizer(self._buttonSizer)
        self.Fit()
        self.SetMinSize(self.GetSize())  # Current size is min size
        self._buttonSizer.GetAffirmativeButton().Bind(
            wx.EVT_BUTTON, self.ok
        )  # gui.uicommand.base_uicommand.bind or Bind ? Plutôt Bind !
        self.CentreOnParent()

    def createInterior(self, pane):
        self.createTemplateList(pane)
        self.createTemplateEntries(pane)

    def createTemplateList(self, pane):
        """Cette méthode est responsable de la construction de l'interface graphique de la boîte de dialogue,
        en créant la liste d'arborescence.

        Args :
            pane :

        Returns :
        """
        panel = sized_controls.SizedPanel(pane)  # revoir l'implémentation
        panel.SetSizerType("horizontal")

        panel.SetSizerProps(expand=True, proportion=1)
        # self._templateList = wx.TreeCtrl(
        #     panel, style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_SINGLE
        # )
        self._templateList = wx.TreeCtrl(
            panel, -1, style=wx.TR_HAS_BUTTONS | wx.TR_HIDE_ROOT | wx.TR_SINGLE
        )
        self._templateList.SetMinSize((300, 200))
        self._templateList.SetSizerProps(expand=True, proportion=1)
        self._templateList.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelectionChanged)
        self._templates = persistence.TemplateList(self.settings.pathToTemplatesDir())
        self._root = self._templateList.AddRoot("Root")
        for task in self._templates.tasks():
            item = self.appendTemplate(self._root, task)
            if operating_system.isMac():
                # See http://trac.wxwidgets.org/ticket/10085
                self._templateList.SetItemText(item, task.subject())
        self.createTemplateListButtons(panel)
        panel.Fit()

    def createTemplateListButtons(self, pane):
        panel = sized_controls.SizedPanel(pane)
        panel.SetSizerType("vertical")
        self._btnDelete = self.createButton(
            panel, "cross_red_icon", self.onDelete, enable=False
        )
        self._btnUp = self.createButton(panel, "arrow_up_icon", self.OnUp, enable=False)
        self._btnDown = self.createButton(
            panel, "arrow_down_icon", self.OnDown, enable=False
        )
        self._btnAdd = self.createButton(panel, "symbol_plus_icon", self.onAdd)
        panel.Fit()

    def createButton(self, parent, bitmapName, handler, enable=True):
        """Cette méthode est responsable de la construction de l'interface graphique de la boîte de dialogue,
        en créant les boutons."""
        bitmap = wx.ArtProvider.GetBitmap(bitmapName, size=(32, 32))
        button = wx.BitmapButton(parent, bitmap=bitmap)
        button.Bind(wx.EVT_BUTTON, handler)
        button.Enable(enable)
        return button

    def createTemplateEntries(self, pane):
        """Cette méthode est responsable de la construction de l'interface graphique de la boîte de dialogue,
        en créant les champs de saisie.

        Args :
            pane :

        Returns :

        """
        panel = self._editPanel = sized_controls.SizedPanel(pane)
        panel.SetSizerType("form")
        panel.SetSizerProps(expand=True)
        label = wx.StaticText(panel, label=_("Subject"))  # StaticText -> TextCtrl ?
        label.SetSizerProps(valign="center")
        self._subjectCtrl = wx.TextCtrl(panel)
        label = wx.StaticText(panel, label=_("Planned start Date"))
        label.SetSizerProps(valign="center")
        self._plannedStartDateTimeCtrl = TimeExpressionEntry(panel)
        label = wx.StaticText(panel, label=_("Due Date"))
        label.SetSizerProps(valign="center")
        self._dueDateTimeCtrl = TimeExpressionEntry(panel)
        label = wx.StaticText(panel, label=_("Completion Date"))
        label.SetSizerProps(valign="center")
        self._completionDateTimeCtrl = TimeExpressionEntry(panel)
        label = wx.StaticText(panel, label=_("Reminder"))
        label.SetSizerProps(valign="center")
        self._reminderDateTimeCtrl = TimeExpressionEntry(panel)
        self._taskControls = (
            self._subjectCtrl,
            self._plannedStartDateTimeCtrl,
            self._dueDateTimeCtrl,
            self._completionDateTimeCtrl,
            self._reminderDateTimeCtrl,
        )
        for ctrl in self._taskControls:
            ctrl.SetSizerProps(valign="center", expand=True)
            ctrl.Bind(wx.EVT_TEXT, self.onValueChanged)
        self.enableEditPanel(False)
        panel.Fit()

    def enableEditPanel(self, enable=True):
        """Active ou désactive les champs d'édition en fonction de la sélection de l'utilisateur."""
        for ctrl in self._taskControls:
            ctrl.Enable(enable)

    def appendTemplate(self, parentItem, task):
        """Ajouter un nouveau nœud à l'arbre des modèles de tâches."""
        # Utilisez AppendItem() avec wx.TreeItemData pour envelopper les données de la tâche
        item = self._templateList.AppendItem(parentItem, task.subject(), data=wx.TreeItemData(task))
        # item = self._templateList.Append(parentItem, task.subject(), data=task)  # Unresolved attribute reference 'Append' for class 'TreeCtrl'
        for child in task.children():
            self.appendTemplate(item, child)
        return item

    def onValueChanged(self, event):
        """Cette méthode gère les événements utilisateur, la modification du contenu d'un champ de saisie.
        Elle met à jour l'état interne de l'application en conséquence.

        Cette méthode est appelée à chaque fois que l'utilisateur modifie le contenu d'un champ de saisie. Son rôle est de :

        - Récupérer le modèle de tâche sélectionné : Elle utilise self._templateList.GetItemData(self._GetSelection()).GetData()
          pour obtenir le modèle de tâche correspondant à l'élément sélectionné dans la liste.
        - Mettre à jour les propriétés du modèle de tâche : Elle modifie les propriétés du modèle de tâche en fonction des
          nouvelles valeurs saisies dans les champs.
          Par exemple, si l'utilisateur a modifié le sujet du modèle, la méthode met à jour la propriété subject du modèle.
        - Gérer les expressions temporelles : Pour les champs de saisie de dates, elle utilise la classe TimeExpressionEntry
          pour vérifier la validité de l'expression saisie et la convertir au format approprié.

        :param event: Événement à sauter.
        :return:
        """
        event.Skip()
        if self._GetSelection().IsOk() and not self._changing:
            task = self._templateList.GetItemData(self._GetSelection()).GetData()
            task.setSubject(self._subjectCtrl.GetValue())
            for ctrl, name in [
                (self._plannedStartDateTimeCtrl, "plannedstartdatetmpl"),
                (self._dueDateTimeCtrl, "duedatetmpl"),
                (self._completionDateTimeCtrl, "completiondatetmpl"),
                (self._reminderDateTimeCtrl, "remindertmpl"),
            ]:
                # Si la classe pour la saisie d'expressions temporelles est valide pour chacune des 4 valeurs
                if TimeExpressionEntry.isValid(ctrl.GetValue()):
                    # Régler l'attribut name de l'objet task sur la valeur saisie ou None.
                    setattr(task, name, ctrl.GetValue() or None)

    def _GetSelection(self):
        return self._templateList.GetSelection()

    def OnSelectionChanged(self, event):  # pylint: disable=W0613
        """Cette méthode gère les événements utilisateur, la sélection d'un élément dans la liste.
        Elle met à jour l'état interne de l'application en conséquence.
        """
        self._changing = True
        try:
            selection = self._GetSelection()
            selectionOk = selection.IsOk() and selection != self._root
            selectionAtRoot = False
            if selectionOk:
                selectionAtRoot = (
                    self._templateList.GetItemParent(selection) == self._root
                )
            self._btnDelete.Enable(selectionAtRoot)
            self._btnUp.Enable(
                selectionAtRoot and self._templateList.GetPrevSibling(selection).IsOk()
            )
            self._btnDown.Enable(
                selectionAtRoot and self._templateList.GetNextSibling(selection).IsOk()
            )
            self.enableEditPanel(selectionOk)
            if selectionOk:
                task = self._templateList.GetItemData(selection).GetData()
                if task is None:
                    for ctrl in self._taskControls:
                        ctrl.SetValue("")
                else:
                    self._subjectCtrl.SetValue(task.subject())
                    self._plannedStartDateTimeCtrl.SetValue(
                        task.plannedstartdatetmpl or ""
                    )
                    self._dueDateTimeCtrl.SetValue(task.duedatetmpl or "")
                    self._completionDateTimeCtrl.SetValue(task.completiondatetmpl or "")
                    self._reminderDateTimeCtrl.SetValue(task.remindertmpl or "")
            else:
                for ctrl in self._taskControls:
                    ctrl.SetValue("")
        except Exception as e:
            log.error(f"Exception: {e}", exc_info=True)
        finally:
            self._changing = False

    def onDelete(self, event):  # pylint: disable=W0613
        """Cette méthode permet à l'utilisateur de modifier la structure de l'arbre des modèles de tâches en supprimant des éléments."""
        task = self._templateList.GetItemData(self._GetSelection()).GetData()
        index = self._templates.tasks().index(task)
        self._templates.deleteTemplate(index)
        self._templateList.Delete(self._GetSelection())

    def OnUp(self, event):  # pylint: disable=W0613
        """Cette méthode permet à l'utilisateur de modifier la structure de l'arbre des modèles de tâches en déplaçant des éléments."""
        selection = self._GetSelection()
        prev = self._templateList.GetPrevSibling(selection)
        prev = self._templateList.GetPrevSibling(prev)
        task = self._templateList.GetItemData(selection).GetData()
        self._templateList.Delete(selection)
        if prev.IsOk():
            # item = self._templateList.InsertItem(self._root, prev, task.subject(), data=wx.TreeItemData(task))
            item = self._templateList.InsertItem(
                self._root, prev, task.subject(), data=task
            )
        else:
            # item = self._templateList.PrependItem(self._root, task.subject(), data=wx.TreeItemData(task))
            item = self._templateList.PrependItem(self._root, task.subject(), data=task)
        for child in task.children():
            self.appendTemplate(item, child)
        index = self._templates.tasks().index(task)
        self._templates.swapTemplates(index - 1, index)
        self._templateList.SelectItem(item)

    def OnDown(self, event):  # pylint: disable=W0613
        """Cette méthode permet à l'utilisateur de modifier la structure de l'arbre des modèles de tâches en déplaçant des éléments."""
        selection = self._GetSelection()
        next = self._templateList.GetNextSibling(selection)
        task = self._templateList.GetItemData(selection).GetData()
        self._templateList.Delete(selection)
        # item = self._templateList.InsertItem(self._root, next, task.subject(), data=wx.TreeItemData(task))
        item = self._templateList.InsertItem(
            self._root, next, task.subject(), data=task
        )
        for child in task.children():
            self.appendTemplate(item, child)
        index = self._templates.tasks().index(task)
        self._templates.swapTemplates(index, index + 1)
        self._templateList.SelectItem(item)

    def onAdd(self, event):  # pylint: disable=W0613
        """Cette méthode permet à l'utilisateur de modifier la structure de l'arbre des modèles de tâches en ajoutant des éléments."""
        template = Task(subject=_("New task template"))
        for name in (
            "plannedstartdatetmpl",
            "duedatetmpl",
            "completiondatetmpl",
            "remindertmpl",
        ):
            setattr(template, name, None)
        theTask = self._templates.addTemplate(template)
        self.appendTemplate(self._root, theTask)

    def ok(self, event):
        """Cette méthode est appelée lorsque l'utilisateur clique sur le bouton "OK" de la boîte de dialogue.
        Elle sauvegarde les modifications apportées aux modèles de tâches."""
        self._templates.save()
        event.Skip()
