from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QMessageBox

from serial.tools import list_ports

from reader.reader_manager import normalize_connection_type
from reader.uhf_reader import UHFReader
from services.settings_service import save_settings


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


def show_settings(parent_window, reader, settings, timer, log_func):
    """
    設定ダイアログを表示する。
    保存時は settings dict を直接更新し、timer のインターバルも更新する。
    保存された場合は (lost_timeout_sec, auto_bookmaster_path) を返す。
    キャンセルされた場合は None を返す。
    """
    ui_file = QFile("ui/settings_dialog.ui")
    ui_file.open(QFile.ReadOnly)

    loader = QUiLoader()
    dialog = loader.load(ui_file, parent_window)
    ui_file.close()

    connection_type = settings.get("connection_type", "USB")
    if normalize_connection_type(connection_type) == "UART":
        connection_type = "232C(UART)"
    dialog.comboConnectionType.setCurrentText(connection_type)
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
        connection_type = normalize_connection_type(
            dialog.comboConnectionType.currentText()
        )

        is_lan = connection_type == "LAN"
        is_serial = connection_type in ("USB", "UART")

        dialog.linePort.setEnabled(is_serial)
        dialog.comboBaudrate.setEnabled(is_serial)

        dialog.lineHost.setEnabled(is_lan)
        dialog.spinTcpPort.setEnabled(is_lan)

    dialog.comboConnectionType.currentTextChanged.connect(update_connection_fields)
    update_connection_fields()

    if hasattr(dialog, "labelReaderConnection"):
        connection_type = settings.get("connection_type", "USB")
        if normalize_connection_type(connection_type) == "UART":
            connection_type = "232C(UART)"
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
        connection_type = dialog.comboConnectionType.currentText()

        # LAN設定バリデーション
        if connection_type == "LAN":
            host_val = dialog.lineHost.text().strip()

            if not host_val:
                QMessageBox.warning(dialog, "入力エラー", "IPアドレスを入力してください。")
                return

        settings["connection_type"] = connection_type
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

        timer.setInterval(int(settings.get("read_interval_ms", 500)))

        log_func("設定を保存しました")
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

    accepted = dialog.exec()

    if accepted:
        return (
            int(settings.get("lost_timeout_sec", 10)),
            settings.get("bookmaster_path", "/home/ncc/ドキュメント/bookmaster.csv"),
        )

    return None
