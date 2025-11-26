# GUÍA COMPLETA - Raspberry Pi 5 (Linux) con Thonny
## Todo desde un solo dispositivo: RPi5

---

## 🖥️ ARQUITECTURA REAL DE TU SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│              RASPBERRY PI 5 (Linux con pantalla)            │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  THONNY IDE                                        │   │
│  │  - Editor Python                                   │   │
│  │  - Ejecuta scripts                                 │   │
│  │  - Programa Pico W (opcional)                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  ARDUINO IDE (Linux)                               │   │
│  │  - Carga sketches en Arduino                       │   │
│  │  - Monitor serial                                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  MOSQUITTO (Docker)                                │   │
│  │  - Broker MQTT localhost:1883                      │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  CÁMARA USB (conectada al RPi5)                    │   │
│  │  - Detección YOLO                                  │   │
│  │  - Publica a MQTT local                            │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
└──────────────┬────────────────────────┬───────────────────┘
               │                        │
               │ USB                    │ USB
               ▼                        ▼
       ┌───────────────┐      ┌─────────────────┐
       │  ARDUINO UNO  │      │  PICO W (opc.)  │
       │  - Servo Pin 9│      │  - Solo si usas │
       └───────┬───────┘      │    Solución 1   │
               │              └─────────────────┘
               ▼
        ┌─────────────┐
        │ SERVOMOTOR  │
        │  MG946R     │
        └─────────────┘
```

---

## 🎯 DOS SOLUCIONES DISPONIBLES

### ✅ SOLUCIÓN SIMPLE (RECOMENDADA para empezar)

**Un solo script en Thonny:**

```
control_servo_directo.py
```

**Hace todo:**
- ✅ Captura cámara USB del RPi5
- ✅ Detecta pistachos con YOLO
- ✅ Escucha MQTT local (localhost)
- ✅ Controla Arduino directamente por USB
- ✅ Mueve servomotor según detección

**NO necesitas:**
- ❌ Pico W
- ❌ Level Converter
- ❌ Ejecutar en laptop aparte

---

### ⚙️ SOLUCIÓN CON PICO W (Avanzada)

Si prefieres usar la Pico W como intermediario inalámbrico.

---

## 📋 INSTALACIÓN EN RASPBERRY PI 5

### PASO 1: Abrir Terminal en RPi5

```bash
# Presiona Ctrl+Alt+T o abre desde menú
```

---

### PASO 2: Instalar dependencias

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python y librerías
sudo apt install -y python3-pip python3-opencv

# Instalar paquetes Python
pip3 install pyserial paho-mqtt ultralytics opencv-python

# Verificar instalación
python3 -c "import cv2, serial, paho.mqtt.client; print('✓ Todo instalado')"
```

---

### PASO 3: Instalar Thonny (si no está)

```bash
# Thonny suele venir preinstalado en Raspberry Pi OS
# Si no está:
sudo apt install -y thonny

# Abrir Thonny
thonny &
```

---

### PASO 4: Instalar Arduino IDE (si no está)

**Opción A - Desde repositorios:**
```bash
sudo apt install -y arduino
```

**Opción B - Última versión:**
```bash
# Descargar desde: https://www.arduino.cc/en/software
# Versión Linux ARM 64-bit para RPi5

# Extraer y ejecutar
tar -xf arduino-*.tar.xz
cd arduino-*/
sudo ./install.sh
```

---

### PASO 5: Configurar permisos para Arduino

```bash
# Agregar usuario a grupos necesarios
sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# Aplicar cambios (elegir una opción):
# Opción 1: Reiniciar sesión (cerrar y volver a entrar)
# Opción 2: Ejecutar
newgrp dialout

# Verificar
groups | grep dialout
# Debe aparecer "dialout"
```

---

### PASO 6: Configurar Mosquitto (broker MQTT)

```bash
# Si ya lo instalaste con Docker, verificar:
sudo docker ps | grep mosquitto

# Si está corriendo, ¡listo!

# Si no está, iniciarlo:
sudo docker start mosquitto

# Si no tienes Docker instalado, instalar Mosquitto directo:
sudo apt install -y mosquitto mosquitto-clients

# Iniciar servicio
sudo systemctl start mosquitto
sudo systemctl enable mosquitto

# Verificar
sudo systemctl status mosquitto
# Debe decir "active (running)"
```

