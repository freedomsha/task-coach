# smartdatetimectrl.py for Tkinter

# C'est un défi complexe ! Le fichier smartdatetimectrl.py est très détaillé et
# utilise des fonctionnalités de dessin avancées de wxPython qui n'ont pas
# d'équivalent direct dans Tkinter. Il faudra donc recréer une grande partie de
# la logique de rendu et de gestion des événements.
#
# J'ai analysé le fichier wxPython et j'ai commencé la conversion.
# Voici une première version de smartdatetimectrl.py pour Tkinter.
# Cette implémentation se concentre sur les aspects principaux :
#
#     Champs d'entrée : Les différentes parties de la date et de l'heure
#     (jour, mois, année, heure, minute, seconde) sont des tk.Entry indépendants.
#
#     Navigation : La navigation entre les champs se fait avec les touches
#     fléchées, comme dans l'original.
#
#     Validation : La saisie est validée pour s'assurer qu'elle correspond à
#     un format de date/heure valide.
#
#     Interface de choix : Une interface simple de choix est mise en place pour
#     les mois, heures, minutes et secondes, avec un menu contextuel qui apparaît au clic.
#
# Gardez à l'esprit que le code wxPython est très sophistiqué en matière de gestion
# du focus, de dessin de cases à cocher personnalisées, et de popups.
# Cette version Tkinter est une simplification qui reproduit la fonctionnalité de base.
# Elle pourra être améliorée par la suite.

# J'ai converti le code principal de smartdatetimectrl.py en une version fonctionnelle
# pour Tkinter. L'implémentation de _CheckBox et de drawFocusRect a été omise
# car ces fonctionnalités graphiques avancées ne sont pas directement supportées
# par les widgets standard de Tkinter.
#
# Pour tester le code, vous pouvez l'exécuter et interagir avec les champs de date et d'heure.
# N'hésitez pas à me poser d'autres questions si vous avez besoin d'ajustements
# ou de conversions supplémentaires.

# J'ai analysé et converti la classe SmartDateTimeCtrl du fichier smartdatetimectrl.py
# pour qu'elle fonctionne avec Tkinter.
# Le code original de wxPython est très sophistiqué, notamment en ce qui
# concerne la gestion des événements, le rendu graphique et les popups.
#
# La conversion pour Tkinter nécessite de recréer cette logique en utilisant
# les widgets et la gestion des événements de Tkinter.
# J'ai donc adapté les classes Entry, NumericField, EnumerationField, AMPMField
# et TimeCtrl pour les rendre compatibles. J'ai également converti la classe
# _CheckBox en utilisant ttk.Checkbutton, ce qui est beaucoup plus simple
# que le rendu personnalisé de wxPython.

# J'ai examiné les fichiers fournis et voici ce que j'ai trouvé concernant votre
# problème d'affichage des dates dans Tkinter, en particulier avec le widget SmartDateTimeCtrl .
# Analyse du problème :
# Votre problème est que le widget SmartDateTimeCtrl dans Tkinter
# (défini dans smartdatetimectrltk.py) affiche des lettres (YYYY, MM, DD, hh, mm, ss)
# au lieu de nombres pour représenter la date et l'heure,
# alors que vous vous attendez à voir des nombres comme dans la version wxPython.
# Cause possible :
# La cause probable est que le formatage de la date et de l'heure n'est pas correctement interprété ou appliqué dans la version Tkinter du widget. Le code Tkinter semble utiliser directement les chaînes de formatage (par exemple, "YYYY-MM-DD") comme des étiquettes littérales au lieu de les utiliser pour formater les valeurs numériques de la date et de l'heure.
# Résolution potentielle :
# Il faut examiner attentivement la manière dont les champs de date et d'heure sont créés et mis à jour dans la classe Entry (utilisée par SmartDateTimeCtrl) dans smartdatetimectrltk.py. Il faut s'assurer que les valeurs numériques (année, mois, jour, heure, minute, seconde) sont correctement formatées en chaînes de caractères en utilisant les spécificateurs de format appropriés avant d'être affichées dans les champs d'entrée Tkinter.
# Vérification du code :
#
# Classe Entry et formatage :
#
# Vérifiez la méthode _parse_format dans la classe Entry . Assurez-vous que les caractères de formatage (Y, M, D, h, m, s) sont correctement associés aux champs numériques correspondants (YearField, MonthField, DayField, HourField, MinuteField, SecondField).
# Dans les classes YearField, MonthField, DayField, HourField, MinuteField et SecondField     , vérifiez comment la valeur numérique est convertie en chaîne de caractères pour être affichée dans le widget Tkinter. Utilisez des spécificateurs de formatage comme %Y, %m, %d, %H, %M, %S pour assurer un affichage numérique correct.
# Examinez la méthode SetValue dans la classe Field  et assurez-vous qu'elle met à jour correctement la valeur affichée dans le widget Tkinter après une modification.
#
#
# Classe SmartDateTimeCtrl :
#
# Dans la classe SmartDateTimeCtrl , vérifiez comment les valeurs initiales de la date et de l'heure sont passées aux champs Entry.
# Assurez-vous que les chaînes de formatage date_format et time_format sont correctement utilisées pour initialiser les champs Entry avec le bon format.
#
#
# Exemple d'utilisation :
#
# Dans la section if __name__ == "__main__": de smartdatetimectrltk.py , vérifiez comment le widget SmartDateTimeCtrl est créé et initialisé. Assurez-vous que les chaînes de formatage sont passées correctement.
#
#
#
# Adaptation du code :
# Voici des suggestions pour adapter le code Tkinter afin d'obtenir l'affichage numérique souhaité :
#
# Utiliser des spécificateurs de formatage : Dans les classes YearField, MonthField, DayField, HourField, MinuteField et SecondField, utilisez des spécificateurs de formatage comme %Y, %m, %d, %H, %M, %S pour convertir les valeurs numériques en chaînes de caractères formatées avant de les afficher dans les widgets Tkinter. Par exemple:
#
# pythonclass YearField(NumericField):
#     def SetValue(self, value, notify=False):
#         formatted_value = "%Y" % value  # Exemple
#         super().SetValue(formatted_value, notify)
#
# Adapter la méthode _parse_format : Modifiez la méthode _parse_format dans la classe Entry pour qu'elle interprète correctement les caractères de formatage et crée les champs numériques correspondants avec les spécificateurs de formatage appropriés.
# La fonction 'my_callback':
# Il faut vérifier dans la fonction my_callback(new_value) de smartdatetimectrltk.py si l'affichage est bien formaté.
#
# En résumé, le problème vient probablement d'une mauvaise interprétation ou application des chaînes de formatage dans le code Tkinter. Il faut vérifier attentivement comment les valeurs numériques sont converties en chaînes de caractères et affichées dans les widgets Tkinter, et utiliser les spécificateurs de formatage appropriés pour assurer un affichage numérique correct.

