from PySide6.QtWidgets import QMessageBox


def rssi_level_text(rssi):
    try:
        value = int(rssi)
    except Exception:
        return "-"

    if value >= -60:
        return "?"
    if value >= -75:
        return "??"
    return "?"


def show_tag_detail(parent, table_details_by_row, row, column):
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
        parent,
        "????",
        f"???\\n{title}\\n\\n"
        f"EPC\\n{epc}\\n\\n"
        f"????\\n{rssi} dBm?{level}?\\n\\n"
        f"ANT\\n{ant}\\n\\n"
        f"??\\n{status}"
    )
