#! /usr/bin/env python
import wx
from wx.lib import newevent

# Define new event types and binders
TimeLineSelectionEvent, EVT_TIMELINE_SELECTED = wx.lib.newevent.NewEvent()
TimeLineActivationEvent, EVT_TIMELINE_ACTIVATED = wx.lib.newevent.NewEvent()


class HotMap(object):
    """
    Gardez une trace de quel nœud qui se trouve quelque part.

    Cette classe aide à gérer les nœuds et leurs positions dans la chronologie.
    """

    def __init__(self, parent=None):
        """
        Initialisez l'instance HotMap.

        Args:
            parent : le nœud parent (la valeur par défaut est Aucun).
        """
        self.parent = parent
        self.nodes = []
        self.rects = {}
        self.children = {}
        super().__init__()

    def append(self, node, rect):
        """
        Ajoutez un nœud et son rectangle au HotMap.

        Args:
            node : Le nœud à ajouter.
            rect (wx.Rect) : Le rectangle représentant la position du nœud.
        """
        self.nodes.append(node)
        self.rects[node] = rect
        self.children[node] = HotMap(node)

    def __getitem__(self, node):
        """
        Obtenez la HotMap enfant pour un nœud donné.

        Args:
            node : Le nœud pour lequel obtenir la HotMap enfant.

        Returns:
            HotMap : La HotMap enfant.
        """
        return self.children[node]

    def findNodeAtPosition(self, position, parent=None):
        """
        Récupère le nœud à la position donnée.

        Args:
            position (wx.Point) : La position à vérifier.
            parent : Le nœud parent (la valeur par défaut est Aucun).

        Returns:
            Le nœud à la position donnée ou le nœud parent si aucun nœud n'est trouvé.
        """
        for node, rect in list(self.rects.items()):
            if rect.Contains(position):
                return self[node].findNodeAtPosition(position, node)
        return parent

    def firstNode(self):
        """
        Obtenez le premier nœud du HotMap.

        Returns:
            Le premier nœud ou Aucun s'il n'y a aucun nœud.
        """
        return self.nodes[0] if self.nodes else None

    def lastNode(self, parent=None):
        """
        Obtenez le dernier nœud du HotMap.

        Args:
            parent : Le nœud parent (la valeur par défaut est Aucun).

        Returns:
            Le dernier nœud ou le nœud parent s'il n'y a pas de nœuds.
        """
        if self.nodes:
            last = self.nodes[-1]
            return self[last].lastNode(last)
        else:
            return parent

    def findNode(self, target):
        """
        Recherchez la HotMap contenant le nœud cible.

        Args:
            target : Le nœud cible à rechercher.

        Renvoie :
            HotMap : La HotMap contenant le nœud cible ou Aucun sinon trouvé.
        """
        if target in self.nodes:
            return self
        for node in self.nodes:
            result = self[node].findNode(target)
            if result:
                return result
        return None

    def nextChild(self, target):
        """
        Obtenez le nœud enfant suivant après le nœud cible.

        Args:
            target : Le nœud cible.

        Returns:
            Le nœud enfant suivant.
        """
        index = self.nodes.index(target)
        index = min(index + 1, len(self.nodes) - 1)
        return self.nodes[index]

    def previousChild(self, target):
        """
        Récupère le nœud enfant précédent avant le nœud cible.

        Args:
            target : Le nœud cible.

        Returns:
            Le nœud enfant précédent.
        """
        index = self.nodes.index(target)
        index = max(index - 1, 0)
        return self.nodes[index]

    def firstChild(self, target):
        """
        Récupère le premier nœud enfant du nœud cible.

        Args:
            target : Le nœud cible.

        Returns:
            Le premier nœud enfant ou le nœud cible s'il n'a pas enfants.
        """
        children = self[target].nodes
        if children:
            return children[0]
        else:
            return target