---

## 🔧 CONFIGURACIÓN EN THONNY

### Abrir proyecto en Thonny

1. **Abrir Thonny** (desde menú o terminal: `thonny`)

2. **Abrir carpeta del proyecto:**
   - File → Open...
   - Navegar a: `/home/tu-usuario/robotica-pico-rpi5-main/`

3. **Configurar intérprete:**
   - Run → Select interpreter...
   - Elegir: **"The same interpreter which runs Thonny"** (Python 3)
   - Click OK

---

## 🚀 USAR SOLUCIÓN SIMPLE EN THONNY

### PASO 1: Cargar código en Arduino

**Desde Arduino IDE en RPi5:**

1. Abrir Arduino IDE
2. File → Open → `arduino/servo_control_simple.ino`
3. Tools → Board → Arduino Uno
4. Tools → Port → `/dev/ttyUSB0` (o el que aparezca)
5. Click en botón **Upload** (→)
6. Esperar: "Done uploading"
7. **IMPORTANTE: Cerrar Arduino IDE** (para liberar puerto USB)

**Verificar:**
- LED del Arduino parpadea 3 veces al terminar upload
- Monitor Serial mostraría `ARDUINO_READY`

---

### PASO 2: Abrir script en Thonny

1. En Thonny: File → Open
2. Navegar a: `rpi5/control_servo_directo.py`
3. Click en Open

---

### PASO 3: Modificar configuración del puerto serial

En Thonny, buscar esta línea al inicio del archivo:

```python
SERIAL_PORT = "/dev/ttyUSB0"  # ← Cambiar si es necesario
```

**Para verificar el puerto correcto:**

Abrir Terminal y ejecutar:
```bash
ls -l /dev/ttyUSB* /dev/ttyACM*
```

Si aparece `/dev/ttyACM0` en lugar de `/dev/ttyUSB0`, cambiar la línea a:
```python
SERIAL_PORT = "/dev/ttyACM0"
```

---

### PASO 4: Conectar cámara USB

1. Conectar cámara USB al Raspberry Pi 5
2. Verificar que se detecta:
   ```bash
   ls /dev/video*
   # Debe aparecer /dev/video0 o similar
   ```

---

### PASO 5: Verificar que tienes el modelo YOLO

Asegúrate de que el archivo `best.pt` esté en la carpeta `rpi5/`:

```bash
ls -lh rpi5/best.pt
```

Si no está, descárgalo desde tu Google Drive (según el README original).

---

### PASO 6: Ejecutar el sistema desde Thonny

**EN THONNY:**

1. Asegúrate de que `control_servo_directo.py` está abierto
2. Click en el botón **Run** (▶️ verde) o presiona **F5**

**Deberías ver en la consola de Thonny:**

```
============================================================
Control Directo Servo - RPi5 → Arduino
Broker MQTT: localhost:1883
Arduino: /dev/ttyUSB0 @ 9600
Umbral confianza: 60%
Timeout sin detección: 5.0s
============================================================
Conectando a Arduino en /dev/ttyUSB0...
Arduino dice: ARDUINO_READY
✓ Conexión Arduino establecida
Conectando a broker MQTT...
✓ Conectado al broker MQTT en localhost:1883
✓ Suscrito al topic: robot/pico/estado

🚀 Sistema iniciado. Presiona Ctrl+C para salir.

Posicionando servo en estado inicial (0°)...
```

---

### PASO 7: Observar funcionamiento

**Cuando la cámara detecta un pistacho:**

```
📡 Detección: pistachio (85%)
🎯 PISTACHO VÁLIDO (85%) - Activando servo
🥜 PISTACHO DETECTADO → Moviendo servo a 180°
✓ Arduino completó secuencia ACTIVATE (180°)
```

**Servo se mueve a 180° (derecha)**

---

**Cuando pasan 5 segundos sin detección:**

```
⏱ 5.0s sin detección - Reseteando servo
⏸ SIN DETECCIÓN → Moviendo servo a 0°
✓ Arduino completó RESET (0°)
```

**Servo se mueve a 0° (izquierda)**

