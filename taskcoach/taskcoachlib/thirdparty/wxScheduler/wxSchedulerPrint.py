#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .wxSchedulerCore import wxSchedulerCore


class wxSchedulerPrint(wxSchedulerCore):
    """
    Classe spécialisée pour l'impression du planificateur.
    Hérite de wxSchedulerCore et permet de dessiner le planning sur un contexte graphique pour l'impression.
    """
    def __init__(self, dc):
        """
        Initialise le planificateur d'impression avec le contexte graphique donné.
        :param dc: Contexte de dessin wxPython (Device Context) à utiliser pour l'impression.
        """
        super().__init__()

        self.SetDc(dc)

    def Draw(self, page):
        """
        Dessine le planning sur le bitmap pour la page spécifiée.
        :param page: Numéro de page à dessiner. Si None, dessine la page courante.
        :return: Le bitmap généré avec le contenu du planning.
        """
        if page is None:
            self.DrawBuffer()
        else:
            self.pageNumber = page
            self.DrawBuffer()

        return self._bitmap

    def GetSize(self):
        """
        Retourne un objet wx.Size représentant la taille de la page à imprimer.
        :return: wx.Size de la page.
        """
        return self.GetDc().GetSize()

    def Refresh(self):
        """
        Redéfinition de la méthode Refresh, inutile pour l'impression (ne fait rien).
        """
        pass