class TimeLine(wx.Panel):
    """
    Un widget de chronologie pour afficher et interagir avec une chronologie d'événements.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialisez l'instance TimeLine.

        Args:
            *args: liste d'arguments de longueur variable.
            **kwargs: arguments de mots clés arbitraires.
        """
        self.model = kwargs.pop("model", [])
        self.padding = kwargs.pop("padding", 3)
        self.adapter = kwargs.pop("adapter", DefaultAdapter())
        self.selectedNode = None
        self.backgroundColour = wx.WHITE
        self._buffer = wx.Bitmap(20, 20)  # Have a default buffer ready
        self.DEFAULT_PEN = wx.Pen(wx.BLACK, 1, wx.PENSTYLE_SOLID)
        self.SELECTED_PEN = wx.Pen(wx.WHITE, 2, wx.PENSTYLE_SOLID)
        kwargs["style"] = (
            wx.TAB_TRAVERSAL
            | wx.NO_BORDER
            | wx.FULL_REPAINT_ON_RESIZE
            | wx.WANTS_CHARS
        )
        super().__init__(*args, **kwargs)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_UP, self.OnClickRelease)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        self.OnSize(None)

    def SetBackgroundColour(self, colour):
        """
        Définissez la couleur d'arrière-plan de la timeline.

        Args:
            colour (wx.Colour) : La couleur d'arrière-plan à définir.
        """
        self.backgroundColour = colour

    def Refresh(self, eraseBackground=True, rect=None):
        """
        Actualisez le dessin de la chronologie.
        """
        # Refresh(self)
        # Signature of method 'Refresh()' does not match signature of the base method in class 'Window'
        # Refresh(self, eraseBackground=True, rect=None)
        self.UpdateDrawing()

    def OnPaint(self, event):
        """
        Gérer l'événement paint.

        Args :
            event (wx.PaintEvent) : L'événement paint.
        """
        dc = wx.BufferedPaintDC(self, self._buffer)

    def OnSize(self, event):
        """
        Gérez l'événement de redimensionnement.

        Args :
            event (wx.SizeEvent): L'événement de redimensionnement.
        """
        # Le tampon est initialisé ici, de sorte qu'il ait toujours
        # la même taille que la fenêtre.
        width, height = self.GetClientSize()
        if width <= 0 or height <= 0:
            return
        # Créer un nouveau bitmap hors écran : ce bitmap contiendra toujours le
        # dessin actuel, il peut donc être utilisé pour enregistrer l'image dans
        # un fichier, ou autre.
        # wxPyDeprecationWarning: Call to deprecated item EmptyBitmap. Use :class:`wx.Bitmap` instead
        self._buffer = wx.Bitmap(width, height)
        self.UpdateDrawing()

    def OnClickRelease(self, event):
        """
        Gérez l'événement de relâchement du bouton gauche de la souris.

        Args :
            event (wx.MouseEvent): L'événement de la souris.
        """
        event.Skip()
        self.SetFocus()
        point = event.GetPosition()
        node = self.hot_map.findNodeAtPosition(point)
        self.SetSelected(node, point)

    def OnDoubleClick(self, event):
        """
        Gérez l'événement de double-clic du bouton gauche de la souris.

        Args :
            event (wx.MouseEvent): L'événement de la souris.
        """
        point = event.GetPosition()
        node = self.hot_map.findNodeAtPosition(point)
        if node:
            wx.PostEvent(self, TimeLineActivationEvent(node=node, point=point))

    def OnKeyUp(self, event):
        """
        Gérer l'événement key up.

        Args :
            event (wx.KeyEvent): L'événement clé.
        """
        # TODO : Review the method
        # because Property 'KeyCode' cannot be read
        event.Skip()
        if not self.hot_map:
            return
        # if event.KeyCode == wx.WXK_HOME:
        if event.GetKeyCode == wx.WXK_HOME:
            self.SetSelected(self.hot_map.firstNode())
            return
        elif event.GetKeyCode == wx.WXK_END:
            self.SetSelected(self.hot_map.lastNode())
            return
        if not self.selectedNode:
            return
        if event.GetKeyCode == wx.WXK_RETURN:
            wx.PostEvent(self, TimeLineActivationEvent(node=self.selectedNode))
            return
        hot_map = self.hot_map.findNode(self.selectedNode)
        if hot_map is None:
            newSelection = self.hot_map.firstNode()
        elif event.GetKeyCode == wx.WXK_DOWN:
            newSelection = hot_map.nextChild(self.selectedNode)
        elif event.GetKeyCode == wx.WXK_UP:
            newSelection = hot_map.previousChild(self.selectedNode)
        elif event.GetKeyCode == wx.WXK_RIGHT:
            newSelection = hot_map.firstChild(self.selectedNode)
        elif event.GetKeyCode == wx.WXK_LEFT and hot_map.parent:
            newSelection = hot_map.parent
        else:
            newSelection = self.selectedNode
        self.SetSelected(newSelection)

    def GetSelected(self):
        """
        Récupère le nœud actuellement sélectionné.

        Returns :
            Le nœud actuellement sélectionné.
        """
        return self.selectedNode

    def SetSelected(self, node, point=None):
        """
        Définissez le nœud donné comme sélectionné dans le widget de chronologie.

        Args :
            node : Le nœud à sélectionner.
            point (wx.Point) : (optional) La position du nœud (la valeur par défaut est None).
        """
        if node == self.selectedNode:
            return
        self.selectedNode = node
        self.Refresh()
        if node:
            wx.PostEvent(self, TimeLineSelectionEvent(node=node, point=point))

    def UpdateDrawing(self):
        """
        Mettre à jour le dessin de la chronologie.
        """
        dc = wx.BufferedDC(wx.ClientDC(self), self._buffer)
        self.Draw(dc)

    def Draw(self, dc):
        """
        Dessinez la chronologie sur le contexte de l'appareil.

        Args :
            dc (wx.DC) : Le contexte de l'appareil.
        """
        self.hot_map = HotMap()
        brush = wx.Brush(self.backgroundColour)
        dc.SetBackground(brush)
        dc.Clear()
        dc.SetFont(self.FontForLabels(dc))
        if self.model:
            bounds = self.adapter.bounds(self.model)
            self.min_start = float(min(bounds))
            self.max_stop = float(max(bounds))
            if self.max_stop - self.min_start < 100:
                self.max_stop += 100
            self.length = self.max_stop - self.min_start
            self.width, self.height = dc.GetSize()
            labelHeight = (
                dc.GetTextExtent("ABC")[1] + 2
            )  # Laissez de la place aux étiquettes de temps
            self.DrawParallelChildren(
                dc,
                self.model,
                labelHeight,
                self.height - labelHeight,
                self.hot_map,
            )
            self.DrawNow(dc)

    def FontForLabels(self, dc):
        """
        Renvoie la police GUI par défaut, mise à l'échelle pour l'impression si nécessaire.

        Args :
            dc (wx.DC) : Le contexte du périphérique.

        Returns :
            font (wx.Font) : La police mise à l'échelle.
        """
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        scale = dc.GetPPI()[0] // wx.ScreenDC().GetPPI()[0]
        font.SetPointSize(scale * font.GetPointSize())
        return font

    def DrawBox(
        self, dc, node, y, h, hot_map, isSequentialNode=False, depth=0
    ):
        """
        Dessinez une boîte représentant un nœud.

        Args :
            dc (wx.DC) : Le contexte du périphérique.
            node : Le nœud à dessiner.
            y (int) : Le y- coordinate.
            h (int) : La hauteur de la boîte.
            hot_map (HotMap) : L'instance de HotMap.
            isSequentialNode (bool, optional) : Indique si le nœud est séquentiel (la valeur par défaut est False).
            depth (int, optional) : la profondeur du nœud (la valeur par défaut est 0).
        """
        if h < self.padding:
            return
        start, stop = self.adapter.start(node), self.adapter.stop(node)
        if start is None:
            start = self.min_start - 10
        if stop is None:
            stop = self.max_stop + 10
        start, stop = min(start, stop), max(
            start, stop
        )  # Désinfecter l'entrée
        x = self.scaleX(start) + 2 * depth
        w = self.scaleWidth(stop - start) - 4 * depth
        hot_map.append(node, (wx.Rect(int(x), int(y), int(w), int(h))))
        self.DrawRectangle(dc, node, x, y, w, h, isSequentialNode, depth)
        if not isSequentialNode:
            self.DrawIconAndLabel(dc, node, x, y, w, h, depth)
            seqHeight = min(dc.GetTextExtent("ABC")[1] + 2, h)
            self.DrawSequentialChildren(
                dc, node, y + 2, seqHeight - 4, hot_map[node], depth + 1
            )
            self.DrawParallelChildren(
                dc,
                node,
                y + seqHeight,
                h - seqHeight,
                hot_map[node],
                depth + 1,
            )

    def DrawRectangle(self, dc, node, x, y, w, h, isSequentialNode, depth):
        """
        Dessinez un rectangle représentant un nœud.

        Args :
            dc (wx.DC) : Le contexte du périphérique.
            node : Le nœud à dessiner.
            x (int) : Le x- coordinate.
            y (int) : La coordonnée y.
            w (int) : La largeur du rectangle.
            h (int) : La hauteur du rectangle.
            isSequentialNode (bool) : Si le nœud est séquentiel.
            depth (int) : La profondeur du nœud.
        """
        dc = wx.GCDC(dc) if isSequentialNode else dc
        dc.SetClippingRegion(x, y, w, h)
        dc.SetBrush(self.brushForNode(node, isSequentialNode, depth))
        dc.SetPen(self.penForNode(node, isSequentialNode, depth))
        rounding = (
            0
            if isSequentialNode
            and (h < self.padding * 4 or w < self.padding * 4)
            else self.padding * 2
        )
        dc.DrawRoundedRectangle(x, y, w, h, rounding)
        dc.DestroyClippingRegion()

    def DrawIconAndLabel(self, dc, node, x, y, w, h, depth):
        """
        Dessinez l'icône, le cas échéant, et l'étiquette, le cas échéant, du nœud.

        Args :
            dc (wx.DC) : The device context.
            node : The node to draw.
            x (int) : The x-coordinate.
            y (int) : The y-coordinate.
            w (int) : The width of the rectangle.
            h (int) : The height of the rectangle.
            depth (int) : The depth of the node.
        """
        # Make sure the Icon and Label are visible:
        if x < 0:
            w -= abs(x)
            x = 0
        dc.SetClippingRegion(
            x + 1, y + 1, w - 2, h - 2
        )  # Don't draw outside the box
        # icon = self.adapter.icon(node, node == self.selectedNode)
        if node == self.selectedNode:
            icon = self.adapter.icon(node)
        if icon and h >= icon.GetHeight() and w >= icon.GetWidth():
            iconWidth = icon.GetWidth() + 2
            dc.DrawIcon(icon, x + 2, y + 2)
        else:
            iconWidth = 0
        if h >= dc.GetTextExtent("ABC")[1]:
            dc.SetFont(self.fontForNode(dc, node, depth))
            dc.SetTextForeground(self.textForegroundForNode(node, depth))
            dc.DrawText(self.adapter.label(node), x + iconWidth + 2, y + 2)
        dc.DestroyClippingRegion()

    def DrawParallelChildren(self, dc, parent, y, h, hot_map, depth=0):
        """
        Dessinez les enfants parallèles d'un nœud.

        Args:
            dc (wx.DC): The device context.
            parent: The parent node.
            y (int): The y-coordinate.
            h (int): The height available for drawing.
            hot_map (HotMap): The HotMap instance.
            depth (int, optional): The depth of the node (default is 0).
        """
        children = self.adapter.parallel_children(parent)
        if not children:
            return
        childY = y
        h -= len(children)  # vertical space between children
        recursiveChildrenList = [
            self.adapter.parallel_children(child, recursive=True)
            for child in children
        ]
        recursiveChildrenCounts = [
            len(recursiveChildren)
            for recursiveChildren in recursiveChildrenList
        ]
        recursiveChildHeight = h / float(
            len(children) + sum(recursiveChildrenCounts)
        )
        for child, numberOfRecursiveChildren in zip(
            children, recursiveChildrenCounts
        ):
            childHeight = recursiveChildHeight * (
                numberOfRecursiveChildren + 1
            )
            if childHeight >= self.padding:
                self.DrawBox(
                    dc, child, childY, childHeight, hot_map, depth=depth
                )
            childY += childHeight + 1

    def DrawSequentialChildren(self, dc, parent, y, h, hot_map, depth=0):
        """
        Dessinez les enfants séquentiels d'un nœud.

        Args:
            dc (wx.DC): The device context.
            parent: The parent node.
            y (int): The y-coordinate.
            h (int): The height available for drawing.
            hot_map (HotMap): The HotMap instance.
            depth (int, optional): The depth of the node (default is 0).
        """
        for child in self.adapter.sequential_children(parent):
            self.DrawBox(
                dc, child, y, h, hot_map, isSequentialNode=True, depth=depth
            )

    def DrawNow(self, dc):
        """
        Dessinez le marqueur « maintenant » sur la chronologie.

        Args:
            dc (wx.DC) : le contexte du périphérique.
        """
        alpha_dc = wx.GCDC(dc)
        alpha_dc.SetPen(wx.Pen(wx.Colour(128, 200, 128, 128), width=3))
        now = self.scaleX(self.adapter.now())
        alpha_dc.DrawLine(int(now), 0, int(now), int(self.height))
        label = self.adapter.nowlabel()
        textWidth = alpha_dc.GetTextExtent(label)[0]
        alpha_dc.DrawText(label, int(now - (textWidth / 2)), 0)

    def scaleX(self, x) -> float:
        """
        Mettre à l'échelle la coordonnée X.

        Args :
            x (float) : La coordonnée X à mettre à l'échelle.

        Returns :
            (float) : La coordonnée X mise à l'échelle.
        """
        return self.scaleWidth(x - self.min_start)

    def scaleWidth(self, width) -> float:
        """
        Mettre à l'échelle la largeur.

        Args :
            width (float) : La largeur à mettre à l'échelle.

        Returns :
            (float) : La largeur mise à l'échelle.
        """
        return (width / self.length) * self.width

    def textForegroundForNode(self, node, depth=0):
        """
        Déterminez la couleur de premier plan du texte à utiliser pour afficher l'étiquette du nœud donné.

        Args :
            node : Le nœud.
            depth (int, optional) : La profondeur du nœud (la valeur par défaut est 0).

        Returns :
            fg_color (wx.Colour) : La couleur de premier plan du texte.
        """
        if node == self.selectedNode:
            fg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHTTEXT)
        else:
            fg_color = self.adapter.foreground_color(node, depth)
            if not fg_color:
                fg_color = wx.SystemSettings.GetColour(
                    wx.SYS_COLOUR_WINDOWTEXT
                )
        return fg_color

    def fontForNode(self, dc, node, depth=0):
        """
        Déterminez la police à utiliser pour afficher l'étiquette du nœud donné, mise à l'échelle pour l'impression si nécessaire.

        Args :
            dc (wx.DC): Le contexte du périphérique.
            node : Le nœud.
            depth (int, optional) : La profondeur du nœud (la valeur par défaut est 0).

        Returns :
            font (wx.Font) : La police.
        """
        font = self.adapter.font(
            node, depth
        )  # Unresolved attribute reference 'font' for class 'DefaultAdapter'
        font = (
            font
            if font
            else wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        )
        scale = dc.GetPPI()[0] / wx.ScreenDC().GetPPI()[0]
        font.SetPointSize(scale * font.GetPointSize())
        return font

    def brushForNode(self, node, isSequentialNode=False, depth=0):
        """
        Créez un pinceau à utiliser pour afficher le nœud donné.

        Args :
            node : Le nœud.
            isSequentialNode (bool, optional) : Indique si le nœud est séquentiel (la valeur par défaut est False).
            depth (int, optional) : La profondeur du nœud (la valeur par défaut est 0).

        Returns :
            (wx.Brush) : Le pinceau.
        """
        if node == self.selectedNode:
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        else:
            color = self.adapter.background_color(node)
            if color:
                # L'adaptateur renvoie un 3-tuple
                color = tuple(
                    int(c) for c in color[:3]
                )  # Convertir RGB en entiers
                if len(color) == 4:
                    color = color + (
                        int(color[3] * 255),
                    )  # Convertir l'alpha en entier

                color = wx.Colour(*color)
            else:
                red = (depth * 10) % 255
                green = 255 - ((depth * 10) % 255)
                blue = 200
                alpha = 128
                color = wx.Colour(red, green, blue, alpha)
        if isSequentialNode:
            color.Set(color.Red(), color.Green(), color.Blue(), 128)
        return wx.Brush(color)

    def penForNode(self, node, isSequentialNode=False, depth=0):
        """
        Déterminez le stylet à utiliser pour afficher le nœud donné.

        Args :
            node : Le nœud.
            isSequentialNode (bool, optional) : Indique si le nœud est séquentiel (la valeur par défaut est False).
            depth (int, optional) : La profondeur du nœud (la valeur par défaut est 0).

        Returns :
            pen (wx.Pen) : Le stylet.
        """
        pen = (
            self.SELECTED_PEN
            if node == self.selectedNode
            else self.DEFAULT_PEN
        )
        # style = wx.DOT if isSequentialNode else wx.SOLID
        # pen.SetStyle(style)
        return pen


