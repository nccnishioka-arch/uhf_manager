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

from widgets.table_items import rssi_level_info, status_color_info, status_display


class TableItemsTests(unittest.TestCase):
    def test_status_display_matches_expected_labels(self):
        self.assertEqual(status_display("棚にある"), "● 棚にある")
        self.assertEqual(status_display("持出"), "● 持出")
        self.assertEqual(status_display("返却"), "● 返却")

    def test_status_color_info_matches_expected_colors(self):
        self.assertEqual(status_color_info("棚にある"), ("#2e7d32", "#e8f5e9"))
        self.assertEqual(status_color_info("持出"), ("#c62828", "#ffebee"))
        self.assertEqual(status_color_info("返却"), ("#ef6c00", "#fff3e0"))


class RssiLevelInfoTests(unittest.TestCase):
    def test_strong_signal_returns_3_bars_and_green_emoji(self):
        value, label, bars, color, emoji = rssi_level_info(-45)
        self.assertEqual(value, -45)
        self.assertEqual(label, "良好")
        self.assertEqual(bars, 3)
        self.assertEqual(emoji, "🟢")

    def test_boundary_strong_signal_at_minus60(self):
        value, label, bars, _color, emoji = rssi_level_info(-60)
        self.assertEqual(label, "良好")
        self.assertEqual(bars, 3)
        self.assertEqual(emoji, "🟢")

    def test_moderate_signal_returns_2_bars_and_yellow_emoji(self):
        value, label, bars, _color, emoji = rssi_level_info(-65)
        self.assertEqual(value, -65)
        self.assertEqual(label, "普通")
        self.assertEqual(bars, 2)
        self.assertEqual(emoji, "🟡")

    def test_boundary_moderate_signal_at_minus70(self):
        value, label, bars, _color, emoji = rssi_level_info(-70)
        self.assertEqual(label, "普通")
        self.assertEqual(bars, 2)
        self.assertEqual(emoji, "🟡")

    def test_slightly_weak_signal_returns_1_bar_and_orange_emoji(self):
        value, label, bars, _color, emoji = rssi_level_info(-73)
        self.assertEqual(value, -73)
        self.assertEqual(label, "やや弱")
        self.assertEqual(bars, 1)
        self.assertEqual(emoji, "🟠")

    def test_boundary_slightly_weak_at_minus80(self):
        value, label, bars, _color, emoji = rssi_level_info(-80)
        self.assertEqual(label, "やや弱")
        self.assertEqual(bars, 1)
        self.assertEqual(emoji, "🟠")

    def test_weak_signal_returns_1_bar_and_red_emoji(self):
        value, label, bars, _color, emoji = rssi_level_info(-85)
        self.assertEqual(value, -85)
        self.assertEqual(label, "弱")
        self.assertEqual(bars, 1)
        self.assertEqual(emoji, "🔴")

    def test_invalid_rssi_returns_none_value(self):
        value, label, bars, _color, emoji = rssi_level_info("invalid")
        self.assertIsNone(value)
        self.assertEqual(bars, 0)
        self.assertEqual(emoji, "")

    def test_none_rssi_returns_none_value(self):
        value, _label, bars, _color, emoji = rssi_level_info(None)
        self.assertIsNone(value)
        self.assertEqual(bars, 0)
        self.assertEqual(emoji, "")

    def test_display_text_includes_emoji_bars_and_dbm(self):
        value, label, bars, _color, emoji = rssi_level_info(-53)
        bar_str = "■" * bars
        display_text = f"{emoji}{bar_str}  {value}"
        self.assertIn("🟢", display_text)
        self.assertIn("■■■", display_text)
        self.assertIn("-53", display_text)

    def test_tooltip_format_includes_dbm_and_judgment(self):
        value, label, bars, _color, emoji = rssi_level_info(-53)
        tooltip = f"RSSI: {value} dBm\n判定: {label}"
        self.assertEqual(tooltip, "RSSI: -53 dBm\n判定: 良好")


if __name__ == "__main__":
    unittest.main()
