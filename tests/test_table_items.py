import unittest
import sys
import types

qtgui = types.ModuleType("PySide6.QtGui")
qtwidgets = types.ModuleType("PySide6.QtWidgets")


class _Dummy:
    def __init__(self, *args, **kwargs):
        pass


qtgui.QColor = _Dummy
qtwidgets.QLabel = _Dummy
qtwidgets.QTableWidgetItem = _Dummy

sys.modules.setdefault("PySide6", types.ModuleType("PySide6"))
sys.modules["PySide6.QtGui"] = qtgui
sys.modules["PySide6.QtWidgets"] = qtwidgets

from widgets.table_items import status_color_info, status_display


class TableItemsTests(unittest.TestCase):
    def test_status_display_matches_expected_labels(self):
        self.assertEqual(status_display("棚にある"), "● 棚にある")
        self.assertEqual(status_display("持出"), "● 持出")
        self.assertEqual(status_display("返却"), "● 返却")

    def test_status_color_info_matches_expected_colors(self):
        self.assertEqual(status_color_info("棚にある"), ("#2e7d32", "#e8f5e9"))
        self.assertEqual(status_color_info("持出"), ("#c62828", "#ffebee"))
        self.assertEqual(status_color_info("返却"), ("#ef6c00", "#fff3e0"))


if __name__ == "__main__":
    unittest.main()
