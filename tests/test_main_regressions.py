import ast
import copy
import csv
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

from app_config import APP_VERSION, DEFAULT_SETTINGS
from services import settings_service as settings_service_module


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


class _FakeEditableTable:
    def __init__(self):
        self._rows = []
        self._cell_widgets = {}

    def rowCount(self):
        return len(self._rows)

    def insertRow(self, row):
        if row != len(self._rows):
            raise AssertionError(f"Unexpected insertRow index: {row}")
        self._rows.append({})

    def setItem(self, row, column, item):
        self._rows[row][column] = item

    def setCellWidget(self, row, column, widget):
        self._cell_widgets[(row, column)] = widget

    def item(self, row, column):
        return self._rows[row].get(column)


class _FakeLabel:
    def __init__(self):
        self.value = None
        self.style = None

    def setText(self, value):
        self.value = value

    def text(self):
        return self.value

    def setStyleSheet(self, style):
        self.style = style


class _FakeStatusTable:
    def __init__(self, row_to_epc, status_by_epc):
        self._row_to_epc = row_to_epc
        self._status_by_epc = status_by_epc

    def item(self, row, column):
        if column != 3:
            return None

        epc = self._row_to_epc.get(row)
        status = self._status_by_epc.get(epc)
        if status is None:
            return None

        return _FakeTableItem(status)


