"""
Interfaz gráfica principal — Monitor de motores Unitree.
"""

import csv
import subprocess
import platform
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QGroupBox, QStatusBar,
    QGridLayout, QFrame,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor
from unitree_monitor.dds_reader import DDSReader
from unitree_monitor.joint_maps import get_joint_map, get_num_motors


class SensorLabel(QLabel):
    """Label con estilo para mostrar un valor de sensor."""
    def __init__(self, title, unit=""):
        super().__init__()
        self.title = title
        self.unit = unit
        self.set_value("—")

    def set_value(self, value):
        self.setText(f"{self.title}: {value} {self.unit}")


class MotorMonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unitree Motor Monitor — Go2 / G1 EDU")
        self.setMinimumSize(1100, 800)

        self.reader = None
        self.latest_data = None
        self.history = []

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ── Barra de conexión ──
        conn_group = QGroupBox("Conexión")
        conn_layout = QHBoxLayout(conn_group)

        conn_layout.addWidget(QLabel("Robot:"))
        self.combo_robot = QComboBox()
        self.combo_robot.addItems(["Go2", "G1"])
        conn_layout.addWidget(self.combo_robot)

        conn_layout.addWidget(QLabel("Interfaz de red:"))
        self.combo_iface = QComboBox()
        self.combo_iface.setMinimumWidth(200)
        self._populate_interfaces()
        conn_layout.addWidget(self.combo_iface)

        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.clicked.connect(self._populate_interfaces)
        conn_layout.addWidget(self.btn_refresh)

        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.clicked.connect(self._on_connect)
        conn_layout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Desconectar")
        self.btn_disconnect.clicked.connect(self._on_disconnect)
        self.btn_disconnect.setEnabled(False)
        conn_layout.addWidget(self.btn_disconnect)

        self.btn_demo = QPushButton("Modo Demo")
        self.btn_demo.clicked.connect(self._on_demo)
        conn_layout.addWidget(self.btn_demo)

        conn_layout.addStretch()
        layout.addWidget(conn_group)

        # ── Panel de sensores (energía + IMU + patas + batería) ──
        sensors_layout = QHBoxLayout()

        # Energía
        energy_group = QGroupBox("Energía")
        energy_grid = QGridLayout(energy_group)
        self.lbl_voltage = SensorLabel("Voltaje", "V")
        self.lbl_current = SensorLabel("Corriente", "A")
        self.lbl_power = SensorLabel("Potencia", "W")
        energy_grid.addWidget(self.lbl_voltage, 0, 0)
        energy_grid.addWidget(self.lbl_current, 1, 0)
        energy_grid.addWidget(self.lbl_power, 2, 0)
        sensors_layout.addWidget(energy_group)

        # Batería
        bms_group = QGroupBox("Batería")
        bms_grid = QGridLayout(bms_group)
        self.lbl_soc = SensorLabel("Carga", "%")
        self.lbl_bms_current = SensorLabel("Corriente BMS", "mA")
        self.lbl_bms_temp = SensorLabel("Temp NTC", "")
        self.lbl_bms_cycle = SensorLabel("Ciclos", "")
        self.lbl_bms_cells = SensorLabel("Celdas", "mV")
        bms_grid.addWidget(self.lbl_soc, 0, 0)
        bms_grid.addWidget(self.lbl_bms_current, 1, 0)
        bms_grid.addWidget(self.lbl_bms_temp, 2, 0)
        bms_grid.addWidget(self.lbl_bms_cycle, 3, 0)
        bms_grid.addWidget(self.lbl_bms_cells, 4, 0)
        sensors_layout.addWidget(bms_group)

        # IMU
        imu_group = QGroupBox("IMU — Orientación")
        imu_grid = QGridLayout(imu_group)
        self.lbl_roll = SensorLabel("Roll", "°")
        self.lbl_pitch = SensorLabel("Pitch", "°")
        self.lbl_yaw = SensorLabel("Yaw", "°")
        self.lbl_accel = SensorLabel("Aceleración", "m/s²")
        self.lbl_gyro = SensorLabel("Giroscopio", "rad/s")
        imu_grid.addWidget(self.lbl_roll, 0, 0)
        imu_grid.addWidget(self.lbl_pitch, 0, 1)
        imu_grid.addWidget(self.lbl_yaw, 0, 2)
        imu_grid.addWidget(self.lbl_accel, 1, 0, 1, 2)
        imu_grid.addWidget(self.lbl_gyro, 1, 2)
        sensors_layout.addWidget(imu_group)

        # Fuerza en patas
        foot_group = QGroupBox("Fuerza en patas")
        foot_grid = QGridLayout(foot_group)
        self.lbl_ff_fr = SensorLabel("FR", "")
        self.lbl_ff_fl = SensorLabel("FL", "")
        self.lbl_ff_rr = SensorLabel("RR", "")
        self.lbl_ff_rl = SensorLabel("RL", "")
        foot_grid.addWidget(self.lbl_ff_fr, 0, 0)
        foot_grid.addWidget(self.lbl_ff_fl, 0, 1)
        foot_grid.addWidget(self.lbl_ff_rr, 1, 0)
        foot_grid.addWidget(self.lbl_ff_rl, 1, 1)
        sensors_layout.addWidget(foot_group)

        layout.addLayout(sensors_layout)

        # ── Botones de captura (arriba de la tabla) ──
        capture_layout = QHBoxLayout()

        self.btn_snapshot = QPushButton("Capturar dato actual")
        self.btn_snapshot.clicked.connect(self._on_snapshot)
        self.btn_snapshot.setEnabled(False)
        capture_layout.addWidget(self.btn_snapshot)

        self.lbl_snapcount = QLabel("Capturas: 0")
        capture_layout.addWidget(self.lbl_snapcount)

        self.btn_export = QPushButton("Exportar CSV")
        self.btn_export.clicked.connect(self._on_export_csv)
        self.btn_export.setEnabled(False)
        capture_layout.addWidget(self.btn_export)

        capture_layout.addStretch()
        layout.addLayout(capture_layout)

        # ── Tabla de motores ──
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Grupo", "Motor", "Ángulo (°)",
            "Vel. (rad/s)", "Torque (N·m)",
            "Temp (°C)", "Índice"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, 7):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # ── Status bar ──
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Desconectado — Seleccioná el robot e interfaz de red")

    # ── Interfaces de red ──

    def _populate_interfaces(self):
        """Detecta interfaces de red activas y las muestra en el combo."""
        self.combo_iface.clear()
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["ipconfig"],
                    capture_output=True, text=True, timeout=5,
                )
                current_name = None
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line.endswith(":") and "adapter" in line.lower():
                        current_name = line.replace(":", "").strip()
                        # Limpiar prefijo "Ethernet adapter" / "Wireless LAN adapter"
                        for prefix in ["Ethernet adapter ", "Wireless LAN adapter ",
                                       "Adaptador de Ethernet ", "Adaptador de LAN inalámbrica "]:
                            if current_name.startswith(prefix):
                                current_name = current_name[len(prefix):]
                    elif current_name and ("IPv4" in line or "Dirección IPv4" in line):
                        self.combo_iface.addItem(current_name)
                        current_name = None
            else:
                result = subprocess.run(
                    ["ip", "-o", "link", "show"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.strip().split("\n"):
                    parts = line.split(": ")
                    if len(parts) >= 2:
                        name = parts[1].split("@")[0]
                        if name != "lo":
                            self.combo_iface.addItem(name)
        except Exception:
            self.combo_iface.addItem("eth0")

        if self.combo_iface.count() == 0:
            self.combo_iface.addItem("No se detectaron interfaces")

    # ── Conexión / Desconexión ──

    def _on_demo(self):
        """Inicia la app con datos simulados para probar sin robot."""
        robot = self.combo_robot.currentText().lower()
        self.status.showMessage(f"Modo demo — {robot.upper()} simulado")
        self.btn_connect.setEnabled(False)
        self.btn_demo.setEnabled(False)

        self._setup_table(robot)

        self.reader = DDSReader(robot, "", demo_mode=True)
        self.reader.data_received.connect(self._on_data)
        self.reader.error_occurred.connect(self._on_error)
        self.reader.connected.connect(self._on_connected)
        self.reader.start()

    def _on_connect(self):
        robot = self.combo_robot.currentText().lower()
        iface = self.combo_iface.currentText().strip()

        if not iface:
            QMessageBox.warning(self, "Error", "Seleccioná la interfaz de red")
            return

        self.status.showMessage(f"Conectando a {robot.upper()} por {iface}...")
        self.btn_connect.setEnabled(False)

        self._setup_table(robot)

        self.reader = DDSReader(robot, iface)
        self.reader.data_received.connect(self._on_data)
        self.reader.error_occurred.connect(self._on_error)
        self.reader.connected.connect(self._on_connected)
        self.reader.start()

    def _on_connected(self):
        self.status.showMessage("Conectado — Recibiendo datos...")
        self.btn_disconnect.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_snapshot.setEnabled(True)
        self.combo_robot.setEnabled(False)
        self.combo_iface.setEnabled(False)

    def _on_disconnect(self):
        if self.reader:
            self.reader.stop()
            self.reader = None

        self.btn_connect.setEnabled(True)
        self.btn_demo.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.btn_snapshot.setEnabled(False)
        self.combo_robot.setEnabled(True)
        self.combo_iface.setEnabled(True)
        self.status.showMessage("Desconectado")

    def _on_error(self, msg):
        self.btn_connect.setEnabled(True)
        self.btn_demo.setEnabled(True)
        self.status.showMessage(f"Error: {msg}")
        QMessageBox.critical(self, "Error de conexión", msg)

    # ── Tabla ──

    def _setup_table(self, robot_type):
        joint_map = get_joint_map(robot_type)
        num = get_num_motors(robot_type)
        self.table.setRowCount(num)

        for idx in range(num):
            info = joint_map.get(idx, {"name": f"Motor_{idx}", "group": "Otro"})
            self.table.setItem(idx, 0, QTableWidgetItem(info["group"]))
            self.table.setItem(idx, 1, QTableWidgetItem(info["name"]))
            for col in range(2, 6):
                self.table.setItem(idx, col, QTableWidgetItem("—"))
            self.table.setItem(idx, 6, QTableWidgetItem(str(idx)))

    def _on_data(self, packet):
        self.latest_data = packet

        # Energía
        v = packet["power_v"]
        a = packet["power_a"]
        self.lbl_voltage.set_value(f"{v:.1f}")
        self.lbl_current.set_value(f"{a:.2f}")
        self.lbl_power.set_value(f"{v * a:.1f}")

        # Batería
        bms = packet.get("bms", {})
        self.lbl_soc.set_value(bms.get("soc", "—"))
        self.lbl_bms_current.set_value(bms.get("current", "—"))
        self.lbl_bms_cycle.set_value(bms.get("cycle", "—"))
        ntc = bms.get("mcu_ntc", [])
        self.lbl_bms_temp.set_value(", ".join(str(t) for t in ntc) if ntc else "—")
        cells = bms.get("cell_vol", [])
        self.lbl_bms_cells.set_value(", ".join(str(c) for c in cells) if cells else "—")

        # IMU
        imu = packet.get("imu", {})
        rpy = imu.get("rpy_deg", [0, 0, 0])
        self.lbl_roll.set_value(f"{rpy[0]:.1f}")
        self.lbl_pitch.set_value(f"{rpy[1]:.1f}")
        self.lbl_yaw.set_value(f"{rpy[2]:.1f}")

        accel = imu.get("accelerometer", [0, 0, 0])
        self.lbl_accel.set_value(f"x:{accel[0]:.2f} y:{accel[1]:.2f} z:{accel[2]:.2f}")

        gyro = imu.get("gyroscope", [0, 0, 0])
        self.lbl_gyro.set_value(f"x:{gyro[0]:.3f} y:{gyro[1]:.3f} z:{gyro[2]:.3f}")

        # Fuerza en patas
        ff = packet.get("foot_force", [0, 0, 0, 0])
        self.lbl_ff_fr.set_value(ff[0])
        self.lbl_ff_fl.set_value(ff[1])
        self.lbl_ff_rr.set_value(ff[2])
        self.lbl_ff_rl.set_value(ff[3])

        # Tabla de motores
        for motor in packet["motors"]:
            row = motor["index"]
            self.table.item(row, 2).setText(f"{motor['q_deg']:.2f}")
            self.table.item(row, 3).setText(f"{motor['dq']:.4f}")
            self.table.item(row, 4).setText(f"{motor['tau_est']:.4f}")

            temp = motor["temperature"]
            temp_item = self.table.item(row, 5)
            temp_item.setText(str(temp))
            if temp >= 60:
                temp_item.setBackground(QColor(255, 100, 100))
            elif temp >= 40:
                temp_item.setBackground(QColor(255, 255, 100))
            else:
                temp_item.setBackground(QColor(100, 255, 100))

    # ── Exportar ──

    def _on_snapshot(self):
        if self.latest_data:
            self.history.append(self.latest_data)
            count = len(self.history)
            self.lbl_snapcount.setText(f"Capturas: {count}")
            self.status.showMessage(f"Captura #{count} guardada")

    def _on_export_csv(self):
        if not self.history:
            QMessageBox.information(
                self, "Sin datos",
                "Usá 'Capturar dato actual' para guardar mediciones antes de exportar."
            )
            return

        default_name = f"motores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar CSV", default_name, "CSV (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Captura", "Timestamp", "Robot",
                "Voltaje_V", "Corriente_A", "Potencia_W",
                "Bateria_%", "Bateria_Temp_C", "Bateria_Ciclos",
                "Roll_deg", "Pitch_deg", "Yaw_deg",
                "Acel_X", "Acel_Y", "Acel_Z",
                "Gyro_X", "Gyro_Y", "Gyro_Z",
                "Fuerza_FR", "Fuerza_FL", "Fuerza_RR", "Fuerza_RL",
                "Grupo", "Motor", "Indice",
                "Angulo_deg", "Vel_rad_s", "Acel_rad_s2",
                "Torque_Nm", "Temp_C"
            ])

            for i, snap in enumerate(self.history, 1):
                ts = datetime.fromtimestamp(snap["timestamp"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                imu = snap.get("imu", {})
                rpy = imu.get("rpy_deg", [0, 0, 0])
                accel = imu.get("accelerometer", [0, 0, 0])
                gyro = imu.get("gyroscope", [0, 0, 0])
                ff = snap.get("foot_force", [0, 0, 0, 0])
                bms = snap.get("bms", {})
                v = snap["power_v"]
                a = snap["power_a"]

                for m in snap["motors"]:
                    writer.writerow([
                        i, ts, snap["robot"],
                        v, a, round(v * a, 1),
                        bms.get("soc", 0), bms.get("current", 0), bms.get("cycle", 0),
                        rpy[0], rpy[1], rpy[2],
                        accel[0], accel[1], accel[2],
                        gyro[0], gyro[1], gyro[2],
                        ff[0], ff[1], ff[2], ff[3],
                        m["group"], m["name"], m["index"],
                        m["q_deg"], m["dq"], m["ddq"],
                        m["tau_est"], m["temperature"],
                    ])

        self.status.showMessage(f"CSV exportado: {path}")
        QMessageBox.information(self, "Exportado", f"Archivo guardado en:\n{path}")

    def closeEvent(self, event):
        self._on_disconnect()
        event.accept()