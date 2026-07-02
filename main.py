import resources_rc
import csv
import html
import json
import os
import sqlite3
import sys

from app_config import APP_VERSION, DB_PATH, SETTINGS_PATH, DEFAULT_SETTINGS
from services.settings_service import load_settings, save_settings
from services.database_service import get_connection, ensure_database
from datetime import datetime

from PySide6.QtCore import QFile, QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtUiTools import QUiLoader
from qt_material import apply_stylesheet

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHeaderView,
    QDialog,
    QLabel,
    QMessageBox,
    QStyle,
    QTableWidgetItem,
)

from reader.uhf_reader import UHFReader
from widgets.table_items import make_table_item, shorten_text, status_item, set_rssi_cell
from serial.tools import list_ports
from PySide6.QtGui import QIcon

settings = load_settings()
LOST_TIMEOUT_SEC = int(settings.get("lost_timeout_sec", 10))
AUTO_BOOKMASTER_PATH = settings.get("bookmaster_path", "/home/ncc/ドキュメント/bookmaster.csv")

tag_states = {}
active_taken = {}
table_rows_by_epc = {}
table_details_by_row = {}
title_display_mode_by_epc = {}
latest_read_title = "-"
latest_read_epc = "-"
latest_detect_count = 0
log_entries = []

app = QApplication(sys.argv)

apply_stylesheet(
    app,
    theme="light_blue_500.xml"
)

ui_file = QFile("ui/main_window.ui")
ui_file.open(QFile.ReadOnly)

loader = QUiLoader()
window = loader.load(ui_file)
ui_file.close()

window.setWindowTitle(f"NCC UHF Manager {APP_VERSION}")

reader = UHFReader()
seen_epcs = set()

timer = QTimer()
timer.setInterval(int(settings.get("read_interval_ms", 500)))

clock_timer = QTimer()
clock_timer.setInterval(1000)


def log(message, level="INFO"):
    global log_entries

    now = datetime.now().strftime("%H:%M:%S")
    safe_message = html.escape(str(message))
    level_upper = str(level).upper()

    if level_upper == "SUCCESS":
        color = "#2e7d32"
        mark = "✓"
    elif level_upper == "WARN":
        color = "#ef6c00"
        mark = "⚠"
    elif level_upper == "ERROR" or "ERROR" in str(message):
        color = "#c62828"
        mark = "✕"
    else:
        color = "#1565c0"
        mark = "•"

    line = (
        f'<span style="color:{color}; font-weight:700;">'
        f'[{now}] {mark}</span> '
        f'<span style="color:{color};">{safe_message}</span>'
    )

    log_entries.append(line)
    log_entries = log_entries[-10:]

    if hasattr(window, "textLog"):
        window.textLog.setHtml("<br>".join(log_entries))




def set_label_short(label, text, max_len=42):
    label.setText(shorten_text(text, max_len))
    label.setToolTip(str(text or ""))











def rssi_level_text(rssi):
    try:
        value = int(rssi)
    except Exception:
        value = -100

    if value >= -60:
        return "強"
    if value >= -75:
        return "普通"
    return "弱"


def set_row_detail(row, epc, title, rssi, ant, status):
    table_details_by_row[row] = {
        "epc": epc,
        "title": title,
        "rssi": rssi,
        "ant": ant,
        "status": status,
    }


def update_row_detail_status(row, status):
    if row in table_details_by_row:
        table_details_by_row[row]["status"] = status


def show_tag_detail(row, column):
    info = table_details_by_row.get(row)
    if not info:
        return

    title = info.get("title", "-")
    epc = info.get("epc", "-")
    rssi = info.get("rssi", "-")
    ant = info.get("ant", "-")
    status = info.get("status", "-")
    level = rssi_level_text(rssi)

    QMessageBox.information(
        window,
        "タグ詳細",
        f"書籍名\n{title}\n\n"
        f"EPC\n{epc}\n\n"
        f"読取強度\n{rssi} dBm（{level}）\n\n"
        f"ANT\n{ant}\n\n"
        f"状態\n{status}"
    )






