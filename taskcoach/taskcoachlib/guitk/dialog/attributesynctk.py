# -*- coding: utf-8 -*-
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

Synchronisation des attributs pour Tkinter.
Basé sur la classe AttributeSync originale de TaskCoach.
"""
# Le fichier original utilise des fonctionnalités spécifiques à wxPython
# et un système pubsub. J'ai réécrit le code pour qu'il soit compatible avec
# Tkinter en utilisant son propre système d'événements et en simplifiant
# la logique de synchronisation pour l'adapter au contexte de Tkinter.
#
# Voici la version convertie, qui inclut une classe de démonstration pour que
# vous puissiez voir comment elle fonctionne avec différents widgets comme
# un champ de texte et une case à cocher.

# J’ai comparé les deux fichiers que tu as fournis :
#
# Points positifs dans ta conversion
#
# La logique générale de synchroniser une valeur entre un contrôle graphique et un objet de domaine est bien reprise.
#
# Les méthodes setValue() / getValue() ont été adaptées pour Tkinter (.delete(), .insert(), .get()) → c’est correct.
#
# L’utilisation de tkinter.colorchooser.askcolor pour remplacer wx.ColourDialog est adaptée.
#
# Tu as gardé la gestion des callbacks (__invokeCallback) avec un messagebox Tkinter.
#
# Le support de pubsub est maintenu, donc la compatibilité avec les événements internes du projet est assurée.
#
# Tu as prévu des classes spécialisées (EntrySync, CheckboxSync, ColorSync, FontColorSync) ce qui va dans le bon sens.
#
# ⚠️ Problèmes relevés
#
# Incohérence entre self.entry et self._entry
#
# Dans __init__, tu définis self.entry = entry mais plus bas,
# toutes les méthodes (setValue, getValue, onAttributeChanged, FontColorSync) utilisent self._entry.
# 👉 Ça provoquera une AttributeError car self._entry n’existe pas.
# Solution : uniformiser → renommer self.entry en self._entry partout.
#
# event.widget.event_generate(editedEventType) dans onAttributeEdited
#
# Ici editedEventType n’est pas défini dans la portée de la méthode (il est seulement paramètre du __init__).
# 👉 Cela plantera (NameError).
# Solution : stocker editedEventType en attribut d’instance (self.__editedEventType = editedEventType) et utiliser event.widget.event_generate(self.__editedEventType) si nécessaire.
#
# Méthodes en double/confuses
#
# Tu as gardé set_value() / get_value() (pensées pour être surchargées) et setValue() / getValue() (héritées du wx).
# 👉 Ça double le code, risque de confusion.
# Solution : choisir une convention unique. Soit tu gardes la version Tk (set_value, get_value), soit tu restes proche du wx (setValue, getValue). Je te recommande de garder setValue / getValue pour la compatibilité avec le reste du code.
#
# Classes de démo (Application, DomainObject, EntrySync, CheckboxSync, ColorSync)
#
# Ces classes sont pratiques pour tester, mais elles n’existent pas dans l’original.
# 👉 À garder dans un fichier de test/démo, pas dans taskcoachlib
# (sinon conflit avec l’architecture du projet).
#
# 🛠 Corrections minimales à faire
#
# Remplacer self.entry par self._entry dans tout le fichier.
# Sauvegarder editedEventType dans self.__editedEventType et corriger onAttributeEdited.
# Supprimer soit set_value/get_value, soit setValue/getValue.
# Éventuellement déplacer la classe Application dans un module de test/démo.
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.colorchooser import askcolor
from taskcoachlib.i18n import _
from pubsub import pub
from typing import Any, Callable, List


# # Une simple classe de données pour simuler un objet de domaine
# class DomainObject:
#     def __init__(self, name: str, value: Any):
#         self._name = name
#         self._value = value
#         self.observers: List[Callable] = []
#
#     @property
#     def value(self) -> Any:
#         return self._value
#
#     @value.setter
#     def value(self, new_value: Any):
#         if self._value != new_value:
#             self._value = new_value
#             self.notify_observers()
#
#     def notify_observers(self):
#         for observer in self.observers:
#             observer(self._value)
#
#     def __repr__(self):
#         return f"DomainObject(name='{self._name}', value='{self._value}')"


class AttributeSync(object):
    """
    Classe utilisée pour garder un attribut d'un objet de domaine synchronisé avec
    un contrôle Tkinter dans une boîte de dialogue. Si l'utilisateur modifie
    la valeur à l'aide du contrôle,
    l'objet de domaine est modifié à l'aide de la commande appropriée.
    Si l'attribut de l'objet de domaine est modifié
    (par exemple dans une autre boîte de dialogue),
    la valeur du contrôle est mise à jour.
    """
    # def __init__(self, domain_object: DomainObject, control: Any,
    #              on_edited_callback: Callable, on_changed_callback: Callable = None, **kwargs):
    def __init__(self, attributeGetterName, entry, currentValue, items,
                 commandClass, editedEventType, changedEventType, callback=None,
                 **kwargs):
        """
        Initialise l'instance d'AttributeSync.
        Args:
            attributeGetterName (str) : Nom de la méthode pour obtenir l'attribut de l'objet.
            entry (tk.Entry) : Contrôle dans la boîte de dialogue qui affiche et modifie l'attribut.
            currentValue (any) : Valeur actuelle de l'attribut.
            items (list) : Liste d'objets dont l'attribut doit être synchronisé.
            commandClass (type) : Classe de commande à utiliser pour modifier l'objet.
            editedEventType (str) : Type d'événement édité qui déclenche la mise à jour de l'attribut.
            changedEventType (str) : Type d'événement changé qui déclenche la mise à jour de l'objet.
            callback (callable, optional) : Fonction de rappel à appeler après la modification de l'attribut.
            **kwargs (dict, optional) : Arguments supplémentaires pour la classe de commande.
        """
        # self._domain_object = domain_object
        self._getter = attributeGetterName
        # self._control = control
        self._entry = entry
        # self._current_value = self._domain_object.value
        self._currentValue = currentValue
        self._items = items
        self._commandClass = commandClass
        self.__commandKwArgs = kwargs
        # self._on_edited_callback = on_edited_callback
        # self._on_changed_callback = on_changed_callback
        self.__editedEventType = editedEventType
        self.__changedEventType = changedEventType
        self.__callback = callback

        # # S'enregistre comme observateur sur l'objet de domaine
        # self._domain_object.observers.append(self._on_domain_object_changed)
        #
        # # Lie le contrôle à un événement de modification
        # self.setup_bindings()

        entry.bind(editedEventType, self.onAttributeEdited)
        if len(items) == 1:
            self.__start_observing_attribute(changedEventType, items[0])

    def setup_bindings(self):
        """Configure les liaisons d'événements pour le contrôle."""
        # Ceci est une méthode "placeholder" qui doit être surchargée
        # par les sous-classes pour des types de contrôles spécifiques.
        pass

    # def _on_control_edited(self, event: tk.Event):
    #     """Gère les modifications du contrôle UI."""
    #     # new_value = self.get_value()
    #     new_value = self.getValue()
    #     if new_value != self._current_value:
    #         self._current_value = new_value
    #         # Appelle la fonction de rappel pour gérer la modification
    #         # self._on_edited_callback(self._domain_object, new_value)
    #         self.__editedEventType(self._getter, new_value)

    def onAttributeEdited(self, event):
        """
        Méthode appelée lorsque l'utilisateur modifie la valeur du contrôle.

        Args :
            event (tk.Event) : Événement déclenché par la modification de l'attribut.
        Returns :
            None
        """
        # event.widget.event_generate(editedEventType)  # TODO : A vérifier
        event.widget.event_generate(self.__editedEventType)  # TODO : A vérifier
        new_value = self.getValue()
        if new_value != self._currentValue:
            self._currentValue = new_value
            commandKwArgs = self.commandKwArgs(new_value)
            self._commandClass(None, self._items, **commandKwArgs).do()  # pylint: disable=W0142
            self.__invokeCallback(new_value)

    # def _on_domain_object_changed(self, new_value: Any):
    #     """Gère les modifications de l'objet de domaine."""
    #     if new_value != self._current_value:
    #         self._current_value = new_value
    #         # self.set_value(new_value)
    #         self.setValue(new_value)
    #         # if self._on_changed_callback:
    #         #     self._on_changed_callback(new_value)
    #         if self.__changedEventType:
    #             self.__changedEventType(new_value)

    def onAttributeChanged(self, newValue, sender):
        """
        Méthode appelée lorsque l'attribut de l'objet est modifié.

        Args :
            newValue (any) : Nouvelle valeur de l'attribut.
            sender (object) : Objet qui a déclenché l'événement.
        """
        if sender in self._items:
            if self._entry:
                if newValue != self._currentValue:
                    self._currentValue = newValue
                    self.setValue(newValue)
                    self.__invokeCallback(newValue)

    def commandKwArgs(self, new_value):
        """
        Met à jour les arguments pour la classe de commande.

        Args :
        new_value (any) : Nouvelle valeur de l'attribut.

        Returns :
            dict : Arguments mis à jour.
        """
        self.__commandKwArgs["newValue"] = new_value
        return self.__commandKwArgs

    # def set_value(self, new_value: Any):
    #     """Met à jour la valeur du contrôle. Doit être surchargé."""
    #     raise NotImplementedError("set_value doit être implémenté par les sous-classes")

    def setValue(self, new_value):
        """
        Définit la valeur du contrôle.

        Args :
            new_value (any) : Nouvelle valeur à définir.
        """
        self._entry.delete(0, tk.END)
        self._entry.insert(0, new_value)

    # def get_value(self) -> Any:
    #     """Récupère la valeur du contrôle. Doit être surchargé."""
    #     raise NotImplementedError("get_value doit être implémenté par les sous-classes")

    def getValue(self):
        """
        Obtient la valeur actuelle du contrôle.

        Returns :
            any : Valeur actuelle du contrôle.
        """
        return self._entry.get()

    def __invokeCallback(self, value):
        """
        Appelle le rappel avec la nouvelle valeur.

        Args :
            value (any) : Nouvelle valeur de l'attribut.
        """
        if self.__callback is not None:
            try:
                self.__callback(value)
            except Exception as e:
                tk.messagebox.showerror(_("Error"), str(e))

    def __start_observing_attribute(self, eventType, eventSource):
        """
        Commence à observer les changements de l'attribut.

        Args :
            eventType (str) : Type d'événement à observer.
        eventSource (object) : Source de l'événement à observer.
        """
        pub.subscribe(self.onAttributeChanged, eventType)

    def __stop_observing_attribute(self):
        """
        Arrête d'observer les changements de l'attribut.
        """
        try:
            pub.unsubscribe(self.onAttributeChanged, self.__changedEventType)
        except pub.TopicNameError:
            pass