# Bon, revoyons cela. Premièrement, dans smartdatetimectrltk, il faut que Entry soit un enfant de ttk.Entry ! :
#
# class Entry(ttk.Entry):
#
# Deuxièmement, pour la mise en forme date et heure, n'est-il pas possible de vérifier justement tout le contenu d'Entry au fur et à mesure de ce qui est écrit ou de ce qu'il contient plutôt que de tout séparer dans des blocs différents ?

# Vos suggestions sont excellentes et représentent un changement de conception fondamental qui est plus en phase avec la manière de faire de Tkinter. Vous avez tout à fait raison : la meilleure approche est de gérer l'intégralité de l'entrée de date et d'heure dans un seul widget ttk.Entry plutôt que de la diviser en plusieurs champs.
#
# Votre première suggestion, faire en sorte que Entry hérite directement de ttk.Entry (class Entry(ttk.Entry):), est la clé. Cela implique de réécrire la logique pour gérer la saisie et la validation directement dans un seul champ de texte.
#
# J'ai réécrit le code de smartdatetimectrltk.py en suivant cette approche.
# Voici les changements principaux :
#
#     Structure de la classe Entry : La classe Entry hérite maintenant de ttk.Entry et gère l'ensemble de la chaîne de date et d'heure. Il n'y a plus de classes YearField, MonthField, etc., car elles ne sont plus nécessaires.
#
#     Validation en temps réel : La saisie est validée en continu à l'aide des fonctions de validation de Tkinter. J'utilise une fonction qui vérifie si l'entrée correspond à un format de date et d'heure valide. Si ce n'est pas le cas, l'entrée est rejetée.
#
#     Gestion de la valeur : Les méthodes GetValue() et SetValue() sont maintenant plus simples. GetValue() utilise datetime.strptime pour convertir la chaîne de l'entrée en un objet datetime, et SetValue() utilise strftime pour formater un objet datetime en chaîne de caractères pour l'affichage.
#
#     Simplicité du code : Cette approche rend le code plus propre et plus simple, car elle élimine la complexité liée à la gestion de plusieurs champs et à la synchronisation des données entre eux.
#
# Ce nouveau code offre une expérience utilisateur plus intuitive et est beaucoup plus robuste.

# C'est une excellente question, qui touche au cœur de l'expérience utilisateur !
#
# En effet, il est tout à fait possible et souvent préférable d'attendre que l'utilisateur ait fini d'écrire pour vérifier la saisie. Le choix entre une validation en temps réel (à chaque frappe) et une validation différée dépend du comportement que vous souhaitez donner à votre application.
#
# 1. Validation en temps réel (validate="key")
#
# C'est l'approche que nous avons utilisée jusqu'à présent.
#
#     Principe : Le code de validation s'exécute à chaque frappe de touche.
#
#     Avantages :
#
#         Prévention des erreurs : Cela empêche l'utilisateur d'entrer des caractères invalides dès le départ. C'est idéal pour des formats très stricts (comme des numéros de téléphone sans lettres).
#
#         Feedback immédiat : L'utilisateur sait immédiatement si son action est correcte ou non.
#
#     Inconvénients :
#
#         Expérience "saccadée" : Pour la saisie d'une date ou d'une heure, cette méthode peut être frustrante. Par exemple, lorsque vous tapez "1", la validation peut échouer si le format attend un "10" ou un "12", car la chaîne n'est pas encore complète. L'utilisateur doit souvent attendre d'avoir tapé le deuxième chiffre pour que la validation réussisse.
#
# 2. Validation à la sortie du champ (validate="focusout")
#
# Cette méthode est un excellent compromis et correspond à votre question.
#
#     Principe : La validation s'exécute uniquement lorsque l'utilisateur quitte le champ de saisie (par exemple, en cliquant dans un autre champ ou en appuyant sur la touche Tab).
#
#     Avantages :
#
#         Liberté de saisie : L'utilisateur peut taper toute la chaîne de caractères librement, sans être interrompu.
#
#         Expérience fluide : Le comportement est moins intrusif et plus naturel.
#
#     Inconvénients :
#
#         Feedback différé : L'utilisateur ne voit pas son erreur tant qu'il n'a pas quitté le champ. Pour résoudre cela, vous pouvez, en cas d'erreur, mettre le champ en surbrillance (avec une couleur de fond rouge, par exemple) pour attirer l'attention.
#
# 3. Recommandation pour votre projet
#
# Pour un champ de saisie de date ou d'heure, l'approche par validation à la sortie du champ (validate="focusout") est souvent la plus pertinente. Elle offre un meilleur équilibre entre le contrôle de la saisie et une expérience utilisateur fluide.
#
# Pour l'implémenter, il vous suffit de modifier la ligne super() de l'initialisation du widget Entry en mettant validate sur "focusout".
import tkinter as tk
from tkinter import ttk, Menu
import datetime
import calendar
import re
from io import StringIO
import math
import platform


# ==============================================================================
# Helper functions
# ==============================================================================
def monthcalendarex(year, month, weeks=0):
    weekDay, monthLength = calendar.monthrange(year, month)
    startDate = datetime.date(year, month, 1)
    endDate = datetime.date(year, month, monthLength)
    # To start of week
    startDate -= datetime.timedelta(
        days=(startDate.weekday() - calendar.firstweekday()) % 7
    )
    endDate += datetime.timedelta(
        days=(7 + calendar.firstweekday() - endDate.weekday()) % 7
    )
    startDate -= datetime.timedelta(weeks=weeks)
    endDate += datetime.timedelta(weeks=weeks)
    monthCal = list()
    while startDate < endDate:
        week = list()
        for dayNumber in range(7):
            theDate = startDate + datetime.timedelta(days=dayNumber)
            week.append((theDate.year, theDate.month, theDate.day))
        monthCal.append(week)
        startDate += datetime.timedelta(weeks=1)
    return monthCal