def set_status_cell(row, column, status):
    text = status_display(status)
    fg, bg = status_color_info(status)

    item = QTableWidgetItem(status)
    item.setToolTip(status)
    window.tableTags.setItem(row, column, item)

    label = QLabel(text)
    label.setToolTip(status)
    label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
    label.setStyleSheet(f"""
        QLabel {{
            color: {fg};
            background-color: {bg};
            font-size: 13px;
            font-weight: 800;
            padding-left: 6px;
        }}
    """)

    window.tableTags.setCellWidget(row, column, label)




def make_title_item(epc, title):
    mode = title_display_mode_by_epc.get(epc, "title")

    if mode == "epc":
        return make_table_item(epc, epc)

    return make_table_item(shorten_text(title, 28), title)


def toggle_title_epc(row, column):
    # 書籍名列だけクリック切替
    if column != 1:
        return

    epc_item = window.tableTags.item(row, 0)
    title_item = window.tableTags.item(row, 1)

    if not epc_item or not title_item:
        return

    epc = epc_item.toolTip() or epc_item.text()
    title = get_book_title(epc)

    current_mode = title_display_mode_by_epc.get(epc, "title")

    if current_mode == "title":
        title_display_mode_by_epc[epc] = "epc"
        window.tableTags.setItem(row, 1, make_table_item(epc, epc))
    else:
        title_display_mode_by_epc[epc] = "title"
        window.tableTags.setItem(row, 1, make_title_item(epc, title))

