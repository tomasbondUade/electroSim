# Unitree Motor Monitor — Go2 / G1 EDU

App de escritorio para monitorear en tiempo real los motores de los robots Unitree Go2 y G1 (versión EDU).

## Datos que muestra
- **Motores**: ángulo, velocidad, torque, temperatura (por motor, agrupados por extremidad)
- **Energía**: voltaje, corriente, potencia
- **Batería**: carga %, corriente, temperatura NTC, ciclos, voltaje por celda
- **IMU**: roll, pitch, yaw, acelerómetro, giroscopio
- **Fuerza en patas**: fuerza de contacto por pata

## Instalación

### 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/electroSim.git
cd electroSim

### 2. Crear entorno virtual e instalar dependencias

python3 -m venv env
source env/bin/activate        # Linux/Mac
env\Scripts\activate           # Windows
pip install -r requirements.txt

### 3. Instalar el SDK de Unitree

git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
pip install -e unitree_sdk2_python

### 4. Ejecutar

python3 main.py

### 5. Generar ejecutable

pyinstaller --onefile --windowed --name "UnitreeMotorMonitor" --collect-all unitree_sdk2py --collect-all cyclonedds main.py

El ejecutable queda en `dist/`.

## Uso
1. Conectar la PC al robot (cable Ethernet o WiFi AP)
2. Abrir la app
3. Seleccionar el robot (Go2 o G1) y la interfaz de red
4. Conectar
5. Usar "Capturar dato actual" para guardar mediciones
6. Exportar a CSV cuando se necesite