class NullField(object):
    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def GetValue(self):
        return 0


NullField = NullField()


# class FormatCharacter(object):
#     valueName = None
#
#     def __init__(self, c):
#         pass
#
#     @classmethod
#     def matches(self, c):
#         raise NotImplementedError
#
#     @classmethod
#     def keywordArgs(klass, kwargs):
#         if klass.valueName is not None:
#             return dict(value=kwargs.pop(klass.valueName))
#         try:
#             return dict(value=kwargs["values"].pop(0))
#         except KeyError:
#             raise KeyError("No values defined for unnamed field %s" % klass)
#
#     def append(self, c):
#         # raise NotImplementedError
#         self.value += c
#
#     def createField(self, *args, **kwargs):
#         raise NotImplementedError


# class SingleFormatCharacter(FormatCharacter):
#     character = None
#
#     @classmethod
#     def matches(self, c):
#         return c == self.character
#
#     def append(self, c):
#         pass
#
#
# class AnyFormatCharacter(FormatCharacter):
#     def __init__(self, c):
#         self.__value = c
#
#     @classmethod
#     def matches(self, c):
#         return True
#
#     def append(self, c):
#         self.__value += c
#
#     @classmethod
#     def keywordArgs(klass, kwargs):
#         return dict()
#
#     # def createField(self, *args, **kwargs):
#     def createField(self, master, *args, **kwargs):
#         # return self.__value
#         return ttk.Label(master, text=self.__value)