def setup_ui_polish():
    # 最新EPCを大きく・見やすくする
    # ログ欄
    if hasattr(window, "textLog"):
        window.textLog.setReadOnly(True)
        window.textLog.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                border: 1px solid #90caf9;
                border-radius: 6px;
                background: #ffffff;
                padding: 6px;
            }
        """)

    # テーブル
    if hasattr(window, "tableTags"):
        window.tableTags.setAlternatingRowColors(True)
        window.tableTags.verticalHeader().hide()
        window.tableTags.setSortingEnabled(False)
        header = window.tableTags.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)

        header.setSectionResizeMode(1, QHeaderView.Fixed)
        window.tableTags.setColumnWidth(1, 115)

        header.setSectionResizeMode(2, QHeaderView.Fixed)
        window.tableTags.setColumnWidth(2, 55)

        header.setSectionResizeMode(3, QHeaderView.Fixed)
        window.tableTags.setColumnWidth(3, 75)
        window.tableTags.setStyleSheet("""
            QTableWidget {
                font-size: 13px;
                background: #ffffff;
                alternate-background-color: #f5f7fa;
                gridline-color: #d0d7de;
            }
            QHeaderView::section {
                font-weight: 700;
                background: #eef3f8;
                padding: 6px;
                border: 1px solid #d0d7de;
            }
        """)

    # ボタンを業務アプリ風に統一
    button_settings = {
        "buttonConnect": "接続",
        "buttonStart": "読取開始",
        "buttonStop": "停止",
        "buttonClear": "クリア",
        "buttonSettings": "設定",
        "buttonSaveCsv": "CSV保存",
        "buttonLoadBooks": "書籍取込",
    }

    for name, text in button_settings.items():
        if hasattr(window, name):
            btn = getattr(window, name)
            btn.setText(text)
            btn.setMinimumHeight(44)
            btn.setMinimumWidth(105)
            btn.setStyleSheet("""
                QPushButton {
                    font-weight: 700;
                    padding: 8px 14px;
                    border-radius: 7px;
                }
            """)


def create_label(parent, text, x, y, w, h, style=""):
    label = QLabel(text, parent)
    label.setGeometry(x, y, w, h)
    if style:
        label.setStyleSheet(style)
    label.show()
    return label


def setup_dashboard_cards():
    if hasattr(window, "groupLatest"):
        window.groupLatest.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                margin-top: 10px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)

    if hasattr(window, "groupReader"):
        window.groupReader.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                margin-top: 10px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)

    if hasattr(window, "groupLog"):
        window.groupLog.setStyleSheet("""
            QGroupBox {
                font-weight: 700;
                border: 1px solid #bbdefb;
                border-radius: 8px;
                margin-top: 10px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)

    if hasattr(window, "labelLatestBookCard"):
        window.labelLatestBookCard.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: 800;
                color: #1565c0;
                padding: 6px;
            }
        """)
        window.labelLatestBookCard.setWordWrap(False)
        window.labelLatestBookCard.setFixedHeight(34)

    if hasattr(window, "labelLatestEpcCard"):
        window.labelLatestEpcCard.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #555555;
                padding: 4px 6px;
            }
        """)
        window.labelLatestEpcCard.setWordWrap(False)
        window.labelLatestEpcCard.setFixedHeight(26)

    if hasattr(window, "labelReaderInfoCard"):
        window.labelReaderInfoCard.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 700;
                color: #1565c0;
                padding: 6px;
            }
        """)
        window.labelReaderInfoCard.setWordWrap(True)


def update_dashboard_cards():
    conn = "接続中" if reader.is_connected() else "未接続"
    ant = "-"
    tx = "-"

    if reader.is_connected():
        try:
            ant = reader.get_antenna()
        except Exception:
            ant = "-"

        try:
            tx = reader.get_tx_power()
        except Exception:
            tx = "-"

    connection_type = settings.get("connection_type", "USB")
    reader_model = settings.get("reader_model", "UXA250-4")

    if connection_type == "LAN":
        target = f'{settings.get("host", "-")}:{settings.get("tcp_port", "-")}'
    else:
        target = settings.get("port", "-")

    values = {
        "labelReaderModel": reader_model,
        "labelReaderConnectionType": connection_type,
        "labelReaderTarget": target,
        "labelReaderAntenna": f"ANT{ant}" if ant != "-" else "-",
        "labelReaderTxPower": str(tx),
        "labelReaderDetectCount": f"{latest_detect_count}冊",
    }

    for name, value in values.items():
        if hasattr(window, name):
            label = getattr(window, name)
            label.setText(value)
            label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    font-weight: 700;
                    color: #1565c0;
                }
            """)

    if hasattr(window, "labelReaderConnectionStatus"):
        window.labelReaderConnectionStatus.setText(f"● {conn}")

        if reader.is_connected():
            color = "#2e7d32"
        else:
            color = "#c62828"

        window.labelReaderConnectionStatus.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: 800;
                color: {color};
            }}
        """)

    title_names = [
        "labelReaderModelTitle",
        "labelReaderStatusTitle",
        "labelReaderConnectionTypeTitle",
        "labelReaderTargetTitle",
        "labelReaderAntennaTitle",
        "labelReaderTxPowerTitle",
        "labelReaderDetectCountTitle",
    ]

    for name in title_names:
        if hasattr(window, name):
            getattr(window, name).setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #666666;
                    font-weight: 600;
                    padding-right: 8px;
                }
            """)


def update_clock():
    if hasattr(window, "labelClock"):
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        window.labelClock.setText(now)
        window.labelClock.setStyleSheet("""
            QLabel {
                font-size: 13px;
                font-weight: 700;
                color: #1565c0;
                padding: 4px 8px;
            }
        """)

def ensure_db():
    ensure_database()


def get_book_title(epc):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT title FROM books WHERE epc = ?", (epc,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "未登録"


def save_book_event(epc, rssi, ant):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO book_events (
            detected_at,
            epc,
            rssi,
            ant
        )
        VALUES (?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        epc,
        rssi,
        ant,
    ))

    conn.commit()
    conn.close()

def save_movement(epc, event_type, event_at, duration_sec=None):
    title = get_book_title(epc)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO book_movements (
            epc,
            title,
            event_type,
            event_at,
            duration_sec
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        epc,
        title,
        event_type,
        event_at.strftime("%Y-%m-%d %H:%M:%S"),
        duration_sec,
    ))

    conn.commit()
    conn.close()