class DefaultAdapter(object):
    """
    Classe d'adaptateur par défaut pour la chronologie.

    Cette classe fournit des méthodes pour accéder aux propriétés et aux relations des nœuds.
    """

    # def __init__(self):
    # self.font = None

    def parallel_children(self, node, recursive=False):
        """
        Obtenez les enfants parallèles d'un nœud.

        Args :
            node : Le nœud.
            recursive (bool, optional) : s'il faut inclure les enfants récursifs (la valeur par défaut est False).

        Returns :
            children (list) : Les enfants parallèles du nœud.
        """
        children = node.parallel_children[:]
        if recursive:
            for child in node.parallel_children:
                children.extend(self.parallel_children(child, True))
        return children

    def sequential_children(self, node):
        """
        Obtenez les enfants séquentiels d'un nœud.

        Args :
            node : Le nœud.

        Returns :
            (list) : Les enfants séquentiels du nœud.
        """
        return node.sequential_children

    def children(self, node):
        """
        Récupère tous les enfants d'un nœud (à la fois parallèles et séquentiels).

        Args :
            node : Le nœud.

        Returns :
            (list) : Tous les enfants du nœud.
        """
        return self.parallel_children(node) + self.sequential_children(node)

    def bounds(self, node):
        """
        Obtenez les limites (heures de début et de fin) d'un nœud.

        Args :
            node : Le nœud.

        Returns :
            (tuple) : L'heure de début minimale et l'heure d'arrêt maximale.
        """
        times = [node.start, node.stop]
        for child in self.children(node):
            times.extend(self.bounds(child))
        return min(times), max(times)

    def start(self, node, recursive=False):
        """
        Obtenez l'heure de début d'un nœud.

        Args :
            node : Le nœud.
            recursive (bool, optional) : s'il faut inclure les enfants récursifs (la valeur par défaut est False).

        Returns :
            (float) : L'heure de début.
        """
        starts = [node.start]
        if recursive:
            starts.extend(
                [self.start(child, True) for child in self.children(node)]
            )
        return float(min(starts))

    def stop(self, node, recursive=False):
        """
        Obtenez l'heure d'arrêt d'un nœud.

        Args :
            node : Le nœud.
            recursive (bool, optional) : s'il faut inclure les enfants récursifs (la valeur par défaut est False).

        Returns :
            (float) : L'heure d'arrêt.
        """
        stops = [node.stop]
        if recursive:
            stops.extend(
                [self.stop(child, True) for child in self.children(node)]
            )
        return float(max(stops))

    def label(self, node):
        """
        Récupère l'étiquette d'un nœud.

        Args :
            node : Le nœud.

        Returns :
            (str) : L'étiquette du nœud.
        """
        return node.path

    def background_color(self, node):
        """
        Récupère la couleur d'arrière-plan d'un nœud.

        Args :
            node : Le nœud.

        Returns :
            (tuple | None) : La couleur d'arrière-plan sous forme de 3 tuples (R, G, B).
        """
        return None

    def foreground_color(self, node, depth):
        """
        Obtenez la couleur de premier plan d'un nœud.

        Args :
            node : Le nœud.
            depth (int) : La profondeur du nœud.

        Returns :
            (tuple | None) : La couleur de premier plan sous forme de 3-tuples (R, V, B).
        """
        return None

    def icon(self, node):
        """
        Récupère l'icône d'un nœud.

        Args :
            node : Le nœud.

        Renvoie :
            (wx.Icon | None) : L'icône du nœud.
        """
        # wx.Icon(node)
        return None

    def now(self):
        """
        Obtenez l'heure actuelle.

        Renvoie :
            (float) : L'heure actuelle.
        """
        return 0.00

    def nowlabel(self):
        """
        Obtenez l'étiquette de l'heure actuelle.

        Renvoie :
            (str) : L'étiquette de l'heure actuelle.
        """
        return "Now"


