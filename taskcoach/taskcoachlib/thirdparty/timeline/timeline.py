#! /usr/bin/env python
import wx
import wx.lib

# Define new event types and binders
TimeLineSelectionEvent, EVT_TIMELINE_SELECTED = wx.lib.newevent.NewEvent()
TimeLineActivationEvent, EVT_TIMELINE_ACTIVATED = wx.lib.newevent.NewEvent()


class HotMap(object):
    """
    Keep track of which node is where.

    This class helps in managing the nodes and their positions within the timeline.
    """

    def __init__(self, parent=None):
        """
        Initialize the HotMap instance.

        Args:
            parent: The parent node (default is None).
        """
        self.parent = parent
        self.nodes = []
        self.rects = {}
        self.children = {}
        super().__init__()

    def append(self, node, rect):
        """
        Append a node and its rectangle to the HotMap.

        Args:
            node: The node to append.
            rect (wx.Rect): The rectangle representing the node's position.
        """
        self.nodes.append(node)
        self.rects[node] = rect
        self.children[node] = HotMap(node)

    def __getitem__(self, node):
        """
        Get the child HotMap for a given node.

        Args:
            node: The node to get the child HotMap for.

        Returns:
            HotMap: The child HotMap.
        """
        return self.children[node]

    def findNodeAtPosition(self, position, parent=None):
        """
        Retrieve the node at the given position.

        Args:
            position (wx.Point): The position to check.
            parent: The parent node (default is None).

        Returns:
            The node at the given position or the parent node if no node is found.
        """
        for node, rect in list(self.rects.items()):
            if rect.Contains(position):
                return self[node].findNodeAtPosition(position, node)
        return parent

    def firstNode(self):
        """
        Get the first node in the HotMap.

        Returns:
            The first node or None if there are no nodes.
        """
        return self.nodes[0] if self.nodes else None

    def lastNode(self, parent=None):
        """
        Get the last node in the HotMap.

        Args:
            parent: The parent node (default is None).

        Returns:
            The last node or the parent node if there are no nodes.
        """
        if self.nodes:
            last = self.nodes[-1]
            return self[last].lastNode(last)
        else:
            return parent

    def findNode(self, target):
        """
        Find the HotMap containing the target node.

        Args:
            target: The target node to find.

        Returns:
            HotMap: The HotMap containing the target node or None if not found.
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
        Get the next child node after the target node.

        Args:
            target: The target node.

        Returns:
            The next child node.
        """
        index = self.nodes.index(target)
        index = min(index + 1, len(self.nodes) - 1)
        return self.nodes[index]

    def previousChild(self, target):
        """
        Get the previous child node before the target node.

        Args:
            target: The target node.

        Returns:
            The previous child node.
        """
        index = self.nodes.index(target)
        index = max(index - 1, 0)
        return self.nodes[index]

    def firstChild(self, target):
        """
        Get the first child node of the target node.

        Args:
            target: The target node.

        Returns:
            The first child node or the target node if it has no children.
        """
        children = self[target].nodes
        if children:
            return children[0]
        else:
            return target