def set_row_status(epc, status, color=None):
    row = table_rows_by_epc.get(epc)
    if row is None:
        return

    set_status_cell(row, 3, status)
    update_row_detail_status(row, status)

    if color is None:
       for col in range(window.tableTags.columnCount()):
           cell = window.tableTags.item(row, col)
           if cell:
               cell.setBackground(QColor(255, 255, 255))
       return

    for col in range(window.tableTags.columnCount()):
        cell = window.tableTags.item(row, col)
        if cell:
            cell.setBackground(color)


def check_movements(current_epcs):
    now = datetime.now()

    for epc in current_epcs:
        if epc not in tag_states:
            tag_states[epc] = {
                "present": True,
                "last_seen": now,
                "status_at": now
            }

            set_row_status(epc, "棚にある")
            continue

        if not tag_states[epc]["present"]:
            taken_at = active_taken.pop(epc, None)

            duration_sec = None
            if taken_at:
                duration_sec = int((now - taken_at).total_seconds())

            save_movement(epc, "RETURNED", now, duration_sec)
            tag_states[epc]["present"] = True
            tag_states[epc]["last_seen"] = now

            set_row_status(epc, "返却", QColor(180, 220, 255))
            tag_states[epc]["status_at"] = now
            log(f"返却検知: {get_book_title(epc)} / {epc}")

            continue

        tag_states[epc]["last_seen"] = now

        status_elapsed = (now - tag_states[epc].get("status_at", now)).total_seconds()
        current_status_item = None
        row = table_rows_by_epc.get(epc)
        if row is not None:
            current_status_item = window.tableTags.item(row, 3)

        current_status = current_status_item.text() if current_status_item else ""

        if current_status == "返却" and status_elapsed < 10:
            continue

        set_row_status(epc, "棚にある")

    for epc, state in list(tag_states.items()):
        if state["present"] and epc not in current_epcs:
            elapsed = (now - state["last_seen"]).total_seconds()

            if elapsed >= LOST_TIMEOUT_SEC:
                state["present"] = False
                active_taken[epc] = now

                save_movement(epc, "TAKEN", now)
                set_row_status(epc, "持出", QColor(255, 190, 190))
                log(f"持出検知: {get_book_title(epc)} / {epc}")


def setup_table():
    window.tableTags.setColumnCount(4)
    window.tableTags.setHorizontalHeaderLabels(["書籍名", "読取強度", "ANT", "状態"])
    window.tableTags.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    window.tableTags.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

def connect_reader():
    try:
        if reader.is_connected():
            log("すでに接続済みです")
            update_dashboard_cards()
            return

        connection_type = settings.get("connection_type", "USB")

        if connection_type == "LAN":
            host = settings.get("host", "192.168.1.100")
            tcp_port = int(settings.get("tcp_port", 10001))

            if reader.connect_tcp(host, tcp_port):
                log(f"LAN接続成功 ({host}:{tcp_port})", "SUCCESS")
            else:
                log(f"LAN接続失敗 ({host}:{tcp_port})", "ERROR")
                update_dashboard_cards()
                return

        else:
            port = settings.get("port", "/dev/ttyUSB0")
            baudrate = int(settings.get("baudrate", 115200))

            if reader.connect(port, baudrate):
                log(f"USB接続成功 ({port})", "SUCCESS")
            else:
                log(f"USB接続失敗 ({port})", "ERROR")
                update_dashboard_cards()
                return

        try:
            tx_power = int(settings.get("tx_power", 2400))
            if reader.set_tx_power(tx_power):
                current_tx_power = reader.get_tx_power()
                log(f"電波強度設定: {tx_power}")
                log(f"電波強度確認: {current_tx_power}")
            else:
                log(f"電波強度設定失敗: {tx_power}", "WARN")
        except Exception as e:
            log(f"電波強度設定エラー: {e}", "ERROR")

        update_dashboard_cards()

    except Exception as e:
        log(f"ERROR: {e}", "ERROR")
        update_dashboard_cards()



