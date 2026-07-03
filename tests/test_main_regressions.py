import ast
import copy
import csv
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from reader.reader_manager import normalize_connection_type


MAIN_PATH = Path(__file__).resolve().parents[1] / "main.py"
MAIN_AST = ast.parse(MAIN_PATH.read_text(encoding="utf-8"), filename=str(MAIN_PATH))


def load_main_function(name, globals_dict):
    for node in MAIN_AST.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            module = ast.Module(body=[copy.deepcopy(node)], type_ignores=[])
            ast.fix_missing_locations(module)
            namespace = dict(globals_dict)
            exec(compile(module, str(MAIN_PATH), "exec"), namespace)
            return namespace[name]
    raise AssertionError(f"Function not found: {name}")


class _FakeReader:
    def __init__(self, tags_by_read=None):
        self._tags_by_read = list(tags_by_read or [])
        self.set_antenna_calls = []
        self.read_calls = 0

    def is_connected(self):
        return True

    def set_antenna(self, ant_no):
        self.set_antenna_calls.append(ant_no)

    def read_tags(self):
        self.read_calls += 1
        if self._tags_by_read:
            return self._tags_by_read.pop(0)
        return []


class _FakeTableItem:
    def __init__(self, value):
        self._value = value

    def text(self):
        return self._value


class _FakeTable:
    def __init__(self, rows):
        self._rows = rows

    def rowCount(self):
        return len(self._rows)

    def item(self, row, column):
        return self._rows[row].get(column)


class MainRegressionTests(unittest.TestCase):
    def test_read_once_uses_single_read_for_lan(self):
        reader = _FakeReader(tags_by_read=[[]])
        movement_calls = []
        read_once = load_main_function(
            "read_once",
            {
                "reader": reader,
                "settings": {"connection_type": "LAN", "antenna_count": 4},
                "normalize_connection_type": normalize_connection_type,
                "log": lambda *args, **kwargs: None,
                "check_movements": lambda epcs: movement_calls.append(epcs),
            },
        )

        read_once()

        self.assertEqual(reader.set_antenna_calls, [])
        self.assertEqual(reader.read_calls, 1)
        self.assertEqual(movement_calls, [set()])

    def test_read_once_uses_antenna_reads_for_usb_and_uart(self):
        for connection_type in ("USB", "UART", "232C(UART)"):
            with self.subTest(connection_type=connection_type):
                reader = _FakeReader(tags_by_read=[[], [], []])
                movement_calls = []
                read_once = load_main_function(
                    "read_once",
                    {
                        "reader": reader,
                        "settings": {
                            "connection_type": connection_type,
                            "antenna_count": 3,
                        },
                        "normalize_connection_type": normalize_connection_type,
                        "log": lambda *args, **kwargs: None,
                        "check_movements": lambda epcs: movement_calls.append(epcs),
                    },
                )

                read_once()

                self.assertEqual(reader.set_antenna_calls, [1, 2, 3])
                self.assertEqual(reader.read_calls, 3)
                self.assertEqual(movement_calls, [set()])

    def test_save_csv_uses_cached_details_when_available(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            path = tmp.name

        table = _FakeTable(
            [
                {
                    0: _FakeTableItem("表示タイトル"),
                    2: _FakeTableItem("9"),
                    3: _FakeTableItem("表示状態"),
                }
            ]
        )
        log_messages = []
        save_csv = load_main_function(
            "save_csv",
            {
                "QFileDialog": SimpleNamespace(
                    getSaveFileName=lambda *args, **kwargs: (path, "CSV Files (*.csv)")
                ),
                "window": SimpleNamespace(tableTags=table),
                "csv": csv,
                "table_details_by_row": {
                    0: {
                        "epc": "E200CACHE",
                        "title": "キャッシュタイトル",
                        "rssi": -55,
                        "ant": 2,
                        "status": "棚にある",
                    }
                },
                "table_rows_by_epc": {"E200TABLE": 0},
                "log": lambda message, *args, **kwargs: log_messages.append(message),
            },
        )

        try:
            save_csv()

            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))
        finally:
            Path(path).unlink(missing_ok=True)

        self.assertEqual(rows[1], ["E200CACHE", "キャッシュタイトル", "-55", "2", "棚にある"])
        self.assertEqual(log_messages, [f"CSV保存: {path}"])

    def test_save_csv_falls_back_to_table_values_when_cache_missing(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            path = tmp.name

        table = _FakeTable(
            [
                {
                    0: _FakeTableItem("表示タイトル"),
                    2: _FakeTableItem("4"),
                    3: _FakeTableItem("返却"),
                }
            ]
        )
        save_csv = load_main_function(
            "save_csv",
            {
                "QFileDialog": SimpleNamespace(
                    getSaveFileName=lambda *args, **kwargs: (path, "CSV Files (*.csv)")
                ),
                "window": SimpleNamespace(tableTags=table),
                "csv": csv,
                "table_details_by_row": {},
                "table_rows_by_epc": {"E200FALLBACK": 0},
                "log": lambda *args, **kwargs: None,
            },
        )

        try:
            save_csv()

            with open(path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.reader(f))
        finally:
            Path(path).unlink(missing_ok=True)

        self.assertEqual(rows[1], ["E200FALLBACK", "表示タイトル", "", "4", "返却"])


if __name__ == "__main__":
    unittest.main()
