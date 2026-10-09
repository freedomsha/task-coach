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

# from builtins import str
# from builtins import object
from taskcoachlib import patterns
# try:
from pubsub import pub
# except ImportError:
#    from taskcoachlib.thirdparty.pubsub import pub
# else:
#    from wx.lib.pubsub import pub
from taskcoachlib.i18n import _
import wx


class AttributeSync(object):
    """
    Classe utilisée pour garder un attribut d'un objet de domaine synchronisé avec
    un contrôle dans une boîte de dialogue. Si l'utilisateur modifie
    la valeur à l'aide du contrôle,
    l'objet de domaine est modifié à l'aide de la commande appropriée.
    Si l'attribut de l'objet de domaine est modifié
    (par exemple dans une autre boîte de dialogue),
    la valeur du contrôle est mise à jour.
    """

    def __init__(self, attributeGetterName, entry, currentValue, items,
                 commandClass, editedEventType, changedEventType, callback=None,
                 **kwargs):
        """
        Initialise l'instance d'AttributeSync.
        Args:
            attributeGetterName (str) : Nom de la méthode pour obtenir l'attribut de l'objet.
            entry (wx.Control) : Contrôle dans la boîte de dialogue qui affiche et modifie l'attribut.
            currentValue (any) : Valeur actuelle de l'attribut.
            items (list) : Liste d'objets dont l'attribut doit être synchronisé.
            commandClass (type) : Classe de commande à utiliser pour modifier l'objet.
            editedEventType (str) : Type d'événement édité qui déclenche la mise à jour de l'attribut.
            changedEventType (str) : Type d'événement changé qui déclenche la mise à jour de l'objet.
            callback (callable, optional) : Fonction de rappel à appeler après la modification de l'attribut.
            **kwargs (dict, optional) : Arguments supplémentaires pour la classe de commande.
        """
        self._getter = attributeGetterName
        self._entry = entry
        self._currentValue = currentValue
        self._items = items
        self._commandClass = commandClass
        self.__commandKwArgs = kwargs
        self.__changedEventType = changedEventType
        self.__callback = callback
        entry.Bind(editedEventType, self.onAttributeEdited)
        if len(items) == 1:
            self.__start_observing_attribute(changedEventType, items[0])

    def onAttributeEdited(self, event):
        """
        Méthode appelée lorsque l'utilisateur modifie la valeur du contrôle.

        Args :
            event (wx.Event) : Événement déclenché par la modification de l'attribut.
        Returns :
            None
        """
        event.Skip()
        new_value = self.getValue()
        if new_value != self._currentValue:
            self._currentValue = new_value
            commandKwArgs = self.commandKwArgs(new_value)
            self._commandClass(None, self._items, **commandKwArgs).do()  # pylint: disable=W0142
            self.__invokeCallback(new_value)

    def onAttributeChanged_Deprecated(self, event):  # pylint: disable=W0613
        """
        Méthode dépréciée appelée lorsque l'attribut de l'objet est modifié.

        Args :
            event (wx.Event) : Événement déclenché par la modification de l'attribut.
        """
        if self._entry:
            new_value = getattr(self._items[0], self._getter)()
            if new_value != self._currentValue:
                self._currentValue = new_value
                self.setValue(new_value)
                self.__invokeCallback(new_value)
        else:
            self.__stop_observing_attribute()

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
            else:
                self.__stop_observing_attribute()

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

    def setValue(self, new_value):
        """
        Définit la valeur du contrôle.

        Args :
            new_value (any) : Nouvelle valeur à définir.
        """
        self._entry.SetValue(new_value)

    def getValue(self):
        """
        Obtient la valeur actuelle du contrôle.

        Returns :
            any : Valeur actuelle du contrôle.
        """
        return self._entry.GetValue()

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
                wx.MessageBox(str(e), _("Error"), wx.OK)

    def __start_observing_attribute(self, eventType, eventSource):
        """
        Commence à observer les changements de l'attribut.

        Args :
            eventType (str) : Type d'événement à observer.
        eventSource (object) : Source de l'événement à observer.
        """
        if eventType.startswith("pubsub"):
            pub.subscribe(self.onAttributeChanged, eventType)
        else:
            patterns.Publisher().registerObserver(self.onAttributeChanged_Deprecated,
                                                  eventType=eventType,
                                                  eventSource=eventSource)
    
    def __stop_observing_attribute(self):
        """
        Arrête d'observer les changements de l'attribut.
        """
        try:
            pub.unsubscribe(self.onAttributeChanged, self.__changedEventType)
        except pub.TopicNameError:
            pass
        patterns.Publisher().removeObserver(self.onAttributeChanged_Deprecated)


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
            newValue (wx.Colour) : Nouvelle couleur à définir.
        """
        self._entry.SetColor(newValue)

    def getValue(self):
        """
        Obtient la couleur actuelle du contrôle.

        Returns :
            wx.Colour : Couleur actuelle du contrôle.
        """
        return self._entry.GetColor()