def read_once():
    try:
        if not reader.is_connected():
            log("ERROR: リーダ未接続です")
            return

        tags = []

        antenna_count = int(settings.get("antenna_count", 1))

        for ant_no in range(1, antenna_count + 1):
            try:
                reader.set_antenna(ant_no)
                ant_tags = reader.read_tags()

                for tag in ant_tags:
                    tag["ant"] = ant_no

                tags.extend(ant_tags)
            except Exception as e:
                log(f"ANT{ant_no} 読取失敗: {e}")

        current_epcs = set()

        if not tags:
            check_movements(current_epcs)
            return

        now_text = datetime.now().strftime("%H:%M:%S")
        new_count = 0

        for tag in tags:
            epc = tag.get("epc")
            rssi = tag.get("rssi")
            ant = tag.get("ant")

            if not epc:
                continue

            current_epcs.add(epc)
            title = get_book_title(epc)
            save_book_event(epc, rssi, ant)

            global latest_read_title, latest_read_epc, latest_detect_count
            latest_read_title = title if title and title != "未登録" else "未登録"
            latest_read_epc = epc
            latest_detect_count = len(tags)
            update_dashboard_cards()

            if epc in seen_epcs:
                row = table_rows_by_epc.get(epc)
                if row is not None:
                    title_item = make_table_item(shorten_text(title, 34), f"{title}\n\nEPC:\n{epc}")
                    window.tableTags.setItem(row, 0, title_item)
                    set_rssi_cell(window.tableTags, row, 1, rssi)
                    window.tableTags.setItem(row, 2, QTableWidgetItem(str(ant)))
                    set_row_detail(row, epc, title, rssi, ant, "棚にある")
                continue

            seen_epcs.add(epc)
            new_count += 1

            row = window.tableTags.rowCount()
            window.tableTags.insertRow(row)

            title_item = make_table_item(shorten_text(title, 34), f"{title}\n\nEPC:\n{epc}")
            window.tableTags.setItem(row, 0, title_item)
            set_rssi_cell(window.tableTags, row, 1, rssi)
            window.tableTags.setItem(row, 2, QTableWidgetItem(str(ant)))
            set_status_cell(row, 3, "棚にある")
            set_row_detail(row, epc, title, rssi, ant, "棚にある")
            table_rows_by_epc[epc] = row

        check_movements(current_epcs)
        if new_count > 0:
            log(f"新規タグ読取: {new_count}件 / 検出: {len(tags)}件", "INFO")

    except Exception as e:
        log(f"ERROR: {e}", "ERROR")


def start_reading():
    if not reader.is_connected():
        log("ERROR: リーダ未接続です")
        return

    if timer.isActive():
        log("連続読取はすでに開始済みです")
        return

    timer.start()
    log("連続読取を開始しました", "SUCCESS")


def stop_reading():
    if timer.isActive():
        timer.stop()
        log("連続読取を停止しました", "WARN")
    else:
        log("連続読取は停止中です")


def clear_table():
    seen_epcs.clear()
    title_display_mode_by_epc.clear()
    window.tableTags.setRowCount(0)
    log("表示をクリアしました")


def save_csv():
    path, _ = QFileDialog.getSaveFileName(
        window,
        "CSV保存",
        "uhf_tags.csv",
        "CSV Files (*.csv)"
    )

    if not path:
        return

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["EPC", "書籍名", "RSSI", "ANT", "状態"])

        for row in range(window.tableTags.rowCount()):
            values = []
            for col in range(window.tableTags.columnCount()):
                item = window.tableTags.item(row, col)
                values.append(item.text() if item else "")
            writer.writerow(values)

    log(f"CSV保存: {path}")