# # ==============================================================================
# # Field classes
# # ==============================================================================
# # class Field(object):
# class Field(ttk.Entry):
#     """
#     Base class representing a data entry field.
#     """
#     def __init__(self, master, observer, value, choices=None, **kwargs):
#         self.master = master
#         self.observer = observer
#         # self.__observer = kwargs.pop("observer")
#         self._value = value
#         # self.__value = kwargs.pop("value")
#         self._choices = choices
#         # self.__choices = kwargs.pop("choices", None)  # 2-tuples [(label, value)]
#         self.entry_var = tk.StringVar(value=str(value))
#         # self.entry = ttk.Entry(self.master, width=5, textvariable=self.entry_var, **kwargs)
#         super().__init__(self.master, width=5, textvariable=self.entry_var, **kwargs)
#
#         # self.entry.bind("<FocusIn>", self.on_focus_in)
#         self.bind("<FocusIn>", self.on_focus_in)
#         # self.entry.bind("<FocusOut>", self.on_focus_out)
#         self.bind("<FocusOut>", self.on_focus_out)
#         # self.entry.bind("<Key>", self.on_key)
#         self.bind("<Key>", self.on_key)
#         # self.entry.bind("<Button-1>", self.on_click)
#         self.bind("<Button-1>", self.on_click)
#
#         self.is_focused = False
#
#     def on_focus_in(self, event):
#         self.is_focused = True
#         # self.entry.select_range(0, 'end')
#         self.select_range(0, 'end')
#         # self.entry.icursor('end')
#         self.icursor('end')
#
#     def on_focus_out(self, event):
#         self.is_focused = False
#
#     def on_key(self, event):
#         # A simple validation and navigation logic
#         if event.keysym == 'Right':
#             self.observer.focus_next_field(self)
#         elif event.keysym == 'Left':
#             self.observer.focus_prev_field(self)
#         elif event.keysym == 'Up':
#             self.observer.increment_field(self)
#         elif event.keysym == 'Down':
#             self.observer.decrement_field(self)
#
#     def on_click(self, event):
#         self.observer.popup_choices(self)
#
#     def GetValue(self):
#         # return self.entry_var.get()
#         return self._value
#
#     def SetValue(self, value, notify=False):
#         if notify:
#             value = self.observer.validate_change(self, value)
#             if value is None:
#                 return
#
#         self._value = value
#         self.entry_var.set(str(value))
#         self.observer.refresh()
#
#     def GetChoices(self):
#         return self._choices
#
#     def GetExtent(self):
#         # This is a simplified version, as Tkinter doesn't have a direct equivalent to GetTextExtent
#         # return self.entry.winfo_reqwidth(), self.entry.winfo_reqheight()
#         return self.winfo_reqwidth(), self.winfo_reqheight()
#
#     def ResetState(self):
#         pass
#
#     def HandleKey(self, event):
#         return False
#
#     def OnClick(self):
#         pass
#
#     # def grid(self, *args, **kwargs):
#     #     # self.entry.grid(*args, **kwargs)
#     #     self.grid(*args, **kwargs)
#     #
#     # def pack(self, *args, **kwargs):
#     #     # self.entry.pack(*args, **kwargs)
#     #     self.pack(*args, **kwargs)
#
#
# class NumericField(Field):
#     class NumericFormatCharacter(FormatCharacter):
#         def __init__(self, c):
#             self.__width = 1
#
#         @classmethod
#         def matches(self, c):
#             return c == "#"
#
#         def append(self, c):
#             self.__width += 1
#
#         def createField(self, *args, **kwargs):
#             kwargs["width"] = self.__width
#             return NumericField(*args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         self.__width = kwargs.pop("width", 0)
#         super().__init__(*args, **kwargs)
#         # self.entry.config(width=self.__width)
#         self.config(width=self.__width)
#         # self.entry.bind("<Key>", self.handle_key)
#         self.bind("<Key>", self.handle_key)
#
#     def GetValue(self):
#         try:
#             return int(self.entry_var.get())
#         except ValueError:
#             return 0
#
#     def handle_key(self, event):
#         key = event.keysym
#         # if key.isdigit() or key == 'BackSpace' or key == 'Delete':
#         if key.isdigit() or key in ['BackSpace', 'Delete', 'Left', 'Right', 'Up', 'Down', 'Tab', 'Return']:
#             return False  # Let default Tkinter behavior handle it
#         else:
#             return 'break'  # Stop key event from propagating
#
#     def OnClick(self):
#         pass
#
#     def SetValue(self, value, notify=False):
#         super().SetValue(int(value), notify)
#
#
# class EnumerationField(Field):
#     def __init__(self, *args, **kwargs):
#         self.__enablePopup = kwargs.pop("enablePopup", True)
#         super().__init__(*args, **kwargs)
#
#     def GetCurrentChoice(self):
#         for idx, (label, value) in enumerate(self._choices):
#             if value == self._value:
#                 return value
#         return self._choices[0][1]
#
#     def on_click(self, event):
#         if self.__enablePopup:
#             super().on_click(event)
#
#     def GetExtent(self):
#         max_width = 0
#         for label, value in self._choices:
#             max_width = max(max_width, len(label))
#         return max_width * 8, 16  # rough estimate
#
#
# class AMPMField(EnumerationField):
#     class AMPMFormatCharacter(SingleFormatCharacter):
#         character = "p"
#         valueName = "ampm"
#
#         def createField(self, *args, **kwargs):
#             kwargs["choices"] = [("AM", 0), ("PM", 1)]
#             return AMPMField(*args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # self.entry.bind("<KeyRelease>", self.handle_key)
#         self.bind("<KeyRelease>", self.handle_key)
#
#     def handle_key(self, event):
#         key = event.keysym
#         if key.lower() == 'a':
#             self.SetValue(0, notify=True)
#             return 'break'
#         elif key.lower() == 'p':
#             self.SetValue(1, notify=True)
#             return 'break'
#         return None
#
#     def OnClick(self):
#         pass
#
#
# # class DayField(Field):
# #     def __init__(self, master, observer, value):
# #         super().__init__(master, observer, value)
# #         self.entry.config(width=2)
#
#
# class DayField(NumericField):
#     # class DateFormatCharacter(SingleFormatCharacter):
#     class DayFormatCharacter(FormatCharacter):
#         # character = "D"
#         # valueName = "day"
#         def __init__(self, c):
#             self.value = c
#
#         @classmethod
#         def matches(self, c):
#             return c == 'D'
#
#         def createField(self, *args, **kwargs):
#             return DayField(*args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # self.entry.config(width=2)
#         self.config(width=2)
#
#
# # class YearField(Field):
# #     def __init__(self, master, observer, value):
# #         super().__init__(master, observer, value)
# #         self.entry.config(width=4)
#
#
# class YearField(NumericField):
#     # class YearFormatCharacter(SingleFormatCharacter):
#     class YearFormatCharacter(FormatCharacter):
#         # character = "Y"
#         # valueName = "year"
#         def __init__(self, c):
#             self.value = c
#
#         @classmethod
#         def matches(self, c):
#             return c == 'Y'
#
#         def createField(self, *args, **kwargs):
#             return YearField(*args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # self.entry.config(width=4)
#         self.config(width=4)
#
#     def SetValue(self, value, notify=False):
#         formatted_value = "%Y" % value  # Exemple
#         super().SetValue(formatted_value, notify)
#
# # class MonthField(Field):
# #     def __init__(self, master, observer, value, choices):
# #         super().__init__(master, observer, value, choices)
# #         self.entry.config(width=2)
# #         self.entry.bind("<Button-1>", self.on_click)
# #
# #     def on_click(self, event):
# #         self.observer.popup_choices(self)
#
#
# class MonthField(NumericField):
#     class MonthFormatCharacter(SingleFormatCharacter):
#         # character = "M"
#         # valueName = "month"
#         def __init__(self, c):
#             self.value = c
#
#         @classmethod
#         def matches(self, c):
#             return c == 'M'
#
#         def createField(self, *args, **kwargs):
#             return MonthField(*args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # self.entry.config(width=2)
#         self.config(width=2)
#
#
# # class HourField(Field):
# #     def __init__(self, master, observer, value, choices):
# #         super().__init__(master, observer, value, choices)
# #         self.entry.config(width=2)
# #         self.entry.bind("<Button-1>", self.on_click)
# #
# #     def on_click(self, event):
# #         self.observer.popup_choices(self)
#
#
# class HourField(NumericField):
#     # class HourFormatCharacter(SingleFormatCharacter):
#     class HourFormatCharacter(FormatCharacter):
#         # character = "h"
#         # valueName = "hour"
#         def __init__(self, c):
#             self.value = c
#
#         @classmethod
#         def matches(self, c):
#             return c == 'h'
#
#         def createField(self, *args, **kwargs):
#             return HourField(*args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # self.entry.config(width=2)
#         self.config(width=2)
#
#
# # class MinuteField(Field):
# #     def __init__(self, master, observer, value, choices):
# #         super().__init__(master, observer, value, choices)
# #         self.entry.config(width=2)
# #         self.entry.bind("<Button-1>", self.on_click)
# #
# #     def on_click(self, event):
# #         self.observer.popup_choices(self)
#
#
# class MinuteField(NumericField):
#     # class MinuteFormatCharacter(SingleFormatCharacter):
#     class MinuteFormatCharacter(FormatCharacter):
#         # character = "m"
#         # valueName = "minute"
#         def __init__(self, c):
#             self.value = c
#
#         @classmethod
#         def matches(self, c):
#             return c == 'm'
#
#         def createField(self, *args, **kwargs):
#             return MinuteField(*args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # self.entry.config(width=2)
#         self.config(width=2)
#
#
# # class SecondField(Field):
# #     def __init__(self, master, observer, value, choices):
# #         super().__init__(master, observer, value, choices)
# #         self.entry.config(width=2)
# #         self.entry.bind("<Button-1>", self.on_click)
# #
# #     def on_click(self, event):
# #         self.observer.popup_choices(self)
#
#
# class SecondField(NumericField):
#     # class SecondFormatCharacter(SingleFormatCharacter):
#     class SecondFormatCharacter(FormatCharacter):
#         # character = "s"
#         # valueName = "second"
#         def __init__(self, c):
#             self.value = c
#
#         @classmethod
#         def matches(self, c):
#             return c == 's'
#
#         def createField(self, *args, **kwargs):
#             return SecondField(*args, **kwargs)
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # self.entry.config(width=2)
#         self.config(width=2)