#
# class EntrySync(AttributeSync):
#     """Synchronise un champ de saisie Tkinter."""
#     def setup_bindings(self):
#         self._control.bind("<KeyRelease>", self._on_control_edited)
#
#     def set_value(self, new_value: Any):
#         self._control.delete(0, tk.END)
#         self._control.insert(0, str(new_value))
#
#     def get_value(self) -> Any:
#         return self._control.get()


# class CheckboxSync(AttributeSync):
#     """Synchronise une case à cocher Tkinter."""
#     def __init__(self, domain_object: DomainObject, control: Any, var: tk.BooleanVar,
#                  on_edited_callback: Callable, **kwargs):
#         self._var = var
#         super().__init__(domain_object, control, on_edited_callback, **kwargs)
#
#     def setup_bindings(self):
#         self._var.trace_add("write", self._on_control_edited_trace)
#
#     def _on_control_edited_trace(self, *args):
#         # Appelé par trace_add, nous devons appeler la méthode de base
#         self._on_control_edited(None)
#
#     def set_value(self, new_value: Any):
#         self._var.set(bool(new_value))
#
#     def get_value(self) -> Any:
#         return self._var.get()


# class ColorSync(AttributeSync):
#     """Synchronise une couleur Tkinter."""
#     def setup_bindings(self):
#         self._control.bind("<Button-1>", self._on_control_edited)
#
#     def _on_control_edited(self, event: tk.Event):
#         color_code = askcolor(self._current_value)[1]
#         if color_code:
#             self.set_value(color_code)
#             super()._on_control_edited(event)
#
#     def set_value(self, new_value: Any):
#         self._control.config(bg=new_value)
#
#     def get_value(self) -> Any:
#         return self._control.cget("bg")