def load_books_from_path(path):
    if not os.path.exists(path):
        log(f"書籍マスタ自動読込失敗: ファイルなし {path}")
        return False

    count = 0

    conn = get_connection()
    cur = conn.cursor()

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader_csv = csv.reader(f)
        rows = list(reader_csv)

    if not rows:
        conn.close()
        log("書籍マスタ読込: 0件")
        return False

    header = [c.strip().lower() for c in rows[0]]

    title_names = ["title", "書籍名", "タイトル"]

    if "epc" in header and any(name in header for name in title_names):
        epc_index = header.index("epc")
        title_index = next(header.index(name) for name in title_names if name in header)
        data_rows = rows[1:]
    else:
        epc_index = 0
        title_index = 1
        data_rows = rows

    # 書籍マスタはCSV内容で入れ替える
    cur.execute("DELETE FROM books")

    for row in data_rows:
        if len(row) <= max(epc_index, title_index):
            continue

        epc = row[epc_index].strip()
        title = row[title_index].strip()

        if not epc or not title:
            continue

        cur.execute("""
            INSERT INTO books (epc, title)
            VALUES (?, ?)
            ON CONFLICT(epc) DO UPDATE SET
                title = excluded.title
        """, (epc, title))

        count += 1

    conn.commit()
    conn.close()

    log(f"書籍マスタ読込: {count}件")
    return True


def load_books():
    path, _ = QFileDialog.getOpenFileName(
        window,
        "書籍マスタ取込",
        "",
        "CSV Files (*.csv)"
    )

    if not path:
        return

    load_books_from_path(path)

def show_ranking():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            e.epc,
            COALESCE(b.title, '未登録') AS title,
            COUNT(*) AS cnt,
            AVG(e.rssi) AS avg_rssi,
            MAX(e.detected_at) AS last_detected_at
        FROM book_events e
        LEFT JOIN books b
            ON b.epc = e.epc
        GROUP BY e.epc, b.title
        ORDER BY cnt DESC
        LIMIT 20
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        QMessageBox.information(window, "ランキング", "読取データがありません。")
        return

    lines = []

    for i, (epc, title, cnt, avg_rssi, last_detected_at) in enumerate(rows, start=1):
        avg_text = "-" if avg_rssi is None else f"{avg_rssi:.1f}"

        lines.append(
            f"{i}位 {title} / {cnt}回\n"
            f"EPC: {epc}\n"
            f"平均RSSI: {avg_text}\n"
            f"最終: {last_detected_at}\n"
        )

    QMessageBox.information(window, "読取ランキング", "\n".join(lines))



def detect_serial_ports():
    ports = []

    for port in list_ports.comports():
        device = port.device
        desc = port.description or ""

        if not device:
            continue

        ports.append({
            "device": device,
            "description": desc,
            "vid": port.vid,
            "pid": port.pid,
        })

    return ports


def get_preferred_serial_port():
    ports = detect_serial_ports()

    # FTDI FT230X / FTDI系を優先
    for port in ports:
        desc = (port.get("description") or "").lower()
        vid = port.get("vid")
        pid = port.get("pid")

        if vid == 0x0403 and pid == 0x6015:
            return port["device"]

        if "ftdi" in desc or "ft230x" in desc:
            return port["device"]

    # 次に ttyUSB を優先
    for port in ports:
        if port["device"].startswith("/dev/ttyUSB"):
            return port["device"]

    # その他
    if ports:
        return ports[0]["device"]

    return ""