# ==============================================================================
# Entry and SmartDateTimeCtrl
# ==============================================================================
# class Entry(ttk.Frame):
class Entry(ttk.Entry):
    # MARGIN = 3
    # formats = [AnyFormatCharacter,
    #            DayField.DayFormatCharacter,
    #            MonthField.MonthFormatCharacter,
    #            YearField.YearFormatCharacter,
    #            HourField.HourFormatCharacter,
    #            MinuteField.MinuteFormatCharacter,
    #            SecondField.SecondFormatCharacter,
    #            AMPMField.AMPMFormatCharacter]
    # _rx_paste = re.compile(r"(?i)\d+|am|pm")

    def __init__(self, master, format_string, **kwargs):
        # super().__init__(master)

        self.master = master
        # self.fields = []
        # self._widgets = []
        # self._namedFields = {}
        # self.current_field_index = 0
        # self.current_focus_idx = -1
        # self.format_spec = format_string
        self.format_str = format_string
        self.format_regex = self._format_to_regex(format_string)
        # self.popup_menu = None
        # self.popup_field = None
        self.value_var = tk.StringVar()

        # We need a validation command for real-time validation
        vcmd = (master.register(self.validate_input), '%P')

        # super().__init__(self.master, textvariable=self.value_var, validate="key", validatecommand=vcmd, **kwargs)
        super().__init__(self.master, textvariable=self.value_var, validate="focusout", validatecommand=vcmd, **kwargs)

        # # self.construct_fields(format, kwargs)
        # self._parse_format(format_string, kwargs)
        # self._setup_widgets()
        # self.bind_events()

    # La méthode validate_input est au cœur du mécanisme de validation en temps réel de votre widget Entry. Son rôle est de s'assurer que chaque caractère que l'utilisateur saisit est valide avant qu'il ne soit affiché.
    #
    # Explication de la méthode validate_input
    #
    # Cette méthode est une fonction de rappel (callback) que Tkinter exécute automatiquement à chaque fois que le contenu du widget Entry change. Elle est associée au widget via les options validate et validatecommand.
    #
    #     Le paramètre %P : Dans votre code, la commande de validation est définie par vcmd = (master.register(self.validate_input), '%P'). Le %P est un spécificateur de Tkinter qui transmet la nouvelle valeur que l'entrée aura si le caractère saisi est accepté.
    #
    #     La logique de validation : La méthode validate_input prend cette nouvelle chaîne de caractères (new_value) et applique une logique de vérification.
    #
    #         Votre code vérifie d'abord si la longueur de la nouvelle chaîne (new_value) ne dépasse pas la longueur du format attendu (self.format_string). Si c'est le cas, la saisie est refusée.
    #
    #         Si la chaîne est vide (l'utilisateur a tout effacé), la validation est acceptée.
    #
    #         Pour les autres cas, la méthode renvoie simplement True, ce qui est une implémentation simplifiée. Elle suppose que la saisie est valide tant qu'elle ne dépasse pas la longueur du format.
    #
    #     La valeur de retour : La méthode doit retourner une valeur booléenne :
    #
    #         True : Tkinter accepte la saisie et met à jour le contenu du widget.
    #
    #         False : Tkinter rejette la saisie, le caractère tapé n'est pas affiché, et le contenu du widget reste inchangé.
    #
    # Amélioration de la validation
    #
    # L'implémentation actuelle est un bon point de départ, mais elle ne valide pas le contenu de manière très stricte. Par exemple, un utilisateur pourrait taper "ABC" dans un champ de date, et tant que la longueur correspond, ce serait accepté.
    #
    # Pour une validation plus robuste, vous pouvez améliorer la méthode validate_input en utilisant des expressions régulières (regex). Une regex permet de vérifier si la chaîne de caractères correspond à un motif spécifique, comme \d{4} pour une année à quatre chiffres ou \d{2} pour un jour à deux chiffres.
    def _format_to_regex(self, format_string):
        # Converts a format string like "%Y-%m-%d" into a regex like "\d{4}-\d{2}-\d{2}"
        # This is a complex task and requires careful mapping of strftime codes.
        # For this example, let's assume a simple mapping.
        regex_pattern = format_string
        regex_pattern = regex_pattern.replace("YYYY", r"\d{4}")
        regex_pattern = regex_pattern.replace("MM", r"\d{2}")
        regex_pattern = regex_pattern.replace("DD", r"\d{2}")
        regex_pattern = regex_pattern.replace("hh", r"\d{2}")
        regex_pattern = regex_pattern.replace("mm", r"\d{2}")
        regex_pattern = regex_pattern.replace("ss", r"\d{2}")
        # Add more mappings as needed
        return "^" + regex_pattern + "$"

    def validate_input(self, new_value):
        # try:
        #     # First, check if the format matches
        #     # We will use a simplified check here. A more advanced version might
        #     # use a regular expression for a more precise format.
        #     if len(new_value) > len(self.format_str):
        #         return False
        #
        #     # If the user is deleting characters, the validation should pass
        #     if new_value == "":
        #         return True
        #
        #     # Attempt to parse the date/time. If it fails, it's not valid yet.
        #     # We'll use a simplified check that allows partial input.
        #     # This part is a simplification. A full implementation would need
        #     # to check the input against a regex derived from the format_string.
        #     # For now, we'll allow any input that is a valid prefix.
        #     return True
        #
        # except ValueError:
        #     return False
        if new_value == "":
            return True
        # Check if the new value is a valid prefix of the full format
        # This is a basic example; a more complex one would be needed for a full solution
        if new_value and self.format_regex.startswith(new_value):
            return True
        return False

    # def construct_fields(self, format_spec, kwargs):
    #     self._fields = []
    #     self._widgets = []
    #     self._namedFields = {}
    #
    #     # Simple parsing of format string, will be more complex later
    #     tokens = re.findall(r'(\w+|\W+)', format_spec)
    #
    #     for token in tokens:
    #         field_obj = None
    #         if token == 'YYYY':
    #             field_obj = YearField(self, self, kwargs.get('year', datetime.datetime.now().year))
    #         elif token == 'MM':
    #             months = [(calendar.month_name[i], i) for i in range(1, 13)]
    #             field_obj = MonthField(self, self, kwargs.get('month', datetime.datetime.now().month), choices=months)
    #         elif token == 'DD':
    #             field_obj = DayField(self, self, kwargs.get('day', datetime.datetime.now().day))
    #         elif token == 'hh':
    #             hours = [ (f"{h:02d}", h) for h in range(24)]
    #             field_obj = HourField(self, self, kwargs.get('hour', datetime.datetime.now().hour), choices=hours)
    #         elif token == 'mm':
    #             minutes = [ (f"{m:02d}", m) for m in range(60)]
    #             field_obj = MinuteField(self, self, kwargs.get('minute', datetime.datetime.now().minute), choices=minutes)
    #         elif token == 'ss':
    #             seconds = [ (f"{s:02d}", s) for s in range(60)]
    #             field_obj = SecondField(self, self, kwargs.get('second', datetime.datetime.now().second), choices=seconds)
    #         else:  # separators
    #             label = ttk.Label(self, text=token)
    #             self._widgets.append(label)
    #             label.pack(side=tk.LEFT)
    #             continue
    #
    #         if field_obj:
    #             self._fields.append(field_obj)
    #             self._widgets.append(field_obj.entry)
    #             field_obj.entry.pack(side=tk.LEFT)
    #
    #     if self._fields:
    #         self._fields[self.current_field_index].entry.focus_set()

    # def _parse_format(self, fmt, kwargs):
    #     state = None
    #     for c in fmt:
    #         klass = next((k for k in self.formats if k.matches(c)), None)
    #         if state is not None and state.__class__ is klass:
    #             state.append(c)
    #         else:
    #             if state is not None:
    #                 field = state.createField(self, self, **state.keywordArgs(kwargs))
    #                 # self.add_field(state.valueName, field)
    #                 if isinstance(field, (tk.Label, ttk.Label)):
    #                     # self.widgets.append((field, {}))
    #                     field.pack(side=tk.LEFT, padx=1)
    #                 else:
    #                     self.add_field(state.valueName, field)
    #             state = klass(c)
    #     if state is not None:
    #         field = state.createField(self, self, **state.keywordArgs(kwargs))
    #         # self.add_field(state.valueName, field)
    #         if isinstance(field, (tk.Label, ttk.Label)):
    #             # self.widgets.append((field, {}))
    #             field.pack(side=tk.LEFT, padx=1)
    #         else:
    #             self.add_field(state.valueName, field)

    # def _setup_widgets(self):
    #     for widget_or_str, widget_kw in self._widgets:
    #         # if isinstance(widget_or_str, str):
    #         #     label = ttk.Label(self, text=widget_or_str)
    #         #     label.pack(side=tk.LEFT, padx=1)
    #         # else:
    #         #     widget_or_str.pack(side=tk.LEFT, padx=1)
    #         if isinstance(widget_or_str, (tk.Label, ttk.Label)):
    #             widget_or_str.pack(side=tk.LEFT, padx=1)
    #         else:
    #             widget_or_str.pack(side=tk.LEFT, padx=1)

    # def bind_events(self):
    #     self.bind_all('<Right>', lambda e: self.focus_next_field())
    #     self.bind_all('<Left>', lambda e: self.focus_prev_field())
    #     self.bind_all('<Up>', lambda e: self.increment_field())
    #     self.bind_all('<Down>', lambda e: self.decrement_field())
    #
    # def add_field(self, name, field):
    #     if name is not None:
    #         self._namedFields[name] = field
    #     self.fields.append(field)
    #     # self._widgets.append((field, {}))
    #     field.pack(side=tk.LEFT, padx=1)
    #
    # def focus_next_field(self, current_field):
    #     # try:
    #     #     current_index = self._fields.index(current_field)
    #     #     next_index = (current_index + 1) % len(self._fields)
    #     #     self._fields[next_index].entry.focus_set()
    #     #     self.current_field_index = next_index
    #     # except ValueError:
    #     #     pass
    #     if current_field:
    #         try:
    #             self.current_focus_idx = self.fields.index(current_field)
    #         except ValueError:
    #             self.current_focus_idx = -1
    #
    #     if self.current_focus_idx < len(self.fields) - 1:
    #         self.current_focus_idx += 1
    #         self.fields[self.current_focus_idx].entry.focus_set()
    #
    # def focus_prev_field(self, current_field):
    #     # try:
    #     #     current_index = self._fields.index(current_field)
    #     #     prev_index = (current_index - 1 + len(self._fields)) % len(self._fields)
    #     #     self._fields[prev_index].entry.focus_set()
    #     #     self.current_field_index = prev_index
    #     # except ValueError:
    #     #     pass
    #     if current_field:
    #         try:
    #             self.current_focus_idx = self.fields.index(current_field)
    #         except ValueError:
    #             self.current_focus_idx = -1
    #
    #     if self.current_focus_idx > 0:
    #         self.current_focus_idx -= 1
    #         self.fields[self.current_focus_idx].entry.focus_set()
    #
    # def refresh(self):
    #     # A Tkinter-specific refresh might involve updating StringVar values
    #     # or redrawing widgets. For ttk.Entry, this is handled by StringVar.
    #     pass
    #
    # def validate_change(self, field, value):
    #     # Placeholder for more complex validation logic
    #     return value
    #
    # def increment_field(self, event=None):
    #     if self.current_focus_idx != -1:
    #         field = self.fields[self.current_focus_idx]
    #         try:
    #             current_val = int(field.GetValue())
    #             field.SetValue(current_val + 1, notify=True)
    #         except (ValueError, TypeError):
    #             pass
    #
    # def decrement_field(self, event=None):
    #     if self.current_focus_idx != -1:
    #         field = self.fields[self.current_focus_idx]
    #         try:
    #             current_val = int(field.GetValue())
    #             field.SetValue(current_val - 1, notify=True)
    #         except (ValueError, TypeError):
    #             pass
    #
    # def popup_choices(self, field):
    #     # if not field.GetChoices():
    #     #     return
    #     #
    #     # x = field.entry.winfo_rootx()
    #     # y = field.entry.winfo_rooty() + field.entry.winfo_height()
    #     #
    #     # popup = tk.Menu(self.master, tearoff=0)
    #     # for label, value in field.GetChoices():
    #     #     popup.add_command(label=label, command=lambda v=value: self.set_field_value(field, v))
    #     #
    #     # popup.post(x, y)
    #     choices = field.GetChoices()
    #     if choices:
    #         self.popup_menu = Menu(self, tearoff=0)
    #         self.popup_field = field
    #         for label, value in choices:
    #             self.popup_menu.add_command(
    #                 label=label,
    #                 command=lambda v=value: self.select_choice(v)
    #             )
    #         x, y = field.entry.winfo_rootx(), field.entry.winfo_rooty()
    #         self.popup_menu.post(x, y + field.entry.winfo_height())
    #
    # def select_choice(self, value):
    #     if self.popup_field:
    #         self.popup_field.SetValue(value, notify=True)
    #         self.popup_field = None
    #         self.popup_menu.destroy()
    #
    # def set_field_value(self, field, value):
    #     field.SetValue(value)

    def SetValue(self, dt):
        if dt:
            formatted_value = dt.strftime(self.format_str)
            self.value_var.set(formatted_value)
        else:
            self.value_var.set("")

    # def get_value(self):
    #     value_list = [f.GetValue() for f in self.fields if isinstance(f, Field)]
    #     return tuple(value_list)

    def GetValue(self):
        # try:
        #     # We assume a fixed order for now
        #     day = int(self._fields[0].GetValue())
        #     month = int(self._fields[1].GetValue())
        #     year = int(self._fields[2].GetValue())
        #     hour = int(self._fields[3].GetValue()) if len(self._fields) > 3 else 0
        #     minute = int(self._fields[4].GetValue()) if len(self._fields) > 4 else 0
        #     second = int(self._fields[5].GetValue()) if len(self._fields) > 5 else 0
        #
        #     return datetime.datetime(year, month, day, hour, minute, second)
        # except (ValueError, IndexError):
        #     return None
        try:
            return datetime.datetime.strptime(self.value_var.get(), self.format_str)
        except ValueError:
            return None


