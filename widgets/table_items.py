from PySide6.QtGui import QColor
from PySide6.QtWidgets import QLabel, QTableWidgetItem


def shorten_text(text, max_len=42):
    text = str(text or "")
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def make_table_item(text, tooltip=None):
    item = QTableWidgetItem(str(text))
    if tooltip:
        item.setToolTip(str(tooltip))
    return item


def status_display(status):
    if status == "棚にある":
        return "● 棚にある"
    if status == "持出":
        return "● 持出"
    if status == "返却":
        return "● 返却"
    return status


def status_color_info(status):
    if status == "棚にある":
        return "#2e7d32", "#e8f5e9"
    if status == "持出":
        return "#c62828", "#ffebee"
    if status == "返却":
        return "#ef6c00", "#fff3e0"
    return "#333333", "#ffffff"


def status_item(status):
    item = QTableWidgetItem(status_display(status))
    item.setToolTip(status)
    fg, bg = status_color_info(status)
    item.setForeground(QColor(fg))
    item.setBackground(QColor(bg))
    return item


def rssi_level_info(rssi):
    try:
        value = int(rssi)
    except Exception:
        value = -100

    if value >= -60:
        return value, "?", 6, "#1565c0"
    elif value >= -75:
        return value, "??", 4, "#f9a825"
    else:
        return value, "?", 2, "#c62828"


def set_rssi_cell(table, row, column, rssi):
    value, level, bars, color = rssi_level_info(rssi)

    label = QLabel("?" * bars)
    label.setToolTip(f"????: {value} dBm\\n???: {level}")
    label.setToolTipDuration(5000)
    label.setMouseTracking(True)
    label.setStyleSheet(f'''
        QLabel {{
            color: {color};
            font-size: 15px;
            font-weight: 800;
            padding-left: 6px;
        }}
    ''')

    table.setCellWidget(row, column, label)