def show_settings():
    global settings, LOST_TIMEOUT_SEC, AUTO_BOOKMASTER_PATH

    ui_file = QFile("ui/settings_dialog.ui")
    ui_file.open(QFile.ReadOnly)

    loader = QUiLoader()
    dialog = loader.load(ui_file, window)
    ui_file.close()

    dialog.comboConnectionType.setCurrentText(settings.get("connection_type", "USB"))
    detected_port = get_preferred_serial_port()
    configured_port = settings.get("port", "/dev/ttyUSB0")
    dialog.linePort.setText(configured_port or detected_port or "/dev/ttyUSB0")
    dialog.lineHost.setText(settings.get("host", "192.168.1.100"))
    dialog.spinTcpPort.setValue(int(settings.get("tcp_port", 10001)))
    dialog.comboBaudrate.setCurrentText(str(settings.get("baudrate", 115200)))
    dialog.comboAntennaCount.setCurrentText(str(settings.get("antenna_count", 1)))
    dialog.checkAutoConnect.setChecked(bool(settings.get("auto_connect", True)))
    dialog.checkAutoLoadBooks.setChecked(bool(settings.get("auto_load_books", True)))
    dialog.checkAutoStartReading.setChecked(bool(settings.get("auto_start_reading", True)))
    dialog.lineBookmasterPath.setText(settings.get("bookmaster_path", "/home/ncc/ドキュメント/bookmaster.csv"))
    dialog.spinReadInterval.setValue(int(settings.get("read_interval_ms", 500)))
    dialog.spinLostTimeout.setValue(int(settings.get("lost_timeout_sec", 10)))
    dialog.spinTxPower.setValue(int(settings.get("tx_power", 2400)))

    def update_connection_fields():
        connection_type = dialog.comboConnectionType.currentText()

        is_lan = connection_type == "LAN"
        is_serial = connection_type in ("USB", "232C(UART)")

        dialog.linePort.setEnabled(is_serial)
        dialog.comboBaudrate.setEnabled(is_serial)

        dialog.lineHost.setEnabled(is_lan)
        dialog.spinTcpPort.setEnabled(is_lan)

    dialog.comboConnectionType.currentTextChanged.connect(update_connection_fields)
    update_connection_fields()

    if hasattr(dialog, "labelReaderConnection"):
        connection_type = settings.get("connection_type", "USB")
        if connection_type == "LAN":
            target = f'{settings.get("host", "-")}:{settings.get("tcp_port", "-")}'
        else:
            target = settings.get("port", "-")
        dialog.labelReaderConnection.setText(f"接続: {connection_type} / {target}")

    if hasattr(dialog, "labelReaderStatus"):
        if reader.is_connected():
            try:
                current_ant = reader.get_antenna()
            except Exception:
                current_ant = "-"

            try:
                current_tx_power = reader.get_tx_power()
            except Exception:
                current_tx_power = "-"

            dialog.labelReaderStatus.setText(
                f"ANT数　　 {current_ant} / 出力: {current_tx_power}"
            )
        else:
            dialog.labelReaderStatus.setText("ANT数　　 - / 出力: -")

    def save_and_close():
        global settings, LOST_TIMEOUT_SEC, AUTO_BOOKMASTER_PATH

        settings["connection_type"] = dialog.comboConnectionType.currentText()
        settings["port"] = dialog.linePort.text().strip() or "/dev/ttyUSB0"
        settings["host"] = dialog.lineHost.text().strip() or "192.168.1.100"
        settings["tcp_port"] = int(dialog.spinTcpPort.value())
        settings["baudrate"] = int(dialog.comboBaudrate.currentText())
        settings["antenna_count"] = int(dialog.comboAntennaCount.currentText())
        settings["auto_connect"] = dialog.checkAutoConnect.isChecked()
        settings["auto_load_books"] = dialog.checkAutoLoadBooks.isChecked()
        settings["auto_start_reading"] = dialog.checkAutoStartReading.isChecked()
        settings["bookmaster_path"] = dialog.lineBookmasterPath.text().strip()
        settings["read_interval_ms"] = int(dialog.spinReadInterval.value())
        settings["lost_timeout_sec"] = int(dialog.spinLostTimeout.value())
        settings["tx_power"] = int(dialog.spinTxPower.value())

        save_settings(settings)

        LOST_TIMEOUT_SEC = int(settings.get("lost_timeout_sec", 10))
        AUTO_BOOKMASTER_PATH = settings.get("bookmaster_path", "/home/ncc/ドキュメント/bookmaster.csv")
        timer.setInterval(int(settings.get("read_interval_ms", 500)))

        log("設定を保存しました")
        dialog.accept()

    dialog.buttonSave.clicked.connect(save_and_close)
    dialog.buttonCancel.clicked.connect(dialog.reject)

    def test_connection():
        connection_type = dialog.comboConnectionType.currentText()

        try:
            if connection_type == "LAN":
                host = dialog.lineHost.text().strip()
                tcp_port = int(dialog.spinTcpPort.value())

                test_reader = UHFReader()
                try:
                    if test_reader.connect_tcp(host, tcp_port):
                        QMessageBox.information(
                            dialog,
                            "接続テスト",
                            f"LAN接続成功\n{host}:{tcp_port}"
                        )
                    else:
                        QMessageBox.warning(
                            dialog,
                            "接続テスト",
                            f"LAN接続失敗\n{host}:{tcp_port}"
                        )
                finally:
                    test_reader.close()

            elif connection_type in ("USB", "232C(UART)"):
                port = dialog.linePort.text().strip() or get_preferred_serial_port() or "/dev/ttyUSB0"
                baudrate = int(dialog.comboBaudrate.currentText())

                test_reader = UHFReader()
                try:
                    if test_reader.connect(port, baudrate):
                        QMessageBox.information(
                            dialog,
                            "接続テスト",
                            f"{connection_type} 接続成功\n{port} / {baudrate}bps"
                        )
                    else:
                        QMessageBox.warning(
                            dialog,
                            "接続テスト",
                            f"{connection_type} 接続失敗\n{port}"
                        )
                finally:
                    test_reader.close()

            else:
                QMessageBox.warning(
                    dialog,
                    "接続テスト",
                    f"未対応の接続方式です: {connection_type}"
                )

        except Exception as e:
            QMessageBox.warning(
                dialog,
                "接続テスト",
                f"接続失敗\n{e}"
            )

    if hasattr(dialog, "buttonTestConnection"):
        dialog.buttonTestConnection.clicked.connect(test_connection)

    dialog.exec()