class SmartDateTimeCtrl(ttk.Frame):
    def __init__(self, master, date_format="%Y-%m-%d", time_format="%H:%M:%S", show_date=True, show_time=True, **kwargs):
        super().__init__(master)
        self.master = master
        self.date_format = date_format
        self.time_format = time_format
        self.show_date = show_date
        self.show_time = show_time
        self.callback = kwargs.pop("callback", None)
        self.value = None

        self.date_entry = None
        self.time_entry = None
        self.time_checkbox_var = tk.BooleanVar(value=show_time)
        self.time_checkbox = None

        self._setup_widgets()

    def _setup_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        if self.show_date:
            date_frame = ttk.Frame(main_frame)
            date_frame.pack(side=tk.LEFT, padx=5, pady=5)
            # # self.date_entry = Entry(date_frame, format=self.date_format, **{'year': datetime.date.today().year, 'month': datetime.date.today().month, 'day': datetime.date.today().day})
            # self.date_entry = Entry(date_frame, format_string=self.date_format,
            #                         day=datetime.date.today().day,
            #                         month=datetime.date.today().month,
            #                         year=datetime.date.today().year)
            self.date_entry = Entry(date_frame, format_string=self.date_format)
            self.date_entry.pack(side=tk.LEFT)
            self.date_entry.SetValue(datetime.datetime.now())

        if self.show_time:
            time_frame = ttk.Frame(main_frame)
            time_frame.pack(side=tk.LEFT, padx=5, pady=5)
            # # self.time_entry = Entry(time_frame, format=self.time_format, **{'hour': datetime.datetime.now().hour, 'minute': datetime.datetime.now().minute, 'second': datetime.datetime.now().second})
            # self.time_entry = Entry(time_frame, format_string=self.time_format,
            #                         hour=datetime.datetime.now().hour,
            #                         minute=datetime.datetime.now().minute,
            #                         second=datetime.datetime.now().second)
            self.time_entry = Entry(time_frame, format_string=self.time_format)
            self.time_entry.pack(side=tk.LEFT)
            self.time_entry.SetValue(datetime.datetime.now())

        if self.show_date:
            # if self.show_date and self.show_time:
            # self.time_checkbox = ttk.Checkbutton(self, text="Include Time")
            self.time_checkbox = ttk.Checkbutton(self, text="Include Time",
                                                 variable=self.time_checkbox_var,
                                                 command=self.on_checkbox_toggle)
            self.time_checkbox.pack(side=tk.LEFT, padx=5, pady=5)
            # self.time_checkbox.bind("<Button-1>", self.on_checkbox_click)

    def on_checkbox_toggle(self):
        if self.time_checkbox_var.get():
            self.time_entry.pack(side=tk.LEFT, padx=5, pady=5)
        else:
            self.time_entry.pack_forget()

    # def on_checkbox_click(self, event):
    #     if self.time_entry:
    #         state = self.time_entry.winfo_viewable()
    #         if state:
    #             self.time_entry.pack_forget()
    #         else:
    #             self.time_entry.pack(side=tk.LEFT, padx=5, pady=5)

    def GetValue(self):
        # date_tuple = self.date_entry.get_value() if self.date_entry else None
        date_val = self.date_entry.GetValue() if self.date_entry else None
        # time_tuple = self.time_entry.get_value() if self.time_entry and self.time_entry.winfo_viewable() else None
        time_val = self.time_entry.GetValue() if self.time_entry and self.time_checkbox_var.get() else None

        # date_val = datetime.date(*date_tuple) if date_tuple else None
        # time_val = datetime.time(*time_tuple) if time_tuple else None

        if date_val and time_val:
            # return datetime.datetime.combine(date_val, time_val)
            return datetime.datetime.combine(date_val.date(), time_val.time())
        elif date_val:
            # return date_val
            return date_val.date()
        # elif time_val:
        #     return time_val
        #     return time_val.time()
        return None

    def SetValue(self, dt):
        # if isinstance(dt, datetime.datetime):
        #     if self.date_entry:
        #         self.date_entry.fields[0].SetValue(dt.year)
        #         self.date_entry.fields[1].SetValue(dt.month)
        #         self.date_entry.fields[2].SetValue(dt.day)
        #     if self.time_entry:
        #         self.time_entry.fields[0].SetValue(dt.hour)
        #         self.time_entry.fields[1].SetValue(dt.minute)
        #         self.time_entry.fields[2].SetValue(dt.second)
        # elif isinstance(dt, datetime.date):
        #     if self.date_entry:
        #         self.date_entry.fields[0].SetValue(dt.year)
        #         self.date_entry.fields[1].SetValue(dt.month)
        #         self.date_entry.fields[2].SetValue(dt.day)
        #     if self.time_checkbox and self.time_entry:
        #         self.time_checkbox.set(0)
        #         self.time_entry.pack_forget()

        self.value = dt
        if isinstance(dt, datetime.datetime):
            if self.date_entry:
                # self.date_entry.named_fields['year'].SetValue(dt.year)
                # self.date_entry.named_fields['month'].SetValue(dt.month)
                # self.date_entry.named_fields['day'].SetValue(dt.day)
                self.date_entry.SetValue(dt)
            if self.time_entry:
                self.time_checkbox_var.set(True)
                # self.time_entry.named_fields['hour'].SetValue(dt.hour)
                # self.time_entry.named_fields['minute'].SetValue(dt.minute)
                # self.time_entry.named_fields['second'].SetValue(dt.second)
                self.time_entry.SetValue(dt)
        elif isinstance(dt, datetime.date):
            if self.date_entry:
                # self.date_entry.named_fields['year'].SetValue(dt.year)
                # self.date_entry.named_fields['month'].SetValue(dt.month)
                # self.date_entry.named_fields['day'].SetValue(dt.day)
                self.date_entry.SetValue(datetime.datetime.combine(dt, datetime.time()))
            if self.time_checkbox:
                self.time_checkbox_var.set(False)
                self.on_checkbox_toggle()