class TimeLine(wx.Panel):
    """
    A timeline widget for displaying and interacting with a timeline of events.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the TimeLine instance.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        self.model = kwargs.pop("model", [])
        self.padding = kwargs.pop("padding", 3)
        self.adapter = kwargs.pop("adapter", DefaultAdapter())
        self.selectedNode = None
        self.backgroundColour = wx.WHITE
        self._buffer = wx.Bitmap(20, 20)  # Have a default buffer ready
        self.DEFAULT_PEN = wx.Pen(wx.BLACK, 1, wx.SOLID)
        self.SELECTED_PEN = wx.Pen(wx.WHITE, 2, wx.SOLID)
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
        Set the background color of the timeline.

        Args:
            colour (wx.Colour): The background color to set.
        """
        self.backgroundColour = colour

    def Refresh(self):
        """
        Refresh the timeline drawing.
        """
        self.UpdateDrawing()

    def OnPaint(self, event):
        """
        Handle the paint event.

        Args:
            event (wx.PaintEvent): The paint event.
        """
        dc = wx.BufferedPaintDC(self, self._buffer)

    def OnSize(self, event):
        """
        Handle the resize event.

        Args:
            event (wx.SizeEvent): The resize event.
        """
        # The buffer is initialized in here, so that the buffer is always
        # the same size as the Window.
        width, height = self.GetClientSize()
        if width <= 0 or height <= 0:
            return
        # Make new off-screen bitmap: this bitmap will always have the
        # current drawing in it, so it can be used to save the image to
        # a file, or whatever.
        # wxPyDeprecationWarning: Call to deprecated item EmptyBitmap. Use :class:`wx.Bitmap` instead
        self._buffer = wx.Bitmap(width, height)
        self.UpdateDrawing()

    def OnClickRelease(self, event):
        """
        Handle the left mouse button release event.

        Args:
            event (wx.MouseEvent): The mouse event.
        """
        event.Skip()
        self.SetFocus()
        point = event.GetPosition()
        node = self.hot_map.findNodeAtPosition(point)
        self.SetSelected(node, point)

    def OnDoubleClick(self, event):
        """
        Handle the left mouse button double-click event.

        Args:
            event (wx.MouseEvent): The mouse event.
        """
        point = event.GetPosition()
        node = self.hot_map.findNodeAtPosition(point)
        if node:
            wx.PostEvent(self, TimeLineActivationEvent(node=node, point=point))

    def OnKeyUp(self, event):
        """
        Handle the key up event.

        Args:
            event (wx.KeyEvent): The key event.
        """
        # TODO : Review the method
        # because Property 'KeyCode' cannot be read
        event.Skip()
        if not self.hot_map:
            return
        if event.KeyCode == wx.WXK_HOME:
            self.SetSelected(self.hot_map.firstNode())
            return
        elif event.KeyCode == wx.WXK_END:
            self.SetSelected(self.hot_map.lastNode())
            return
        if not self.selectedNode:
            return
        if event.KeyCode == wx.WXK_RETURN:
            wx.PostEvent(self, TimeLineActivationEvent(node=self.selectedNode))
            return
        hot_map = self.hot_map.findNode(self.selectedNode)
        if hot_map is None:
            newSelection = self.hot_map.firstNode()
        elif event.KeyCode == wx.WXK_DOWN:
            newSelection = hot_map.nextChild(self.selectedNode)
        elif event.KeyCode == wx.WXK_UP:
            newSelection = hot_map.previousChild(self.selectedNode)
        elif event.KeyCode == wx.WXK_RIGHT:
            newSelection = hot_map.firstChild(self.selectedNode)
        elif event.KeyCode == wx.WXK_LEFT and hot_map.parent:
            newSelection = hot_map.parent
        else:
            newSelection = self.selectedNode
        self.SetSelected(newSelection)

    def GetSelected(self):
        """
        Get the currently selected node.

        Returns:
            The currently selected node.
        """
        return self.selectedNode

    def SetSelected(self, node, point=None):
        """
        Set the given node as selected in the timeline widget.

        Args:
            node: The node to select.
            point (wx.Point, optional): The position of the node (default is None).
        """
        if node == self.selectedNode:
            return
        self.selectedNode = node
        self.Refresh()
        if node:
            wx.PostEvent(self, TimeLineSelectionEvent(node=node, point=point))

    def UpdateDrawing(self):
        """
        Update the drawing of the timeline.
        """
        dc = wx.BufferedDC(wx.ClientDC(self), self._buffer)
        self.Draw(dc)

    def Draw(self, dc):
        """
        Draw the timeline on the device context.

        Args:
            dc (wx.DC): The device context.
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
            )  # Leave room for time labels
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
        Return the default GUI font, scaled for printing if necessary.

        Args:
            dc (wx.DC): The device context.

        Returns:
            wx.Font: The scaled font.
        """
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        scale = dc.GetPPI()[0] // wx.ScreenDC().GetPPI()[0]
        font.SetPointSize(scale * font.GetPointSize())
        return font

    def DrawBox(
        self, dc, node, y, h, hot_map, isSequentialNode=False, depth=0
    ):
        """
        Draw a box representing a node.

        Args:
            dc (wx.DC): The device context.
            node: The node to draw.
            y (int): The y-coordinate.
            h (int): The height of the box.
            hot_map (HotMap): The HotMap instance.
            isSequentialNode (bool, optional): Whether the node is sequential (default is False).
            depth (int, optional): The depth of the node (default is 0).
        """
        if h < self.padding:
            return
        start, stop = self.adapter.start(node), self.adapter.stop(node)
        if start is None:
            start = self.min_start - 10
        if stop is None:
            stop = self.max_stop + 10
        start, stop = min(start, stop), max(start, stop)  # Sanitize input
        x = int(self.scaleX(start) + 2 * depth)
        w = int(self.scaleWidth(stop - start) - 4 * depth)
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
        Draw a rectangle representing a node.

        Args:
            dc (wx.DC): The device context.
            node: The node to draw.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.
            isSequentialNode (bool): Whether the node is sequential.
            depth (int): The depth of the node.
        """
        dc = wx.GCDC(dc) if isSequentialNode else dc
        dc.SetClippingRegion(int(x), int(y), int(w), int(h))
        dc.SetBrush(self.brushForNode(node, isSequentialNode, depth))
        dc.SetPen(self.penForNode(node, isSequentialNode, depth))
        rounding = (
            0
            if isSequentialNode
            and (h < self.padding * 4 or w < self.padding * 4)
            else self.padding * 2
        )
        dc.DrawRoundedRectangle(int(x), int(y), int(w), int(h), rounding)
        dc.DestroyClippingRegion()

    def DrawIconAndLabel(self, dc, node, x, y, w, h, depth):
        """
        Draw the icon, if any, and the label, if any, of the node.

        Args:
            dc (wx.DC): The device context.
            node: The node to draw.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            w (int): The width of the rectangle.
            h (int): The height of the rectangle.
            depth (int): The depth of the node.
        """
        # Make sure the Icon and Label are visible:
        if x < 0:
            w -= abs(x)
            x = 0
        dc.SetClippingRegion(
            int(x + 1), int(y + 1), int(w - 2), int(h - 2)
        )  # Don't draw outside the box
        icon = self.adapter.icon(node, node == self.selectedNode)
        if icon and h >= icon.GetHeight() and w >= icon.GetWidth():
            iconWidth = icon.GetWidth() + 2
            dc.DrawIcon(icon, int(x + 2), int(y + 2))
        else:
            iconWidth = 0
        if h >= dc.GetTextExtent("ABC")[1]:
            dc.SetFont(self.fontForNode(dc, node, depth))
            dc.SetTextForeground(self.textForegroundForNode(node, depth))
            dc.DrawText(
                self.adapter.label(node), int(x + iconWidth + 2), int(y + 2)
            )
        dc.DestroyClippingRegion()

    def DrawParallelChildren(self, dc, parent, y, h, hot_map, depth=0):
        """
        Draw the parallel children of a node.

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
        # recursiveChildHeight = h / float(
        recursiveChildHeight = h // (
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
        Draw the sequential children of a node.

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
        Draw the "now" marker on the timeline.

        Args:
            dc (wx.DC): The device context.
        """
        alpha_dc = wx.GCDC(dc)
        alpha_dc.SetPen(wx.Pen(wx.Colour(128, 200, 128, 128), width=3))
        now = int(self.scaleX(self.adapter.now()))
        alpha_dc.DrawLine(int(now), 0, int(now), int(self.height))
        label = self.adapter.nowlabel()
        textWidth = alpha_dc.GetTextExtent(label)[0]
        alpha_dc.DrawText(label, int(now - (textWidth / 2)), 0)

    def scaleX(self, x):
        """
        Scale the x-coordinate.

        Args:
            x (float): The x-coordinate to scale.

        Returns:
            float: The scaled x-coordinate.
        """
        return self.scaleWidth(x - self.min_start)

    def scaleWidth(self, width):
        """
        Scale the width.

        Args:
            width (float): The width to scale.

        Returns:
            float: The scaled width.
        """
        return int((width / self.length) * self.width)

    def textForegroundForNode(self, node, depth=0):
        """
        Determine the text foreground color to use to display the label of the given node.

        Args:
            node: The node.
            depth (int, optional): The depth of the node (default is 0).

        Returns:
            wx.Colour: The text foreground color.
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
        Determine the font to use to display the label of the given node, scaled for printing if necessary.

        Args:
            dc (wx.DC): The device context.
            node: The node.
            depth (int, optional): The depth of the node (default is 0).

        Returns:
            wx.Font: The font.
        """
        font = self.adapter.font(node, depth)
        font = (
            font
            if font
            else wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        )
        scale = dc.GetPPI()[0] // wx.ScreenDC().GetPPI()[0]
        font.SetPointSize(scale * font.GetPointSize())
        return font

    def brushForNode(self, node, isSequentialNode=False, depth=0):
        """
        Create brush to use to display the given node.

        Args:
            node: The node.
            isSequentialNode (bool, optional): Whether the node is sequential (default is False).
            depth (int, optional): The depth of the node (default is 0).

        Returns:
            wx.Brush: The brush.
        """
        if node == self.selectedNode:
            color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_HIGHLIGHT)
        else:
            color = self.adapter.background_color(node)
            if color:
                # The adapter returns a 3-tuple
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
                color = wx.Colour(red, green, blue)
        if isSequentialNode:
            color.Set(color.Red(), color.Green(), color.Blue(), 128)
        return wx.Brush(color)

    def penForNode(self, node, isSequentialNode=False, depth=0):
        """
        Determine the pen to use to display the given node.

        Args:
            node: The node.
            isSequentialNode (bool, optional): Whether the node is sequential (default is False).
            depth (int, optional): The depth of the node (default is 0).

        Returns:
            wx.Pen: The pen.
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
    The default adapter class for the timeline.

    This class provides methods for accessing node properties and relationships.
    """

    def parallel_children(self, node, recursive=False):
        """
        Get the parallel children of a node.

        Args:
            node: The node.
            recursive (bool, optional): Whether to include recursive children (default is False).

        Returns:
            list: The parallel children of the node.
        """
        children = node.parallel_children[:]
        if recursive:
            for child in node.parallel_children:
                children.extend(self.parallel_children(child, True))
        return children

    def sequential_children(self, node):
        """
        Get the sequential children of a node.

        Args:
            node: The node.

        Returns:
            list: The sequential children of the node.
        """
        return node.sequential_children

    def children(self, node):
        """
        Get all children of a node (both parallel and sequential).

        Args:
            node: The node.

        Returns:
            list: All children of the node.
        """
        return self.parallel_children(node) + self.sequential_children(node)

    def bounds(self, node):
        """
        Get the bounds (start and stop times) of a node.

        Args:
            node: The node.

        Returns:
            tuple: The minimum start time and maximum stop time.
        """
        times = [node.start, node.stop]
        for child in self.children(node):
            times.extend(self.bounds(child))
        return min(times), max(times)

    def start(self, node, recursive=False):
        """
        Get the start time of a node.

        Args:
            node: The node.
            recursive (bool, optional): Whether to include recursive children (default is False).

        Returns:
            float: The start time.
        """
        starts = [node.start]
        if recursive:
            starts.extend(
                [self.start(child, True) for child in self.children(node)]
            )
        return float(min(starts))

    def stop(self, node, recursive=False):
        """
        Get the stop time of a node.

        Args:
            node: The node.
            recursive (bool, optional): Whether to include recursive children (default is False).

        Returns:
            float: The stop time.
        """
        stops = [node.stop]
        if recursive:
            stops.extend(
                [self.stop(child, True) for child in self.children(node)]
            )
        return float(max(stops))

    def label(self, node):
        """
        Get the label of a node.

        Args:
            node: The node.

        Returns:
            str: The label of the node.
        """
        return node.path

    def background_color(self, node):
        """
        Get the background color of a node.

        Args:
            node: The node.

        Returns:
            tuple: The background color as a 3-tuple (R, G, B).
        """
        return None

    def foreground_color(self, node, depth):
        """
        Get the foreground color of a node.

        Args:
            node: The node.
            depth (int): The depth of the node.

        Returns:
            tuple: The foreground color as a 3-tuple (R, G, B).
        """
        return None

    def icon(self, node):
        """
        Get the icon of a node.

        Args:
            node: The node.

        Returns:
            wx.Icon: The icon of the node.
        """
        return None

    def now(self):
        """
        Get the current time.

        Returns:
            float: The current time.
        """
        return 0

    def nowlabel(self):
        """
        Get the label for the current time.

        Returns:
            str: The label for the current time.
        """
        return "Now"


class TestApp(wx.App):
    """
    Basic application for holding the viewing Frame.
    """

    def __init__(self, size):
        """
        Initialize the TestApp instance.

        Args:
            size (int): The size of the model.
        """
        self.size = size
        super().__init__(0)

    def OnInit(self):
        """
        Initialize the application.

        Returns:
            bool: True if initialization was successful.
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
        Get the model for the timeline.

        Args:
            size (int): The size of the model.

        Returns:
            Node: The root node of the model.
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
    A node in the timeline model.
    """

    def __init__(self, path, start, stop, subnodes, events):
        """
        Initialize the Node instance.

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
        Return a string representation of the Node instance.

        Returns:
            str: The string representation.
        """
        return "%s(%r, %r, %r, %r, %r)" % (
            self.__class__.__name__,
            self.path,
            self.start,
            self.stop,
            self.parallel_children,
            self.sequential_children,
        )


usage = "timeline.py [size]"


def main():
    """
    Mainloop for the application.
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