def auto_startup():
    if settings.get("auto_connect", True):
        connect_reader()
    else:
        log("自動接続: OFF")
        return

    if not reader.is_connected():
        log("自動開始中止: リーダ未接続")
        return

    if settings.get("auto_load_books", True):
        if not load_books_from_path(AUTO_BOOKMASTER_PATH):
            log("自動開始中止: 書籍マスタ読込失敗")
            return
    else:
        log("書籍マスタ自動読込: OFF")

    if settings.get("auto_start_reading", True):
        start_reading()
    else:
        log("自動読取開始: OFF")

ensure_db()
setup_table()
setup_ui_polish()
setup_dashboard_cards()

timer.timeout.connect(read_once)
clock_timer.timeout.connect(update_clock)
clock_timer.start()
update_clock()

window.buttonConnect.clicked.connect(connect_reader)
window.buttonSettings.clicked.connect(show_settings)
window.buttonStart.clicked.connect(start_reading)
window.buttonStop.clicked.connect(stop_reading)
window.buttonClear.clicked.connect(clear_table)

if hasattr(window, "buttonSaveCsv"):
    window.buttonSaveCsv.clicked.connect(save_csv)

if hasattr(window, "buttonLoadBooks"):
    window.buttonLoadBooks.clicked.connect(load_books)
window.tableTags.cellDoubleClicked.connect(show_tag_detail)

if hasattr(window, "buttonRanking"):
    window.buttonRanking.clicked.connect(show_ranking)

log(f"NCC UHF Manager {APP_VERSION} 起動")

if hasattr(window, "labelStatus"):
    window.labelStatus.setText("接続状態: 未接続")
    window.labelStatus.setStyleSheet(
        "color: red; font-weight: bold;"
    )
window.show()
update_dashboard_cards()
QTimer.singleShot(500, auto_startup)
sys.exit(app.exec())
