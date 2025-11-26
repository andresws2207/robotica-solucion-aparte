# SOLUCIÓN SIMPLE - Control Directo Arduino
## Python (RPi5) → Arduino por USB → Servomotor

---

## 🎯 ARQUITECTURA SIMPLIFICADA

```
┌─────────────────────────────┐
│   LAPTOP/PC (Windows)       │
│   - Cámara + YOLO           │
│   - Publica a MQTT          │
└──────────┬──────────────────┘
           │
           │ WiFi/Ethernet
           │ MQTT
           ▼
┌─────────────────────────────┐
│   RASPBERRY PI 5 (Linux)    │
│   - Broker MQTT (Mosquitto) │
│   - Python escucha MQTT     │
│   - Controla Arduino USB    │
└──────────┬──────────────────┘
           │
           │ Cable USB
           ▼
┌─────────────────────────────┐
│   ARDUINO UNO               │
│   - Recibe comandos serial  │
│   - Mueve servomotor        │
└──────────┬──────────────────┘
           │
           │ Pin 9 (PWM)
           ▼
┌─────────────────────────────┐
│   SERVOMOTOR MG946R         │
│   - 0° = Sin detección      │
│   - 180° = Pistacho         │
└─────────────────────────────┘
```

**✅ VENTAJAS:**
- No necesita Pico W
- No necesita Level Converter
- Conexión directa USB
- Más fácil de debuggear
- Menos componentes = menos puntos de fallo

---

## 🔌 CONEXIONES FÍSICAS

### 1. Raspberry Pi 5 ↔ Arduino

```
RPi5 Puerto USB ──[Cable USB A-B]──> Arduino Puerto USB
```

**Esto proporciona:**
- ✅ Alimentación al Arduino (5V desde USB)
- ✅ Comunicación serial bidireccional
- ✅ Programación del Arduino

---

### 2. Arduino ↔ Servomotor

**IMPORTANTE: Servo debe tener alimentación externa**

```
FUENTE EXTERNA 5V (2-3A)
    (+) ───┬──> Servo Cable ROJO (VCC)
           │
    (-) ───┼──> Servo Cable MARRÓN (GND)
           │
           └──> Arduino GND ← CRÍTICO: GND COMÚN

Arduino Pin 9 ──> Servo Cable AMARILLO (Señal PWM)
```

**Conexión detallada:**

| Componente | Pin/Cable | Destino | Color Cable |
|------------|-----------|---------|-------------|
| **Fuente 5V** | (+) | Servo VCC | Rojo |
| **Fuente 5V** | (-) | Servo GND + Arduino GND | Negro/Marrón |
| **Arduino** | Pin 9 | Servo Señal | Amarillo/Naranja |
| **Arduino** | GND | Fuente (-) | Negro |

---

### 3. Diagrama Visual

```
RASPBERRY PI 5
     │
     │ USB
     ▼
ARDUINO UNO
     │
     ├─── Pin 9 (PWM) ────────────────┐
     │                                │
     └─── GND ─────┐                  │
                   │                  │
FUENTE 5V          │                  │
  (+) ─────────────┼──────────────────┤
                   │                  │
  (-) ─────────────┴──────────────────┤
                                      │
                               SERVOMOTOR MG946R
                                  🔴 Rojo (VCC)
                                  🟤 Marrón (GND)
                                  🟡 Amarillo (PWM)
```

---

## 📦 ARCHIVOS A USAR

### En Arduino:
```
arduino/servo_control_simple.ino
```

**Características:**
- Sin watchdog (más simple)
- Comandos: 'A' (180°), 'R' (0°), 'S' (status)
- LED parpadea al mover

### En RPi5:
```
rpi5/control_servo_directo.py
```

**Características:**
- Escucha MQTT
- Controla Arduino por USB
- Umbral 0.6 (60%)
- Timeout 5s sin detección → Reset a 0°

---

## 🚀 INSTALACIÓN Y USO

### PASO 1: Preparar RPi5

