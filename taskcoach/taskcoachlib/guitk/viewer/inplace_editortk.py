# guitk/viewer/inplace_editor.py

# Ce fichier définit les éditeurs "en place" utilisés dans les viewers. La conversion impliquera de remplacer les classes de base (hypertreelist.EditTextCtrl, widgets.SpinCtrl, etc.) par leurs équivalents Tkinter et d'adapter la gestion des événements.

# Explications des changements :
#
# Importations : Remplacement des importations wx par tkinter et tkinter.ttk.
# KillFocusAcceptsEditsMixin :
#
# TODO : a implémenter dans taskcoach !
# GetChildren remplacé par winfo_children.
# wx.Window.FindFocus() remplacé par self.focus_get().
# Ajout de méthodes abstraites cancel_changes, accept_changes et finish pour forcer les sous-classes à implémenter ces comportements.
#
#
# SubjectCtrl et DescriptionCtrl :
#
# Remplacement de hypertreelist.EditTextCtrl par ttk.Entry (pour SubjectCtrl) et tk.Text (pour DescriptionCtrl).
# Gestion de l'événement wx.EVT_KILL_FOCUS remplacé par <FocusOut>.
# Implémentation des méthodes abstraites cancel_changes, accept_changes et finish.
#
#
# EscapeKeyMixin :
#
# wx.WXK_ESCAPE, wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER remplacés par leurs équivalents Tkinter ("Escape", "Return", "Enter").
# event.ShiftDown() remplacé par (event.state & 0x0004).
# event.Skip() est commenté.  Dans Tkinter, event.Skip() n'a pas d'équivalent direct. Si tu as besoin d'empêcher le traitement par d'autres gestionnaires, tu peux retourner "break" depuis ton gestionnaire d'événement.
#
#
# _SpinCtrl :
#
# Remplacement de hypertreelist.EditCtrl et widgets.SpinCtrl par ttk.Spinbox.
# Ajout d'une validation pour s'assurer que la valeur entrée est un nombre.
# Initialisation de la valeur avec self.set(str(value)).
# Implémentation des méthodes abstraites cancel_changes, accept_changes et finish.
#
#
# Panel :
#
# Remplacement de wx.Panel par ttk.Frame.
# Remplacement de wx.BoxSizer par pack.
#
#
# BudgetCtrl, AmountCtrl et DateTimeCtrl :
#
# Remplacement de hypertreelist.EditCtrl et Panel par ttk.Frame.
# Il faudra adapter les classes widgets.masked.TimeDeltaCtrl, widgets.masked.AmountCtrl et widgets.DateTimeCtrl pour Tkinter.
#
#
#
# Points Importants :
#
# Adaptation de widgets.masked : Les classes widgets.masked.TimeDeltaCtrl et widgets.masked.AmountCtrl utilisent probablement des fonctionnalités spécifiques à wxPython. Il faudra les adapter pour Tkinter, ou les remplacer par des solutions alternatives.
# Gestion des Événements : La gestion des événements a été adaptée pour Tkinter, mais il faudra vérifier que tout fonctionne correctement.
# Implémentation des Méthodes cancel_changes, accept_changes et finish : Ces méthodes sont vides pour l'instant. Il faudra les implémenter dans chaque sous-classe pour effectuer les actions appropriées (ex: sauvegarder la valeur, annuler l'édition).
#
# Prochaines Étapes :
#
# Adapte les classes widgets.masked : Adapte les classes widgets.masked.TimeDeltaCtrl et widgets.masked.AmountCtrl pour Tkinter.
# Implémente les Méthodes cancel_changes, accept_changes et finish : Implémente ces méthodes dans chaque sous-classe.
# Teste le Code : Adapte les exemples d'utilisation pour tester le code.
# Continue la Conversion : Adapte les autres fichiers en suivant les mêmes principes.
import tkinter as tk
import tkinter.ttk as ttk
# from taskcoachlib.thirdparty.agw import hypertreelist # pas besoin car non utilisé directement
# from wx.lib.agw import hypertreelist # pas besoin car non utilisé directement
from taskcoachlib import widgetstk as widgets  # il faudra adapter widgets.SpinCtrl et widgets.masked
from taskcoachlib.domain import date
# from taskcoachlib.i18n import _ # Pas utilisé directement, peut être utile dans les classes adaptées