---

### PASO 8: Detener el sistema

En Thonny:
- Click en botón **Stop** (cuadrado rojo)
- O presiona **Ctrl+C** en la consola

El script hará limpieza automática:
```
Cerrando conexiones...
Reseteando servo a posición inicial...
✓ Arduino desconectado
✓ MQTT desconectado
Sistema detenido correctamente
```

---

## 🔍 DEBUGGING EN THONNY

### Ver logs detallados

Cambiar esta línea en `control_servo_directo.py`:

```python
# De:
logging.basicConfig(
    level=logging.INFO,
    ...
)

# A:
logging.basicConfig(
    level=logging.DEBUG,  # ← Cambiar a DEBUG
    ...
)
```

Ahora verás todos los comandos seriales enviados/recibidos.

---

### Probar Arduino manualmente desde Thonny

**Crear nuevo archivo en Thonny:**

```python
import serial
import time

# Conectar a Arduino
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=2)
time.sleep(2)  # Esperar reset Arduino

# Limpiar buffer
if ser.in_waiting:
    print("Arduino dice:", ser.read(ser.in_waiting).decode())

# Enviar comando A (mover a 180°)
print("Enviando comando A...")
ser.write(b'A')
time.sleep(1)

# Leer respuesta
if ser.in_waiting:
    print("Respuesta:", ser.read(ser.in_waiting).decode())

# Esperar movimiento
time.sleep(2)

# Enviar comando R (mover a 0°)
print("Enviando comando R...")
ser.write(b'R')
time.sleep(1)

if ser.in_waiting:
    print("Respuesta:", ser.read(ser.in_waiting).decode())

ser.close()
print("Listo!")
```

Ejecutar con F5. El servo debe moverse.

---

## 📊 CONFIGURAR PARÁMETROS

### En `control_servo_directo.py` (líneas 20-30):

```python
# Umbral de confianza (60% por defecto)
CONFIDENCE_THRESHOLD = 0.6  # Cambiar a 0.5 para 50%, etc.

# Tiempo sin detección antes de resetear
NO_DETECTION_TIMEOUT = 5.0  # Cambiar a 3.0 para 3 segundos

# Cooldown entre movimientos (evita mover muy seguido)
MOVEMENT_COOLDOWN = 5.0  # Cambiar a 2.0 para 2 segundos
```

**Guardar cambios:** Ctrl+S

---

### En `servo_control_simple.ino` (líneas 18-19):

```cpp
// Posiciones del servo
const int POS_IZQUIERDA = 0;      // Sin detección
const int POS_DERECHA = 180;      // Pistacho detectado

// Puedes cambiar, por ejemplo:
const int POS_IZQUIERDA = 45;     // 45 grados
const int POS_DERECHA = 135;      // 135 grados
```

**Recargar en Arduino:** Upload desde Arduino IDE

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Problema: "Permission denied" en /dev/ttyUSB0

**En Terminal:**
```bash
# Agregar usuario a dialout
sudo usermod -a -G dialout $USER

# Aplicar cambios
newgrp dialout

# Verificar
groups | grep dialout
```

**Si sigue sin funcionar:**
```bash
# Temporal (solo para probar):
sudo chmod 666 /dev/ttyUSB0
```

---

### Problema: No encuentra el puerto /dev/ttyUSB0

**En Terminal:**
```bash
# Listar puertos disponibles
ls -l /dev/ttyUSB* /dev/ttyACM*

# Ejemplo salida:
# crw-rw---- 1 root dialout ... /dev/ttyACM0
```

**Cambiar en el script:**
```python
SERIAL_PORT = "/dev/ttyACM0"  # ← Usar el que aparezca
```

---

### Problema: "ModuleNotFoundError: No module named 'serial'"

**En Terminal:**
```bash
pip3 install pyserial
```

Si sigue sin funcionar:
```bash
# Instalar específicamente para Python3
sudo apt install python3-serial
```

---

### Problema: Cámara no detecta (`/dev/video0` no existe)

**Verificar cámara:**
```bash
# Ver dispositivos video
ls -l /dev/video*

# Ver info de cámara
v4l2-ctl --list-devices
```