```bash
# 1. Verificar que Mosquitto esté corriendo
sudo docker ps | grep mosquitto

# Si no está, iniciarlo
sudo docker start mosquitto

# 2. Instalar pyserial (si no está)
pip3 install pyserial

# 3. Agregar usuario a grupo dialout (si no está)
sudo usermod -a -G dialout $USER
newgrp dialout  # O reiniciar sesión
```

---

### PASO 2: Cargar código en Arduino

**Opción A - Arduino IDE en RPi5:**

1. Abrir Arduino IDE
2. Abrir `arduino/servo_control_simple.ino`
3. Tools → Board → Arduino Uno
4. Tools → Port → `/dev/ttyUSB0` (o `/dev/ttyACM0`)
5. Click en **Upload**
6. Esperar mensaje: "Done uploading"
7. **Cerrar Arduino IDE** (importante para liberar puerto)

**Opción B - arduino-cli en RPi5:**

```bash
cd arduino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno servo_control_simple.ino
```

**Verificar:**
- LED del Arduino parpadea 3 veces al iniciar
- En monitor serial (si lo abres): `ARDUINO_READY`

---

### PASO 3: Configurar Laptop (Cámara)

En el archivo de cámara de tu laptop, asegúrate de que apunte al RPi5:

```python
# videoPublicTopic_mejorado.py (o el que uses)
BROKER = "192.168.X.XXX"  # ← IP del RPi5 (usar hostname -I en RPi5)
PORT = 1883
TOPIC = "robot/pico/estado"
```

---

### PASO 4: Ejecutar Sistema

#### En RPi5:

**Terminal 1 - Control del servo:**
```bash
cd rpi5
python3 control_servo_directo.py
```

**Deberías ver:**
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
⏸ SIN DETECCIÓN → Moviendo servo a 0°
✓ Arduino completó RESET (0°)
```

#### En Laptop:

```bash
cd rpi5  # (o donde tengas tu código de cámara)
python videoPublicTopic_mejorado.py
```

---

### PASO 5: Funcionamiento

**Cuando detecta pistacho:**
```
[LAPTOP] 
  📸 Cámara detecta pistacho (confianza: 0.85)
  📤 Publica MQTT: {"objeto":"pistachio", "confianza":0.85}

[RPi5]
  📡 Detección: pistachio (85%)
  🎯 PISTACHO VÁLIDO (85%) - Activando servo
  🥜 PISTACHO DETECTADO → Moviendo servo a 180°
  ✓ Arduino completó secuencia ACTIVATE (180°)

[ARDUINO]
  CMD_RX: A
  MOVER_DERECHA_START
  POS_ACTUAL: 0
  POS_DESTINO: 180
  MOVER_DERECHA_DONE

[SERVO]
  🔄 Se mueve a 180° (derecha)
```

**Cuando NO detecta por 5 segundos:**
```
[RPi5]
  ⏱ 5.0s sin detección - Reseteando servo
  ⏸ SIN DETECCIÓN → Moviendo servo a 0°
  ✓ Arduino completó RESET (0°)

[ARDUINO]
  CMD_RX: R
  MOVER_IZQUIERDA_START
  POS_ACTUAL: 180
  POS_DESTINO: 0
  MOVER_IZQUIERDA_DONE

[SERVO]
  🔄 Se mueve a 0° (izquierda)
```

---

## 🔧 SOLUCIÓN DE PROBLEMAS

### Problema: "Permission denied" en /dev/ttyUSB0

```bash
# Verificar puerto
ls -l /dev/ttyUSB0

# Debe mostrar: crw-rw---- 1 root dialout ...
#                               ^^^^^^^ 
#                         Debes estar en este grupo

# Solución:
sudo usermod -a -G dialout $USER
newgrp dialout

# Verificar:
groups | grep dialout
```

---

### Problema: No encuentra puerto /dev/ttyUSB0

```bash
# Listar puertos disponibles:
ls -l /dev/ttyUSB* /dev/ttyACM*