class KillFocusAcceptsEditsMixin:
    """
    Mixin class to let in place editors accept changes whenever the user clicks
    outside the edit control instead of cancelling the changes.
    """
    def stop_editing(self):
        try:
            if self.__has_focus():
                # User hit Escape
                self.cancel_changes() # Equivalent de StopEditing
            else:
                # User clicked outside edit window
                self.accept_changes() # Equivalent de AcceptChanges
            self.finish() # Equivalent de Finish
        except RuntimeError:
            pass

    def __has_focus(self):
        """Return whether this control has the focus."""
        def window_and_all_children(window):
            window_and_children = [window]
            for child in window.winfo_children(): # Utilisation de winfo_children
                window_and_children.extend(window_and_all_children(child))
            return window_and_children
        return self.focus_get() in window_and_all_children(self.master) # focus_get() pour Tkinter

    def cancel_changes(self):
        """Méthode à implémenter dans les sous-classes pour annuler les changements."""
        raise NotImplementedError

    def accept_changes(self):
        """Méthode à implémenter dans les sous-classes pour accepter les changements."""
        raise NotImplementedError

    def finish(self):
        """Méthode à implémenter dans les sous-classes pour terminer l'édition."""
        raise NotImplementedError


class SubjectCtrl(KillFocusAcceptsEditsMixin, ttk.Entry): # Remplacement de hypertreelist.EditTextCtrl par ttk.Entry
    """Single line inline control for editing item subjects."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.bind("<FocusOut>", lambda event: self.stop_editing()) # Gestion de la perte de focus

    def cancel_changes(self):
        """Annule les changements."""
        pass  # À adapter selon les besoins

    def accept_changes(self):
        """Accepte les changements."""
        pass  # À adapter selon les besoins

    def finish(self):
        """Termine l'édition."""
        pass  # À adapter selon les besoins


class DescriptionCtrl(KillFocusAcceptsEditsMixin, tk.Text): # Remplacement de hypertreelist.EditTextCtrl par tk.Text
    """Multiline inline text control for editing item descriptions."""
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.bind("<FocusOut>", lambda event: self.stop_editing())  # Gestion de la perte de focus

    def cancel_changes(self):
        """Annule les changements."""
        pass  # À adapter selon les besoins

    def accept_changes(self):
        """Accepte les changements."""
        pass  # À adapter selon les besoins

    def finish(self):
        """Termine l'édition."""
        pass  # À adapter selon les besoins


class EscapeKeyMixin:
    """
    Mixin class for text(like) controls to properly handle the Escape key.
    The inheriting class needs to bind to the event handler. For example:
    self._spinCtrl.bind("<Key>", self.on_key_down)
    """
    def on_key_down(self, event):
        if event.keysym == "Escape":
            self.stop_editing()
        elif event.keysym in ("Return", "Enter") and not (event.state & 0x0004):  # Check Shift key
            # Notify the owner about the changes
            self.accept_changes()
            # Even if vetoed, Close the control (consistent with MSW)
            self.after(0, self.finish)
        else:
            pass  # event.Skip() #Pas utile dans Tkinter, mais peut être remplacé par un return "break" si nécessaire


