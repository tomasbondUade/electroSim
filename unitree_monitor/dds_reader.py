"""
Hilo que se suscribe al tópico lowstate del robot vía DDS
y emite los datos de motores como señal Qt.
"""

import math
import time
import random
from PyQt6.QtCore import QThread, pyqtSignal
from unitree_monitor.joint_maps import get_joint_map, get_num_motors


class DDSReader(QThread):
    """Lee lowstate del robot en un hilo separado."""

    data_received = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    connected = pyqtSignal()

    def __init__(self, robot_type: str, interface: str, demo_mode: bool = False):
        super().__init__()
        self.robot_type = robot_type.lower()
        self.interface = interface
        self.demo_mode = demo_mode
        self._running = True

    def run(self):
        if self.demo_mode:
            self._run_demo()
            return

        try:
            from unitree_sdk2py.core.channel import (
                ChannelSubscriber,
                ChannelFactoryInitialize,
            )

            ChannelFactoryInitialize(0, self.interface)

            joint_map = get_joint_map(self.robot_type)
            num_motors = get_num_motors(self.robot_type)

            if self.robot_type == "go2":
                from unitree_sdk2py.idl.unitree_go.msg.dds_ import (
                    LowState_ as LowState,
                )
            else:
                from unitree_sdk2py.idl.unitree_hg.msg.dds_ import (
                    LowState_ as LowState,
                )

            self.connected.emit()

            self._last_emit = 0

            def handler(msg):
                if not self._running:
                    return

                now = time.time()
                if now - self._last_emit < 0.1:
                    return
                self._last_emit = now

                motors = []
                for idx in range(num_motors):
                    ms = msg.motor_state[idx]

                    q = ms.q if not callable(ms.q) else ms.q()
                    dq = ms.dq if not callable(ms.dq) else ms.dq()
                    ddq = ms.ddq if not callable(ms.ddq) else ms.ddq()
                    tau = ms.tau_est if not callable(ms.tau_est) else ms.tau_est()
                    temp = ms.temperature if not callable(ms.temperature) else ms.temperature()

                    info = joint_map.get(idx, {
                        "name": f"Motor_{idx}",
                        "group": "Otro",
                    })

                    motors.append({
                        "index": idx,
                        "name": info["name"],
                        "group": info["group"],
                        "q_rad": round(float(q), 4),
                        "q_deg": round(math.degrees(float(q)), 2),
                        "dq": round(float(dq), 4),
                        "ddq": round(float(ddq), 4),
                        "tau_est": round(float(tau), 4),
                        "temperature": int(temp) if isinstance(temp, (int, float)) else 0,
                    })

                # Energía
                try:
                    pv = msg.power_v
                    power_v = float(pv() if callable(pv) else pv)
                except Exception:
                    power_v = 0.0
                try:
                    pa = msg.power_a
                    power_a = float(pa() if callable(pa) else pa)
                except Exception:
                    power_a = 0.0

                # IMU
                imu_data = {}
                try:
                    imu = msg.imu_state if not callable(msg.imu_state) else msg.imu_state()

                    quat = imu.quaternion if not callable(imu.quaternion) else imu.quaternion()
                    gyro = imu.gyroscope if not callable(imu.gyroscope) else imu.gyroscope()
                    accel = imu.accelerometer if not callable(imu.accelerometer) else imu.accelerometer()
                    rpy = imu.rpy if not callable(imu.rpy) else imu.rpy()

                    imu_data = {
                        "quaternion": [round(float(quat[i]), 4) for i in range(4)],
                        "gyroscope": [round(float(gyro[i]), 4) for i in range(3)],
                        "accelerometer": [round(float(accel[i]), 4) for i in range(3)],
                        "rpy_deg": [round(math.degrees(float(rpy[i])), 2) for i in range(3)],
                    }
                except Exception:
                    imu_data = {
                        "quaternion": [0, 0, 0, 0],
                        "gyroscope": [0, 0, 0],
                        "accelerometer": [0, 0, 0],
                        "rpy_deg": [0, 0, 0],
                    }

                # Fuerza en patas
                foot_force = [0, 0, 0, 0]
                try:
                    ff = msg.foot_force if not callable(msg.foot_force) else msg.foot_force()
                    foot_force = [int(ff[i]) for i in range(4)]
                except Exception:
                    pass

                # Batería (BMS)
                bms_data = {}
                try:
                    bms = msg.bms_state
                    bms_data = {
                        "soc": int(bms.soc),
                        "cycle": int(bms.cycle),
                        "current": int(bms.current),
                        "status": int(bms.status),
                        "mcu_ntc": list(bms.mcu_ntc),
                        "bq_ntc": list(bms.bq_ntc),
                        "cell_vol": list(bms.cell_vol),
                    }
                except Exception:
                    bms_data = {
                        "soc": 0, "cycle": 0, "current": 0,
                        "status": 0, "mcu_ntc": [], "bq_ntc": [],
                        "cell_vol": [],
                    }

                packet = {
                    "robot": self.robot_type.upper(),
                    "timestamp": time.time(),
                    "power_v": round(power_v, 2),
                    "power_a": round(power_a, 2),
                    "motors": motors,
                    "imu": imu_data,
                    "foot_force": foot_force,
                    "bms": bms_data,
                }

                self.data_received.emit(packet)

            sub = ChannelSubscriber("rt/lowstate", LowState)
            sub.Init(handler, 10)

            while self._running:
                time.sleep(0.1)

        except Exception as e:
            error_msg = str(e)
            if "does not match" in error_msg or "domain" in error_msg.lower():
                self.error_occurred.emit(
                    f"No se pudo conectar por la interfaz '{self.interface}'.\n\n"
                    f"Posibles causas:\n"
                    f"- El robot no está conectado a esta PC\n"
                    f"- La interfaz de red seleccionada no es la correcta\n"
                    f"- El cable Ethernet no está bien conectado\n\n"
                    f"Verificá la conexión y probá con otra interfaz."
                )
            else:
                self.error_occurred.emit(f"Error inesperado:\n{error_msg}")

    def _run_demo(self):
        """Genera datos simulados para probar la app sin robot."""
        self.connected.emit()
        joint_map = get_joint_map(self.robot_type)
        num_motors = get_num_motors(self.robot_type)

        base_angles = {}
        for idx in range(num_motors):
            base_angles[idx] = random.uniform(-90, 90)

        t = 0
        while self._running:
            t += 0.1
            motors = []
            for idx in range(num_motors):
                info = joint_map.get(idx, {"name": f"Motor_{idx}", "group": "Otro"})
                angle = base_angles[idx] + 5 * math.sin(t + idx * 0.5)
                motors.append({
                    "index": idx,
                    "name": info["name"],
                    "group": info["group"],
                    "q_rad": round(math.radians(angle), 4),
                    "q_deg": round(angle, 2),
                    "dq": round(0.5 * math.cos(t + idx * 0.3), 4),
                    "ddq": 0.0,
                    "tau_est": round(random.uniform(-10, 10), 4),
                    "temperature": random.randint(28, 45),
                })

            packet = {
                "robot": self.robot_type.upper(),
                "timestamp": time.time(),
                "power_v": round(27.5 + random.uniform(-0.5, 0.5), 2),
                "power_a": round(3.0 + random.uniform(-0.5, 0.5), 2),
                "motors": motors,
                "imu": {
                    "quaternion": [1, 0, 0, 0],
                    "gyroscope": [round(random.uniform(-0.01, 0.01), 4) for _ in range(3)],
                    "accelerometer": [round(random.uniform(-0.5, 0.5), 4), round(random.uniform(-0.5, 0.5), 4), round(9.8 + random.uniform(-0.1, 0.1), 4)],
                    "rpy_deg": [round(random.uniform(-5, 5), 2), round(random.uniform(-5, 5), 2), round(random.uniform(-180, 180), 2)],
                },
                "foot_force": [random.randint(10, 60) for _ in range(4)],
                "bms": {
                    "soc": 75, "cycle": 20, "current": -3500,
                    "status": 0, "mcu_ntc": [30, 31], "bq_ntc": [29, 30],
                    "cell_vol": [3520, 3518, 3525, 3530, 3522, 3519],
                },
            }

            self.data_received.emit(packet)
            time.sleep(0.1)

    def stop(self):
        self._running = False
        self.quit()
        self.wait(3000)