class TestApp(wx.App):
    """
    Application de base pour maintenir le cadre de visualisation.
    """

    def __init__(self, size):
        """
        Initialisez l'instance TestApp.

        Args :
            size (int) : La taille du modèle.
        """
        self.size = size
        # super(TestApp, self).__init__(0)
        super().__init__(0)

    def OnInit(self):
        """
        Initialisez l'application.

        Returns :
            (bool) : True Vrai si l'initialisation a réussi.
        """
        wx.InitAllImageHandlers()
        self.frame = wx.Frame(None)
        self.frame.CreateStatusBar()
        model = self.get_model(self.size)
        self.timeline = TimeLine(self.frame, model=model)
        self.frame.Show(True)
        return True

    def get_model(self, size):
        """
        Obtenez le modèle pour la chronologie.

        Args :
            size (int) : La taille du modèle.

        Returns :
            Node : Le nœud racine du modèle.
        """
        parallel_children, sequential_children = [], []
        if size > 0:
            parallel_children = [self.get_model(size - 1) for i in range(size)]
        sequential_children = [
            Node("Seq 1", 30 + 10 * size, 40 + 10 * size, [], []),
            Node("Seq 2", 80 - 10 * size, 90 - 10 * size, [], []),
        ]
        return Node(
            "Node %d" % size,
            0 + 5 * size,
            100 - 5 * size,
            parallel_children,
            sequential_children,
        )