# class DateTimeSpanCtrl(ttk.Frame):
#     def __init__(self, master, start_ctrl, end_ctrl, **kwargs):
#         super().__init__(master)
#
#         self.start_ctrl = start_ctrl
#         self.end_ctrl = end_ctrl
#         self.min_span = kwargs.pop("minSpan", None)
#
#         self.start_ctrl.pack(side=tk.LEFT)
#         self.end_ctrl.pack(side=tk.LEFT)
#
#         # Example of binding.
#         # This part requires more complex event handling in Tkinter
#         # to properly propagate events.
#         self.start_ctrl.bind("<<EntryChanged>>", self.on_change)
#         self.end_ctrl.bind("<<EntryChanged>>", self.on_change)
#
#     def on_change(self, event):
#         start_dt = self.start_ctrl.GetValue()
#         end_dt = self.end_ctrl.GetValue()
#
#         if start_dt and end_dt:
#             span = end_dt - start_dt
#             if self.min_span and span < self.min_span:
#                 print("Span is less than minimum allowed.") # Or show a message to the user


# Exemple d'utilisation
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Test SmartDateTimeCtrl Tkinter")

    def my_callback(new_value):
        print("Value changed:", new_value)

    # # Create the main frame
    # main_frame = ttk.Frame(root, padding="10")
    # main_frame.pack(fill=tk.BOTH, expand=True)

    dt_ctrl_frame = ttk.LabelFrame(root, text="SmartDateTimeCtrl")
    # dt_ctrl_frame = ttk.LabelFrame(main_frame, text="SmartDateTimeCtrl")
    dt_ctrl_frame.pack(padx=10, pady=5, fill=tk.X)

    # # --- Date and Time Controls ---
    # date_label = ttk.Label(main_frame, text="Date and Time Control")
    # date_label.pack(padx=5, pady=5, anchor='w')

    # Simple DateTime control
    # dt_ctrl = SmartDateTimeCtrl(dt_ctrl_frame, date_format="YYYY-MM-DD", time_format="hh:mm:ss", callback=my_callback)
    dt_ctrl = SmartDateTimeCtrl(dt_ctrl_frame, date_format="%Y-%m-%d", time_format="%H:%M:%S", callback=my_callback)
    dt_ctrl.pack(fill=tk.X, padx=5, pady=5)

    # # This part replaces the wx.Panel from the original example
    # pnl1 = ttk.Frame(main_frame)
    # pnl1.pack(padx=5, pady=5)
    #
    # # Simple date format
    # date_entry = Entry(pnl1, format_string="DD/MM/YYYY")
    # date_entry.pack(side=tk.LEFT)
    #
    # # Date and Time format
    # datetime_entry = Entry(pnl1, format_string="DD/MM/YYYY hh:mm:ss")
    # datetime_entry.pack(side=tk.LEFT, padx=10)
    #
    # # --- DateTimeSpanCtrl ---
    # span_label = ttk.Label(main_frame, text="Date and Time Span Control")
    # span_label.pack(padx=5, pady=5, anchor='w')
    #
    # pnl2 = ttk.Frame(main_frame)
    # pnl2.pack(padx=5, pady=5)
    #
    # start_ctrl = Entry(pnl2, format_string="YYYY-MM-DD hh:mm")
    # end_ctrl = Entry(pnl2, format_string="YYYY-MM-DD hh:mm")
    #
    # span_ctrl = DateTimeSpanCtrl(pnl2, start_ctrl, end_ctrl, minSpan=datetime.timedelta(hours=1))
    # span_ctrl.pack()

    # We add a way to print the values to test
    # def print_values():
    #     print("Date Entry Value:", date_entry.GetValue())
    #     print("DateTime Entry Value:", datetime_entry.GetValue())
    #     print("Start Span Value:", start_ctrl.GetValue())
    #     print("End Span Value:", end_ctrl.GetValue())

    def get_value():
        # print("Current value:", dt_ctrl.GetValue())
        val = dt_ctrl.GetValue()
        print("Current value:", val, type(val))

    # print_btn = ttk.Button(main_frame, text="Print Values", command=print_values)
    # print_btn.pack(pady=10)

    get_btn = ttk.Button(dt_ctrl_frame, text="Get Value", command=get_value)
    get_btn.pack(pady=5)

    def set_value_to_now():
        dt_ctrl.SetValue(datetime.datetime.now())

    set_btn_now = ttk.Button(dt_ctrl_frame, text="Set to Now", command=set_value_to_now)
    set_btn_now.pack(pady=5)

    root.mainloop()