# Si aparece /dev/ttyACM0 en lugar de /dev/ttyUSB0:
# Editar control_servo_directo.py:
SERIAL_PORT = "/dev/ttyACM0"  # Cambiar esta línea
```

---

### Problema: Arduino no responde

```bash
# Test manual con minicom:
minicom -D /dev/ttyUSB0 -b 9600

# Dentro de minicom:
# - Presionar 'A' → Servo debe moverse a 180°
# - Presionar 'R' → Servo debe moverse a 0°
# - Presionar 'S' → Debe responder con STATUS

# Salir: Ctrl+A, luego Q
```

---

### Problema: Servo vibra pero no gira

**Causas:**
1. ❌ Alimentado desde Arduino (insuficiente corriente)
2. ❌ Sin fuente externa
3. ❌ GND no común

**Solución:**
```
✅ Fuente externa 5V (2-3A) para servo
✅ GND común: Arduino + Fuente + Servo
✅ Servo VCC desde fuente (NO desde Arduino)
```

---

### Problema: MQTT no recibe mensajes

```bash
# Verificar broker:
sudo docker ps | grep mosquitto

# Debe aparecer como "Up"

# Si no está corriendo:
sudo docker start mosquitto

# Ver logs:
sudo docker logs mosquitto

# Test manual:
# Terminal 1:
mosquitto_sub -h localhost -t robot/pico/estado -v

# Terminal 2:
mosquitto_pub -h localhost -t robot/pico/estado -m '{"objeto":"pistachio","confianza":0.8}'

# Terminal 1 debe mostrar el mensaje
```

---

## 📊 CONFIGURACIÓN

### Ajustar tiempos en `control_servo_directo.py`:

```python
# Umbral de detección (60% por defecto)
CONFIDENCE_THRESHOLD = 0.6

# Tiempo sin detección antes de resetear (5 segundos)
NO_DETECTION_TIMEOUT = 5.0

# Cooldown entre movimientos (5 segundos)
MOVEMENT_COOLDOWN = 5.0
```

### Ajustar posiciones en `servo_control_simple.ino`:

```cpp
// Posiciones del servo
const int POS_IZQUIERDA = 0;      // Sin detección
const int POS_DERECHA = 180;      // Pistacho detectado

// Puedes cambiar a:
const int POS_IZQUIERDA = 45;     // Por ejemplo
const int POS_DERECHA = 135;
```

---

## ✅ CHECKLIST ANTES DE EJECUTAR

Hardware:
- [ ] Arduino conectado a RPi5 por USB
- [ ] Servo alimentado por fuente externa 5V (2-3A)
- [ ] GND común: Arduino + Fuente + Servo
- [ ] Cable amarillo servo → Arduino Pin 9

Software RPi5:
- [ ] Mosquitto corriendo: `sudo docker ps | grep mosquitto`
- [ ] Usuario en grupo dialout: `groups | grep dialout`
- [ ] Arduino programado con `servo_control_simple.ino`
- [ ] Arduino IDE cerrado (liberar puerto)
- [ ] pyserial instalado: `pip3 list | grep pyserial`

Software Laptop:
- [ ] Script de cámara con IP correcta del RPi5
- [ ] Laptop y RPi5 en la misma red

---

## 🎯 COMANDOS RÁPIDOS

```bash
# Ejecutar sistema en RPi5
cd rpi5
python3 control_servo_directo.py

# Detener: Ctrl+C

# Ver logs de MQTT
sudo docker logs mosquitto

# Test manual servo
echo "A" > /dev/ttyUSB0  # Mover a 180°
echo "R" > /dev/ttyUSB0  # Mover a 0°
```

---

## 📝 RESUMEN

**✅ Más simple que usar Pico W**
**✅ Menos cables y componentes**
**✅ Más fácil de debuggear**
**✅ Control directo desde Python**

**Funcionamiento:**
1. Laptop detecta con cámara → Publica MQTT
2. RPi5 escucha MQTT → Envía comando a Arduino por USB
3. Arduino mueve servo según comando
4. Si no detecta por 5s → Reset automático

**¡Listo para usar!** 🚀