class Node(object):
    """
    Un nœud dans le modèle de chronologie.
    """

    def __init__(self, path, start, stop, subnodes, events):
        """
        Initialisez l'instance de nœud.

        Args:
            path (str): The path of the node.
            start (int): The start time of the node.
            stop (int): The stop time of the node.
            subnodes (list): The subnodes of the node.
            events (list): The events of the node.
        """
        self.path = path
        self.start = start
        self.stop = stop
        self.parallel_children = subnodes
        self.sequential_children = events

    def __repr__(self):
        """
        Renvoie une représentation sous forme de chaîne de l'instance Node.

        Returns :
            (str) : The string representation.
        """
        return "%s(%r, %r, %r, %r, %r)" % (
            self.__class__.__name__,
            self.path,
            self.start,
            self.stop,
            self.parallel_children,
            self.sequential_children,
        )
        # return f"{self.__class__.__name__}({self.path!r}, {self.start!r}, {self.stop!r}, {self.parallel_children!r}, {self.sequential_children!r})"


usage = "timeline.py [size]"


def main():
    """
    Boucle principale pour l'application.
    """
    import sys

    size = 3
    if len(sys.argv) > 1:
        if sys.argv[1] in ("-h", "--help"):
            print(usage)
        else:
            try:
                size = int(sys.argv[1])
            except ValueError:
                print(usage)
    else:
        app = TestApp(size)
        app.MainLoop()


if __name__ == "__main__":
    main()