class _SpinCtrl(EscapeKeyMixin, KillFocusAcceptsEditsMixin, ttk.Spinbox): # Remplacement de hypertreelist.EditCtrl et widgets.SpinCtrl
    """Base spin control class."""
    def __init__(self, parent, item, column, owner, value, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.item = item
        self.the_column = column
        self.owner = owner
        self.value = value
        self.bind("<FocusOut>", lambda event: self.stop_editing())
        self.bind("<Key>", self.on_key_down)
        self.set(str(value))  # Initialise la valeur
        self['validate'] = 'key'
        self['validatecommand'] = (self.register(self.validate_spinbox), '%P')

    def validate_spinbox(self, new_value):
        try:
            float(new_value)  # Vérifie si la nouvelle valeur est un nombre
            return True
        except ValueError:
            return False

    def cancel_changes(self):
        """Annule les changements."""
        pass  # À adapter selon les besoins

    def accept_changes(self):
        """Accepte les changements."""
        pass  # À adapter selon les besoins

    def finish(self):
        """Termine l'édition."""
        pass  # À adapter selon les besoins

    def get_value(self):
        try:
            return float(self.get())
        except ValueError:
            return self.value  # Retourne la valeur initiale en cas d'erreur


class PriorityCtrl(_SpinCtrl):
    """
    Spin control for priority. Since priorities can be any negative or
    positive integer we don't need to set an allowed range.
    """
    pass


class PercentageCtrl(_SpinCtrl):
    """Spin control for percentages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, from_=0, to=100, **kwargs) # min=0, max=100 -> from_=0, to=100


class Panel(ttk.Frame): # Remplacement de wx.Panel par ttk.Frame
    """Panel class for inline controls that need to be put into a panel."""
    def __init__(self, parent, value, *args, **kwargs):
        # pylint: disable=W0613
        # Don't pass the value argument to the wx.Panel since it doesn't take
        # a value argument
        super().__init__(parent, *args, **kwargs)

    def make_sizer(self, control):
        control.pack(expand=True, fill="both") # Remplacement de BoxSizer par pack


class BudgetCtrl(EscapeKeyMixin, KillFocusAcceptsEditsMixin, ttk.Frame): # Remplacement de hypertreelist.EditCtrl et Panel
    """Masked inline text control for editing budgets: <hours>:<minutes>:<seconds>."""
    def __init__(self, parent, item, column, owner, value):
        super().__init__(parent)
        self.item = item
        self.the_column = column
        self.owner = owner
        hours, minutes, seconds = value.hoursMinutesSeconds()
        # Can't inherit from TimeDeltaCtrl because we need to override GetValue,
        # so we use composition instead
        self.__time_delta_ctrl = widgets.masked.TimeDeltaCtrl(self, hours, minutes, seconds) #Adapter widgets.masked.TimeDeltaCtrl
        self.__time_delta_ctrl.bind("<Key>", self.on_key_down)
        self.make_sizer(self.__time_delta_ctrl)
        self.bind("<FocusOut>", lambda event: self.stop_editing())

    def get_value(self):
        return date.parseTimeDelta(self.__time_delta_ctrl.get_value())

    def cancel_changes(self):
        """Annule les changements."""
        pass  # À adapter selon les besoins

    def accept_changes(self):
        """Accepte les changements."""
        pass  # À adapter selon les besoins

    def finish(self):
        """Termine l'édition."""
        pass  # À adapter selon les besoins


class AmountCtrl(EscapeKeyMixin, KillFocusAcceptsEditsMixin, ttk.Frame):  # Remplacement de hypertreelist.EditCtrl et Panel
    """Masked inline text control for editing amounts (floats >= 0)."""
    def __init__(self, parent, item, column, owner, value):
        super().__init__(parent)
        self.item = item
        self.the_column = column
        self.owner = owner
        self.__float_ctrl = widgets.masked.AmountCtrl(self, value) #Adapter widgets.masked.AmountCtrl
        self.__float_ctrl.bind("<Key>", self.on_key_down)
        self.make_sizer(self.__float_ctrl)
        self.bind("<FocusOut>", lambda event: self.stop_editing())

    def get_value(self):
        return self.__float_ctrl.get_value()

    def cancel_changes(self):
        """Annule les changements."""
        pass  # À adapter selon les besoins

    def accept_changes(self):
        """Accepte les changements."""
        pass  # À adapter selon les besoins

    def finish(self):
        """Termine l'édition."""
        pass  # À adapter selon les besoins


class DateTimeCtrl(KillFocusAcceptsEditsMixin, ttk.Frame): # Remplacement de hypertreelist.EditCtrl et Panel
    """Inline Date and time picker control."""
    def __init__(self, parent, item, column, owner, value, **kwargs):
        relative = kwargs.pop("relative", False)
        if relative:
            start = kwargs.pop("startDateTime", date.Now())
        super().__init__(parent)
        self.item = item
        self.the_column = column
        self.owner = owner
        settings = kwargs["settings"]
        starthour = settings.getint("view", "efforthourstart")
        endhour = settings.getint("view", "efforthourend")
        interval = settings.getint("view", "effortminuteinterval")
        self._date_time_ctrl = widgets.DateTimeCtrl( #Adapter widgets.DateTimeCtrl
            self,
            starthour=starthour,
            endhour=endhour,
            interval=interval,
            showRelative=relative,
        )
        self._date_time_ctrl.set_value(value)
        if relative:
            self._date_time_ctrl.set_relative_choices_start(
                start=None if start == date.DateTime() else start
            )
        self.make_sizer(self._date_time_ctrl)
        self.bind("<FocusOut>", lambda event: self.stop_editing())

    def get_value(self):
        return self._date_time_ctrl.get_value()

    def cancel_changes(self):
        """Annule les changements."""
        pass  # À adapter selon les besoins

    def accept_changes(self):
        """Accepte les changements."""
        pass  # À adapter selon les besoins

    def finish(self):
        """Termine l'édition."""
        pass  # À adapter selon les besoins