class MainRegressionTests(unittest.TestCase):
    def make_temp_csv_path(self):
        fd, path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        self.addCleanup(Path(path).unlink, missing_ok=True)
        return path

    def test_read_once_lan_switches_antennas(self):
        reader = _FakeReader(tags_by_read=[[], [], [], []])
        movement_calls = []
        read_once = load_main_function(
            "read_once",
            {
                "reader": reader,
                "settings": {"connection_type": "LAN", "antenna_count": 4},
                "log": lambda *args, **kwargs: None,
                "check_movements": lambda epcs: movement_calls.append(epcs),
            },
        )

        read_once()

        self.assertEqual(reader.set_antenna_calls, [1, 2, 3, 4])
        self.assertEqual(reader.read_calls, 4)
        self.assertEqual(movement_calls, [set()])

    def test_read_once_lan_antenna_count_1(self):
        reader = _FakeReader(tags_by_read=[[]])
        movement_calls = []
        read_once = load_main_function(
            "read_once",
            {
                "reader": reader,
                "settings": {"connection_type": "LAN", "antenna_count": 1},
                "log": lambda *args, **kwargs: None,
                "check_movements": lambda epcs: movement_calls.append(epcs),
            },
        )

        read_once()

        self.assertEqual(reader.set_antenna_calls, [1])
        self.assertEqual(reader.read_calls, 1)
        self.assertEqual(movement_calls, [set()])

    def test_read_once_lan_antenna_count_2(self):
        reader = _FakeReader(tags_by_read=[[], []])
        movement_calls = []
        read_once = load_main_function(
            "read_once",
            {
                "reader": reader,
                "settings": {"connection_type": "LAN", "antenna_count": 2},
                "log": lambda *args, **kwargs: None,
                "check_movements": lambda epcs: movement_calls.append(epcs),
            },
        )

        read_once()

        self.assertEqual(reader.set_antenna_calls, [1, 2])
        self.assertEqual(reader.read_calls, 2)
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
                        "log": lambda *args, **kwargs: None,
                        "check_movements": lambda epcs: movement_calls.append(epcs),
                    },
                )

                read_once()

                self.assertEqual(reader.set_antenna_calls, [1, 2, 3])
                self.assertEqual(reader.read_calls, 3)
                self.assertEqual(movement_calls, [set()])

    def test_save_csv_uses_cached_details_when_available(self):
        path = self.make_temp_csv_path()

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

        save_csv()

        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))

        self.assertEqual(rows[1], ["E200CACHE", "キャッシュタイトル", "-55", "2", "棚にある"])
        self.assertEqual(log_messages, [f"CSV保存: {path}"])

    def test_save_csv_falls_back_to_table_values_when_cache_missing(self):
        path = self.make_temp_csv_path()

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

        save_csv()

        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))

        self.assertEqual(rows[1], ["E200FALLBACK", "表示タイトル", "", "4", "返却"])

    def test_check_movements_does_not_mark_taken_by_time_alone(self):
        current_now = datetime(2026, 7, 3, 12, 0, 0)

        class _FakeDateTime:
            @staticmethod
            def now():
                return current_now

        save_calls = []
        status_calls = []
        tag_states = {
            "E200TIME": {
                "present": True,
                "last_seen": current_now - timedelta(seconds=6),
                "status_at": current_now - timedelta(seconds=6),
                "missed_count": 1,
            }
        }
        active_taken = {}
        check_movements = load_main_function(
            "check_movements",
            {
                "datetime": _FakeDateTime,
                "tag_states": tag_states,
                "active_taken": active_taken,
                "LOST_TIMEOUT_SEC": 5,
                "LOST_DETECTION_COUNT": 3,
                "save_movement": lambda *args: save_calls.append(args),
                "set_row_status": lambda *args: status_calls.append(args),
                "log": lambda *args, **kwargs: None,
                "get_book_title": lambda epc: epc,
                "QColor": lambda *args: args,
            },
        )

        check_movements(set())

        self.assertTrue(tag_states["E200TIME"]["present"])
        self.assertEqual(tag_states["E200TIME"]["missed_count"], 2)
        self.assertEqual(active_taken, {})
        self.assertEqual(save_calls, [])
        self.assertEqual(status_calls, [])

    def test_check_movements_marks_taken_after_time_and_consecutive_misses(self):
        current_now = datetime(2026, 7, 3, 12, 0, 0)

        class _FakeDateTime:
            @staticmethod
            def now():
                return current_now

        save_calls = []
        status_calls = []
        logs = []
        tag_states = {
            "E200TAKEN": {
                "present": True,
                "last_seen": current_now - timedelta(seconds=6),
                "status_at": current_now - timedelta(seconds=6),
                "missed_count": 2,
            }
        }
        active_taken = {}
        check_movements = load_main_function(
            "check_movements",
            {
                "datetime": _FakeDateTime,
                "tag_states": tag_states,
                "active_taken": active_taken,
                "LOST_TIMEOUT_SEC": 5,
                "LOST_DETECTION_COUNT": 3,
                "save_movement": lambda *args: save_calls.append(args),
                "set_row_status": lambda *args: status_calls.append(args),
                "log": lambda message, *args, **kwargs: logs.append(message),
                "get_book_title": lambda epc: "テスト書籍",
                "QColor": lambda *args: args,
            },
        )

        check_movements(set())

        self.assertFalse(tag_states["E200TAKEN"]["present"])
        self.assertEqual(tag_states["E200TAKEN"]["missed_count"], 3)
        self.assertEqual(active_taken, {"E200TAKEN": current_now})
        self.assertEqual(save_calls, [("E200TAKEN", "TAKEN", current_now)])
        self.assertEqual(status_calls, [("E200TAKEN", "持出", (255, 190, 190))])
        self.assertEqual(logs, ["持出検知: テスト書籍 / E200TAKEN"])

    def test_check_movements_resets_missed_count_when_tag_is_seen_again(self):
        current_now = datetime(2026, 7, 3, 12, 0, 0)

        class _FakeDateTime:
            @staticmethod
            def now():
                return current_now

        tag_states = {
            "E200RESET": {
                "present": True,
                "last_seen": current_now - timedelta(seconds=6),
                "status_at": current_now - timedelta(seconds=6),
                "missed_count": 2,
            }
        }
        check_movements = load_main_function(
            "check_movements",
            {
                "datetime": _FakeDateTime,
                "tag_states": tag_states,
                "active_taken": {},
                "LOST_TIMEOUT_SEC": 5,
                "LOST_DETECTION_COUNT": 3,
                "save_movement": lambda *args: None,
                "set_row_status": lambda *args: None,
                "log": lambda *args, **kwargs: None,
                "get_book_title": lambda epc: epc,
                "QColor": lambda *args: args,
                "table_rows_by_epc": {},
                "window": SimpleNamespace(tableTags=SimpleNamespace(item=lambda *args: None)),
            },
        )

        check_movements({"E200RESET"})

        self.assertTrue(tag_states["E200RESET"]["present"])
        self.assertEqual(tag_states["E200RESET"]["last_seen"], current_now)
        self.assertEqual(tag_states["E200RESET"]["missed_count"], 0)

    def test_check_movements_counts_misses_per_cycle_per_tag(self):
        current_now = datetime(2026, 7, 3, 12, 0, 0)

        class _FakeDateTime:
            @staticmethod
            def now():
                return current_now

        tag_states = {
            "E200MISS": {
                "present": True,
                "last_seen": current_now - timedelta(seconds=6),
                "status_at": current_now - timedelta(seconds=6),
                "missed_count": 1,
            },
            "E200SEEN": {
                "present": True,
                "last_seen": current_now - timedelta(seconds=6),
                "status_at": current_now - timedelta(seconds=6),
                "missed_count": 2,
            },
        }
        check_movements = load_main_function(
            "check_movements",
            {
                "datetime": _FakeDateTime,
                "tag_states": tag_states,
                "active_taken": {},
                "LOST_TIMEOUT_SEC": 5,
                "LOST_DETECTION_COUNT": 99,
                "save_movement": lambda *args: None,
                "set_row_status": lambda *args: None,
                "log": lambda *args, **kwargs: None,
                "get_book_title": lambda epc: epc,
                "QColor": lambda *args: args,
                "table_rows_by_epc": {},
                "window": SimpleNamespace(tableTags=SimpleNamespace(item=lambda *args: None)),
            },
        )

        check_movements({"E200SEEN"})

        self.assertEqual(tag_states["E200MISS"]["missed_count"], 2)
        self.assertEqual(tag_states["E200SEEN"]["missed_count"], 0)
        self.assertEqual(tag_states["E200SEEN"]["last_seen"], current_now)

        current_now = current_now + timedelta(seconds=1)
        check_movements({"E200SEEN"})

        self.assertEqual(tag_states["E200MISS"]["missed_count"], 3)
        self.assertEqual(tag_states["E200SEEN"]["missed_count"], 0)

    def test_check_movements_returns_taken_tag_then_restores_on_shelf(self):
        current_now = datetime(2026, 7, 3, 12, 0, 0)

        class _FakeDateTime:
            @staticmethod
            def now():
                return current_now

        save_calls = []
        status_calls = []
        epc = "E200RETURN"
        row_to_epc = {0: epc}
        status_by_epc = {epc: "持出"}
        tag_states = {
            epc: {
                "present": False,
                "last_seen": current_now - timedelta(seconds=20),
                "status_at": current_now - timedelta(seconds=20),
                "missed_count": 3,
            }
        }
        active_taken = {epc: current_now - timedelta(seconds=30)}

        def set_row_status(target_epc, status, color=None):
            status_by_epc[target_epc] = status
            status_calls.append((target_epc, status, color))

        check_movements = load_main_function(
            "check_movements",
            {
                "datetime": _FakeDateTime,
                "tag_states": tag_states,
                "active_taken": active_taken,
                "LOST_TIMEOUT_SEC": 5,
                "LOST_DETECTION_COUNT": 3,
                "save_movement": lambda *args: save_calls.append(args),
                "set_row_status": set_row_status,
                "log": lambda *args, **kwargs: None,
                "get_book_title": lambda seen_epc: seen_epc,
                "QColor": lambda *args: args,
                "table_rows_by_epc": {epc: 0},
                "window": SimpleNamespace(
                    tableTags=_FakeStatusTable(row_to_epc, status_by_epc)
                ),
            },
        )

        check_movements({epc})

        self.assertTrue(tag_states[epc]["present"])
        self.assertEqual(tag_states[epc]["missed_count"], 0)
        self.assertEqual(save_calls, [(epc, "RETURNED", current_now, 30)])
        self.assertEqual(status_calls, [(epc, "返却", (180, 220, 255))])
        self.assertEqual(status_by_epc[epc], "返却")

        current_now = current_now + timedelta(seconds=11)
        status_calls.clear()
        save_calls.clear()

        check_movements({epc})

        self.assertEqual(save_calls, [])
        self.assertEqual(status_calls, [(epc, "棚にある", None)])
        self.assertEqual(status_by_epc[epc], "棚にある")

    def test_settings_service_persists_lost_detection_count(self):
        original_cwd = os.getcwd()

        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                settings = DEFAULT_SETTINGS.copy()
                settings["lost_detection_count"] = 7
                settings_service_module.save_settings(settings)
                reloaded = settings_service_module.load_settings()
            finally:
                os.chdir(original_cwd)

        self.assertEqual(reloaded["lost_detection_count"], 7)
        self.assertEqual(reloaded["lost_timeout_sec"], DEFAULT_SETTINGS["lost_timeout_sec"])

    def test_read_once_deduplicates_epc_and_counts_unique_tags(self):
        reader = _FakeReader(
            tags_by_read=[
                [{"epc": "E200DUP", "rssi": -70}],
                [{"epc": "E200DUP", "rssi": -60}],
                [{"epc": "E200UNIQ", "rssi": -80}],
            ]
        )
        movement_calls = []
        save_calls = []
        table = _FakeEditableTable()
        table_rows_by_epc = {}
        table_details_by_row = {}
        globals_dict = {
            "reader": reader,
            "settings": {"connection_type": "LAN", "antenna_count": 3},
            "seen_epcs": set(),
            "table_rows_by_epc": table_rows_by_epc,
            "table_details_by_row": table_details_by_row,
            "window": SimpleNamespace(tableTags=table),
            "QTableWidgetItem": _FakeTableItem,
            "make_table_item": lambda text, tooltip=None: _FakeTableItem(text),
            "shorten_text": lambda text, max_len=42: text,
            "set_rssi_cell": lambda table_obj, row, column, rssi: table_obj.setItem(
                row, column, _FakeTableItem(str(rssi))
            ),
            "set_status_cell": lambda row, column, status: table.setItem(
                row, column, _FakeTableItem(status)
            ),
            "set_row_detail": lambda row, epc, title, rssi, ant, status: table_details_by_row.update(
                {
                    row: {
                        "epc": epc,
                        "title": title,
                        "rssi": rssi,
                        "ant": ant,
                        "status": status,
                    }
                }
            ),
            "get_book_title": lambda epc: f"title:{epc}",
            "save_book_event": lambda epc, rssi, ant: save_calls.append((epc, rssi, ant)),
            "check_movements": lambda epcs: movement_calls.append(epcs),
            "update_dashboard_cards": lambda: None,
            "log": lambda *args, **kwargs: None,
            "latest_read_title": "-",
            "latest_read_epc": "-",
            "latest_detect_count": 0,
        }
        read_once = load_main_function("read_once", globals_dict)

        read_once()

        self.assertEqual(table.rowCount(), 2)
        self.assertEqual(set(table_rows_by_epc.keys()), {"E200DUP", "E200UNIQ"})
        self.assertEqual(movement_calls, [{"E200DUP", "E200UNIQ"}])
        self.assertEqual(read_once.__globals__["latest_detect_count"], 2)
        self.assertEqual(len(save_calls), 2)
        self.assertEqual(
            sorted(epc for epc, _, _ in save_calls),
            ["E200DUP", "E200UNIQ"],
        )

        dup_row = table_rows_by_epc["E200DUP"]
        self.assertEqual(table.item(dup_row, 1).text(), "-60")
        self.assertEqual(table.item(dup_row, 2).text(), "2")
        self.assertEqual(table_details_by_row[dup_row]["ant"], 2)
        self.assertEqual(table_details_by_row[dup_row]["rssi"], -60)

    def test_update_dashboard_cards_shows_configured_antenna_count(self):
        labels = {
            "labelReaderModel": _FakeLabel(),
            "labelReaderConnectionType": _FakeLabel(),
            "labelReaderTarget": _FakeLabel(),
            "labelReaderAntenna": _FakeLabel(),
            "labelReaderTxPower": _FakeLabel(),
            "labelReaderDetectCount": _FakeLabel(),
            "labelReaderConnectionStatus": _FakeLabel(),
            "labelLatestBookCard": _FakeLabel(),
            "labelLatestEpcCard": _FakeLabel(),
            "labelReaderModelTitle": _FakeLabel(),
            "labelReaderStatusTitle": _FakeLabel(),
            "labelReaderConnectionTypeTitle": _FakeLabel(),
            "labelReaderTargetTitle": _FakeLabel(),
            "labelReaderAntennaTitle": _FakeLabel(),
            "labelReaderTxPowerTitle": _FakeLabel(),
            "labelReaderDetectCountTitle": _FakeLabel(),
        }
        window = SimpleNamespace(**labels)
        update_dashboard_cards = load_main_function(
            "update_dashboard_cards",
            {
                "reader": SimpleNamespace(
                    is_connected=lambda: True,
                    get_tx_power=lambda: 2400,
                ),
                "settings": {
                    "connection_type": "LAN",
                    "reader_model": "UXA250-4",
                    "host": "192.168.1.10",
                    "tcp_port": 10001,
                    "antenna_count": 4,
                },
                "latest_detect_count": 7,
                "latest_read_title": "book",
                "latest_read_epc": "E200",
                "window": window,
                "set_label_short": lambda label, text, max_len=42: label.setText(text),
            },
        )

        update_dashboard_cards()

        self.assertEqual(window.labelReaderAntenna.text(), "4")
        self.assertEqual(window.labelReaderDetectCount.text(), "7冊")
        self.assertEqual(window.labelReaderConnectionStatus.text(), "● 接続中")

    def test_app_config_uses_v0134_checkout_defaults(self):
        self.assertEqual(APP_VERSION, "0.13.4")
        self.assertEqual(DEFAULT_SETTINGS["lost_timeout_sec"], 5)
        self.assertEqual(DEFAULT_SETTINGS["lost_detection_count"], 3)


if __name__ == "__main__":
    unittest.main()
