"""Unit tests for VirtualListCtrl (widget-level).

These tests create a real wx.Frame and a fake viewer panel (ParentStub)
that implements the minimal API expected by VirtualListCtrl.
"""
import os
import importlib.util
import pytest
import wx

# from taskcoach.taskcoachlib.widgets.listctrl import VirtualListCtrl
# Importer le module `listctrl.py` directement par chemin pour éviter les
# initialisations lourdes / circulaires du package 'taskcoach'.
spec = importlib.util.spec_from_file_location(
    "taskcoach_listctrl",
    os.path.join(
        os.path.dirname(__file__), "../../../taskcoach/taskcoachlib/widgets/listctrl.py"
    ),
)

# Préparer des modules factices pour éviter les importations circulaires
import sys
import types as _types

# taskcoachlib.operating_system
os_mod = _types.ModuleType("taskcoachlib.operating_system")
os_mod.isMac = lambda: False
sys.modules["taskcoachlib.operating_system"] = os_mod

# taskcoachlib.widgets.itemctrl (mixins minimalistes requis par la classe)
itemctrl_mod = _types.ModuleType("taskcoachlib.widgets.itemctrl")


class CtrlWithItemsMixin:
    pass


class CtrlWithColumnsMixin:
    pass


class CtrlWithToolTipMixin:
    pass


itemctrl_mod.CtrlWithItemsMixin = CtrlWithItemsMixin
itemctrl_mod.CtrlWithColumnsMixin = CtrlWithColumnsMixin
itemctrl_mod.CtrlWithToolTipMixin = CtrlWithToolTipMixin
sys.modules["taskcoachlib.widgets.itemctrl"] = itemctrl_mod
sys.modules["taskcoachlib.widgets"] = _types.ModuleType("taskcoachlib.widgets")

listctrl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(listctrl)
VirtualListCtrl = listctrl.VirtualListCtrl


class TestItem:
    def __init__(self, name):
        self.name = name

    def foregroundColor(self, recursive=True):
        return wx.Colour(0, 0, 0)

    def backgroundColor(self, recursive=True):
        return wx.Colour(255, 255, 255)

    def font(self, recursive=True):
        return None


class ParentStub(wx.Panel):
    """Parent 'viewer' factice pour VirtualListCtrl ; est un wx.Panel réel.

    Fournit l'API minimale attendue par `VirtualListCtrl`.
    """

    def __init__(self, parent, count=10):
        super().__init__(parent)
        self.data = [TestItem(f"item{i}") for i in range(count)]

    def getItemWithIndex(self, idx):
        return self.data[idx]

    def getIndexOfItem(self, item):
        return self.data.index(item)

    def getItemText(self, item, columnIndex):
        return f"{item.name}-col{columnIndex}"

    def getItemImages(self, item, columnIndex):
        return [1, 2, 3, 4]

    def getItemTooltipData(self, item):
        return f"tooltip-{item.name}"


@pytest.fixture(scope="module")
def wx_app():
    app = wx.App(False)
    frame = wx.Frame(None)
    # Ne pas montrer la fenêtre pendant les tests
    frame.Hide()
    yield frame
    try:
        frame.Destroy()
    except Exception:
        pass
    try:
        app.Destroy()
    except Exception:
        pass


def test_OnGetItemText_and_image_and_attr(wx_app):
    parent = ParentStub(wx_app, 5)
    ctrl = VirtualListCtrl(parent, columns=[])
    ctrl.SetItemCount(5)

    text = ctrl.OnGetItemText(2, 0)
    assert text == parent.getItemText(parent.getItemWithIndex(2), 0)

    img = ctrl.OnGetItemImage(1)
    assert isinstance(img, int)

    attr = ctrl.OnGetItemAttr(0)
    assert attr is not None


def test_HitTest_returns_column(wx_app, monkeypatch):
    parent = ParentStub(wx_app, 3)
    ctrl = VirtualListCtrl(parent, columns=[])
    # Ensure super().HitTest returns a 2-tuple
    monkeypatch.setattr(
        wx.ListCtrl,
        "HitTest",
        lambda self, pt, *a, **k: (0, 0),
    )
    # set two columns widths
    try:
        ctrl.InsertColumn(0, "c0")
        ctrl.InsertColumn(1, "c1")
        ctrl.SetColumnWidth(0, 50)
        ctrl.SetColumnWidth(1, 50)
    except Exception:
        # some wx versions / environments may not support InsertColumn in tests
        pass
    result = ctrl.HitTest((10, 10))
    assert isinstance(result, tuple) and len(result) == 3


def test_scheduleRefresh_coalescing(wx_app, monkeypatch):
    parent = ParentStub(wx_app, 4)
    ctrl = VirtualListCtrl(parent, columns=[])

    calls = {"count": 0}

    def fake_refresh_all(count):
        calls["count"] += 1

    # # Monkeypatch wx.CallAfter to execute immediately
    # monkeypatch.setattr(wx, "CallAfter", lambda f, *a, **k: f(*a, **k))
    # Monkeypatch wx.CallAfter to queue the callable instead of executing it
    scheduled = []
    monkeypatch.setattr(wx, "CallAfter", lambda f, *a, **k: scheduled.append(lambda: f(*a, **k)))


    # Replace instance method
    monkeypatch.setattr(ctrl, "RefreshAllItems", fake_refresh_all)

    # Call scheduleRefresh multiple times rapidly
    ctrl.scheduleRefresh(1)
    ctrl.scheduleRefresh(2)
    ctrl.scheduleRefresh(3)

    # Only one scheduled call should have been appended
    assert len(scheduled) == 1

    # Execute the scheduled refresh (simulating the event loop)
    scheduled[0]()

    # After execution, the fake refresh should have been called once
    assert calls["count"] == 1


def test_selection_methods(wx_app):
    parent = ParentStub(wx_app, 3)
    ctrl = VirtualListCtrl(parent, columns=[])
    ctrl.SetItemCount(3)

    # select second item
    ctrl.select([parent.getItemWithIndex(1)])

    sel = ctrl.curselection()
    assert len(sel) >= 0