class FontColorSync(AttributeSync):
    """
    Classe utilisée pour garder la couleur d'un attribut d'un objet de domaine synchronisée avec
    un contrôle dans une boîte de dialogue. Si l'utilisateur modifie
    la couleur à l'aide du contrôle,
    l'objet de domaine est modifié à l'aide de la commande appropriée.
    Si la couleur de l'attribut de l'objet est modifiée
    (par exemple dans une autre boîte de dialogue),
    la valeur du contrôle est mise à jour.
    """

    def setValue(self, newValue):
        """
        Définit la couleur du contrôle.

        Args :
            newValue (tk.Entry) : Nouvelle couleur à définir.
        """
        self._entry.config(fg=newValue)

    def getValue(self):
        """
        Obtient la couleur actuelle du contrôle.

        Returns :
            tk.Entry : Couleur actuelle du contrôle.
        """
        return self._entry.cget("fg")


# class Application(tk.Tk):
#     def __init__(self):
#         super().__init__()
#         self.title("Démonstration AttributeSync")
#         self.geometry("600x400")
#
#         # Objet de domaine à synchroniser
#         self.task_name = DomainObject("Nom de la tâche", "Tâche de test")
#         self.task_completed = DomainObject("Tâche terminée", False)
#         self.task_color = DomainObject("Couleur de la tâche", "#FFFFFF")
#
#         self.setup_ui()
#
#     def setup_ui(self):
#         frame = ttk.Frame(self, padding="10")
#         frame.pack(fill="both", expand=True)
#
#         # Synchronisation pour un champ de saisie
#         ttk.Label(frame, text="Nom de la tâche:").grid(row=0, column=0, sticky="w", pady=5)
#         name_entry = ttk.Entry(frame)
#         name_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=5)
#         EntrySync(self.task_name, name_entry, self.on_domain_edited)
#
#         # Synchronisation pour une case à cocher
#         ttk.Label(frame, text="Tâche terminée:").grid(row=1, column=0, sticky="w", pady=5)
#         completed_var = tk.BooleanVar(value=self.task_completed.value)
#         completed_checkbox = ttk.Checkbutton(frame, variable=completed_var)
#         completed_checkbox.grid(row=1, column=1, sticky="w", pady=5, padx=5)
#         CheckboxSync(self.task_completed, completed_checkbox, completed_var, self.on_domain_edited)
#
#         # Synchronisation pour la couleur
#         ttk.Label(frame, text="Couleur de la tâche:").grid(row=2, column=0, sticky="w", pady=5)
#         color_frame = tk.Frame(frame, width=30, height=30, relief="solid", borderwidth=1, cursor="hand2")
#         color_frame.grid(row=2, column=1, sticky="w", pady=5, padx=5)
#         ColorSync(self.task_color, color_frame, self.on_domain_edited)
#
#         # Champ de saisie pour modifier directement les objets de domaine (pour le test)
#         ttk.Label(frame, text="Modifier l'objet de domaine (test):").grid(row=3, column=0, sticky="w", pady=5, columnspan=2)
#         domain_entry = ttk.Entry(frame)
#         domain_entry.grid(row=4, column=0, sticky="ew", pady=5, columnspan=2, padx=5)
#
#         def update_from_entry():
#             self.task_name.value = domain_entry.get()
#
#         domain_entry.bind("<KeyRelease>", lambda e: update_from_entry())
#
#         # Affichage pour voir les changements
#         self.status_label = ttk.Label(self, text="Statut: Attente de modification...")
#         self.status_label.pack(side="bottom", fill="x", pady=10)
#
#     def on_domain_edited(self, domain_object: DomainObject, new_value: Any):
#         """Cette fonction agit comme la classe de commande dans l'original."""
#         self.status_label.config(text=f"Statut: L'attribut '{domain_object._name}' a été modifié en '{new_value}'")
#         domain_object.value = new_value


# if __name__ == '__main__':
#     app = Application()
#     app.mainloop()