**Si no aparece:**
- Desconectar y reconectar cámara USB
- Probar otro puerto USB
- Verificar que la cámara funciona: `cheese` (aplicación de cámara)

---

### Problema: MQTT no conecta

**Verificar broker:**
```bash
# Si usas Docker:
sudo docker ps | grep mosquitto

# Si usas servicio:
sudo systemctl status mosquitto

# Debe decir "active (running)"
```

**Reiniciar broker:**
```bash
# Docker:
sudo docker restart mosquitto

# Servicio:
sudo systemctl restart mosquitto
```

**Probar manualmente:**
```bash
# Terminal 1:
mosquitto_sub -h localhost -t robot/pico/estado -v

# Terminal 2:
mosquitto_pub -h localhost -t robot/pico/estado -m 'test'

# Terminal 1 debe mostrar: robot/pico/estado test
```

---

## 📂 ESTRUCTURA DE ARCHIVOS EN THONNY

Tu proyecto debería verse así:

```
robotica-pico-rpi5-main/
├── arduino/
│   ├── servo_control.ino              (original)
│   ├── servo_control_mejorado.ino     (con watchdog)
│   └── servo_control_simple.ino       (USAR ESTE) ⭐
├── rpi5/
│   ├── best.pt                        (modelo YOLO)
│   ├── videoPublicTopic.py            (original)
│   ├── videoPublicTopic_mejorado.py   (mejorado)
│   └── control_servo_directo.py       (USAR ESTE) ⭐
├── SOLUCION_SIMPLE.md                  (esta guía)
└── README.md                           (documentación completa)
```

---

## ✅ CHECKLIST ANTES DE EJECUTAR

### Hardware:
- [ ] Arduino Uno conectado a RPi5 por USB
- [ ] Servomotor con fuente externa 5V (2-3A)
- [ ] GND común: Arduino + Fuente + Servo
- [ ] Cable amarillo servo → Arduino Pin 9
- [ ] Cámara USB conectada a RPi5

### Software:
- [ ] Arduino programado con `servo_control_simple.ino`
- [ ] Arduino IDE cerrado (para liberar puerto)
- [ ] Usuario en grupo dialout: `groups | grep dialout`
- [ ] Mosquitto corriendo: `sudo docker ps` o `systemctl status mosquitto`
- [ ] Archivo `best.pt` en carpeta `rpi5/`
- [ ] Paquetes Python instalados: `pip3 list | grep -E "pyserial|paho-mqtt|ultralytics"`

### Thonny:
- [ ] Archivo `control_servo_directo.py` abierto
- [ ] Puerto serial configurado correctamente (línea SERIAL_PORT)
- [ ] Intérprete Python 3 seleccionado

---

## 🎯 RESUMEN - FLUJO COMPLETO

**TODO EN EL RASPBERRY PI 5:**

1. **Arduino IDE** → Cargar `servo_control_simple.ino` → Cerrar IDE

2. **Thonny** → Abrir `control_servo_directo.py` → Run (F5)

3. **Sistema funciona:**
   - Cámara USB detecta pistachos
   - Python publica a MQTT local
   - Python escucha MQTT
   - Python envía comando a Arduino por USB
   - Arduino mueve servomotor
   - Si no detecta por 5s → Reset automático

4. **Detener:** Stop en Thonny o Ctrl+C

---

## 💡 TIPS

### Ejecutar en segundo plano

Si quieres que el script siga corriendo mientras haces otras cosas:

**Terminal:**
```bash
cd rpi5
python3 control_servo_directo.py &

# Ver proceso:
ps aux | grep control_servo

# Detener:
pkill -f control_servo_directo
```

---

### Ver logs en tiempo real

```bash
tail -f rpi5/deteccion_pistachos.log
```

(Si el script está configurado para guardar logs)

---

### Probar solo la cámara

```python
# Crear archivo test_camara.py en Thonny:
import cv2

cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✓ Cámara OK")
    ret, frame = cap.read()
    if ret:
        print(f"✓ Captura OK - Tamaño: {frame.shape}")
    else:
        print("✗ No se pudo leer frame")
else:
    print("✗ No se pudo abrir cámara")
    
cap.release()
```

---

**¡Listo para usar todo desde Thonny en Raspberry Pi 5!** 🚀
