# GUÍA COMPLETA DE CONEXIONES FÍSICAS
## Sistema de Detección de Pistachos - Arquitectura Real

---

## 📐 ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LAPTOP/PC (Windows)                         │
│  - Ejecuta cámara (detección YOLO)                                 │
│  - Publica detecciones a MQTT                                       │
│  - IP: 192.168.X.XXX (misma red WiFi)                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             │ WiFi / Ethernet
                             │ MQTT: mqtt://192.168.X.XXX:1883
                             │
┌────────────────────────────┴────────────────────────────────────────┐
│                    RASPBERRY PI 5 (Linux)                           │
│  - Sistema Operativo Linux (con pantalla)                           │
│  - Broker MQTT (Mosquitto en Docker)                                │
│  - Compila/carga código Arduino                                     │
│  - IP: 192.168.X.XXX (servidor MQTT)                                │
│                                                                      │
│  ┌──────────────┐                                                   │
│  │  Mosquitto   │ Puerto 1883 (MQTT Broker)                         │
│  └──────────────┘                                                   │
└───────────────────┬─────────────────────────────┬───────────────────┘
                    │                             │
                    │ USB                         │ USB
                    │                             │
         ┌──────────▼──────────┐      ┌──────────▼──────────┐
         │   PICO W (WiFi)     │      │   ARDUINO UNO       │
         │  - Recibe MQTT      │      │  - Conectado a RPi5 │
         │  - Procesa señal    │      │  - Se programa      │
         │  - Envía a Arduino  │      │    desde RPi5       │
         └──────────┬──────────┘      └──────────┬──────────┘
                    │                             │
                    │ UART Serial                 │
                    │ (3.3V ⇄ 5V)                │
                    │                             │
         ┌──────────▼─────────────────────────────▼──────────┐
         │        PROTOBOARD (Conexiones)                     │
         │                                                    │
         │  ┌──────────────────────────────────────┐         │
         │  │  Bi-Directional Level Converter      │         │
         │  │  LV (3.3V) ←→ HV (5V)                │         │
         │  └──────────────────────────────────────┘         │
         │                                                    │
         │  Rails de alimentación:                           │
         │  [+5V] ────────────────────────                   │
         │  [GND] ────────────────────────                   │
         └────────────────────────────┬───────────────────────┘
                                      │
                          ┌───────────▼───────────┐
                          │  SERVOMOTOR MG946R    │
                          │  (Torre/Tower)        │
                          │  - Alimentación: 5V   │
                          │  - Señal: Arduino Pin9│
                          └───────────────────────┘
```

---

## 🔌 PARTE 1: CONEXIONES RASPBERRY PI 5

### A) Raspberry Pi 5 ↔ Arduino Uno (USB)

**Conexión:**
```
Raspberry Pi 5 (Puerto USB-A) ──[Cable USB A-B]──> Arduino Uno (Puerto USB-B)
```

**Propósito:**
- Programar Arduino desde RPi5
- El Arduino NO se comunica directamente con RPi5 por serial
- Solo se usa para cargar el código

**En RPi5 aparecerá como:**
- `/dev/ttyUSB0` o `/dev/ttyACM0`

---

### B) Raspberry Pi 5 ↔ Pico W (USB - OPCIONAL)

**Conexión:**
```
Raspberry Pi 5 (Puerto USB) ──[Cable USB Micro]──> Pico W (Puerto Micro USB)
```

**Propósito:**
- Programar Pico W con Thonny desde RPi5
- Después de programar, puedes desconectar la Pico W del RPi5
- La Pico W puede alimentarse desde otro USB (cargador, powerbank, laptop)

**Nota:** La Pico W NO necesita estar conectada al RPi5 durante operación normal.

---

## 🔌 PARTE 2: CONEXIONES EN LA PROTOBOARD

### Setup de la Protoboard

```
PROTOBOARD - Vista Superior
═══════════════════════════════════════════════════════════

        [+] Rail Positivo (+5V)
        ─────────────────────────────────────────────

  a b c d e     f g h i j
  ═ ═ ═ ═ ═     ═ ═ ═ ═ ═
1 ○ ○ ○ ○ ○     ○ ○ ○ ○ ○
2 ○ ○ ○ ○ ○     ○ ○ ○ ○ ○
  ...
30 ○ ○ ○ ○ ○    ○ ○ ○ ○ ○

        [-] Rail Negativo (GND)
        ─────────────────────────────────────────────
```

---

### CONEXIÓN 1: Alimentación (Fuente Externa 5V)

**Componentes necesarios:**
- Fuente de alimentación 5V, 2-3A (adaptador de pared o fuente DC)
- Cable con conector barrel jack o cables + y -

**Conexiones:**

```
FUENTE EXTERNA 5V
    │
    ├── (+) Positivo ──────> [PROTOBOARD] Rail Positivo (+)
    │
    └── (-) Negativo ──────> [PROTOBOARD] Rail Negativo (-)
```

**CRÍTICO:** 
- ✅ Todos los GND deben conectarse al rail negativo
- ✅ Solo el servo se alimenta del rail positivo (+5V)
- ⚠️ NO conectar el rail +5V a ningún pin de Arduino (solo GND común)

---

### CONEXIÓN 2: Level Converter en Protoboard

**Componentes:**
- Bi-directional Logic Level Converter (4 canales)

**Posición en protoboard:**
```
Coloca el Level Converter centrado (pines a ambos lados del canal central)

Ejemplo: Filas 10-17

LADO LV (3.3V - Pico W)          LADO HV (5V - Arduino)
────────────────────             ────────────────────
Fila 10: LV                      Fila 10: HV
Fila 11: GND                     Fila 11: GND
Fila 12: LV1                     Fila 12: HV1
Fila 13: LV2                     Fila 13: HV2
Fila 14: LV3                     Fila 14: HV3
Fila 15: LV4                     Fila 15: HV4
```

**Conexiones del Level Converter:**

#### Lado LV (3.3V - para Pico W):
```
Level Converter          Protoboard                    Pico W
─────────────────        ──────────                    ──────
LV (Pin alimentación) ── Fila X columna a ──[cable]──> Pico W: 3V3 (Pin 36)
GND                   ── Fila Y columna a ──[puente]─> Rail Negativo (-)
LV1                   ── Fila Z columna a ──[cable]──> Pico W: GP4/TX (Pin 6)
LV2                   ── Fila W columna a ──[cable]──> Pico W: GP5/RX (Pin 7)
```

#### Lado HV (5V - para Arduino):
```
Level Converter          Protoboard                    Arduino
─────────────────        ──────────                    ───────
HV (Pin alimentación) ── Fila X columna j ──[cable]──> Arduino: 5V
GND                   ── Fila Y columna j ──[puente]─> Rail Negativo (-)
HV1                   ── Fila Z columna j ──[cable]──> Arduino: RX (Pin 0)
HV2                   ── Fila W columna j ──[cable]──> Arduino: TX (Pin 1)
```

**IMPORTANTE - Cables cruzados:**
- Pico W GP4 (TX) → LV1 → HV1 → Arduino RX
- Pico W GP5 (RX) → LV2 → HV2 → Arduino TX

---

### CONEXIÓN 3: Servomotor en Protoboard

**Servomotor MG946R (Tower) tiene 3 cables:**
- 🔴 **Rojo** = VCC (Alimentación +5V)
- 🟤 **Marrón/Negro** = GND (Tierra)
- 🟡 **Amarillo/Naranja** = Señal PWM

**Conexiones:**

```
Servomotor              Protoboard                    Destino
──────────              ──────────                    ───────
Cable ROJO (VCC)   ───> Fila A columna x ──[puente]─> Rail Positivo (+5V)
Cable MARRÓN (GND) ───> Fila B columna x ──[puente]─> Rail Negativo (-)
Cable AMARILLO (PWM)──> Fila C columna x ──[cable]──> Arduino Pin 9
```

**Opcional pero RECOMENDADO - Condensador de desacoplo:**

```
Condensador 470µF-1000µF (16V)
    (+) Pata larga  ──> Rail Positivo (+5V)
    (-) Pata corta  ──> Rail Negativo (-)
```

**Coloca el condensador cerca del servo en la protoboard**

---

### CONEXIÓN 4: GND Común (CRÍTICO)

**Todos estos deben conectarse al Rail Negativo (-) de la protoboard:**

```
Rail Negativo (-) de Protoboard
    │
    ├── Fuente Externa (-)
    ├── Arduino GND
    ├── Pico W GND (Pin 38)
    ├── Level Converter GND (ambos lados)
    └── Servomotor GND (cable marrón)
```

**Puedes usar puentes cortos en la protoboard para conectar todo al rail negativo**

---

## 🔌 PARTE 3: DIAGRAMA DE CONEXIONES DETALLADO

### Vista Completa de Conexiones

```
PICO W (conectada a WiFi, alimentada por USB de laptop o cargador)
─────────────────────────────────────────────────────────────
Pin 36 (3V3)  ────────────┐
Pin 38 (GND)  ────────┐   │
Pin 6  (GP4/TX) ───┐  │   │
Pin 7  (GP5/RX) ─┐ │  │   │
                 │ │  │   │
                 │ │  │   │
         ┌───────▼─▼──▼───▼────────────────┐
         │      PROTOBOARD                 │
         │                                 │
         │  ┌─────────────────────────┐   │
         │  │ Level Converter         │   │
         │  │ LV ← 3V3                │   │
         │  │ GND ← Rail (-)          │   │
         │  │ LV1 ← GP4 (TX)          │   │
         │  │ LV2 ← GP5 (RX)          │   │
         │  │                         │   │
         │  │ HV → Arduino 5V         │   │
         │  │ GND → Rail (-)          │   │
         │  │ HV1 → Arduino RX (Pin 0)│   │
         │  │ HV2 → Arduino TX (Pin 1)│   │
         │  └─────────────────────────┘   │
         │                                 │
         │  Rails de Alimentación:         │
         │  [+5V] ←── Fuente Externa (+)   │
         │         └──> Servo VCC (rojo)   │
         │                                 │
         │  [GND] ←── Fuente Externa (-)   │
         │         ├──> Arduino GND        │
         │         ├──> Pico W GND         │
         │         ├──> Level Conv. GND    │
         │         └──> Servo GND (marrón) │
         │                                 │
         │  Servo PWM (amarillo) ──┐       │
         └─────────────────────────┼───────┘
                                   │
                                   │
ARDUINO UNO (conectado a RPi5 por USB)      │
─────────────────────────────────────       │
Pin 0 (RX)  ← Level Converter HV1          │
Pin 1 (TX)  → Level Converter HV2          │
Pin 5V      → Level Converter HV           │
Pin GND     → Rail Negativo (-)            │
Pin 9 (PWM) ← ─────────────────────────────┘


SERVOMOTOR MG946R (Tower)
──────────────────────────
Cable ROJO    → Rail Positivo (+5V)
Cable MARRÓN  → Rail Negativo (-)
Cable AMARILLO→ Arduino Pin 9


FUENTE EXTERNA 5V (2-3A)
────────────────────────
(+) → Rail Positivo
(-) → Rail Negativo
```

---

## 📋 LISTA DE MATERIALES NECESARIOS

### Hardware:
- [ ] **Raspberry Pi 5** (con sistema operativo Linux y pantalla)
- [ ] **Arduino Uno** (con cable USB A-B)
- [ ] **Raspberry Pi Pico W** (con cable USB Micro)
- [ ] **Servomotor MG946R** o similar (Tower)
- [ ] **Bi-directional Logic Level Converter** (4 canales, 3.3V ↔ 5V)
- [ ] **Protoboard** (830 puntos recomendado)
- [ ] **Fuente de alimentación 5V, 2-3A** (para servo)
- [ ] **Condensador electrolítico 470µF-1000µF, 16V** (opcional pero recomendado)

### Cables:
- [ ] **Cables Dupont macho-macho** (20-30 unidades)
- [ ] **Cables Dupont macho-hembra** (10-15 unidades) 
- [ ] **Puentes de protoboard** (o cable sólido 22AWG)
- [ ] **Cable USB A-B** (para Arduino ↔ RPi5)
- [ ] **Cable USB Micro** (para Pico W ↔ RPi5 o laptop)

---

## 🔧 INSTRUCCIONES DE MONTAJE PASO A PASO

### PASO 1: Preparar la Protoboard

1. **Conectar fuente externa a rails:**
   ```
   Fuente 5V (+) ──> Rail Positivo (+) [rojo]
   Fuente 5V (-) ──> Rail Negativo (-) [azul/negro]
   ```

2. **NO ENCENDER la fuente todavía**

---

### PASO 2: Montar Level Converter

1. **Insertar Level Converter en protoboard** (centrado, filas 10-17 por ejemplo)

2. **Conectar alimentación del Level Converter:**
   ```
   LV pin ──[puente]──> Pico W 3V3 (usarás cable después)
   HV pin ──[puente]──> Arduino 5V (usarás cable después)
   ```

3. **Conectar GNDs:**
   ```
   Level Converter GND (lado LV) ──[puente]──> Rail Negativo
   Level Converter GND (lado HV) ──[puente]──> Rail Negativo
   ```

---

### PASO 3: Conectar Servomotor

1. **Conectar cables del servo a protoboard:**
   ```
   Cable ROJO (VCC)    ──> Insertar en fila X, luego puente a Rail (+)
   Cable MARRÓN (GND)  ──> Insertar en fila Y, luego puente a Rail (-)
   Cable AMARILLO (PWM)──> Insertar en fila Z (dejar libre para conectar a Arduino)
   ```

2. **Opcional: Agregar condensador:**
   ```
   Pata larga (+) ──> Rail Positivo
   Pata corta (-) ──> Rail Negativo
   (Cerca del servo)
   ```

---

### PASO 4: Conectar Pico W a Protoboard

**Cables Dupont macho-hembra (Pico W tiene pines macho):**

```
Pico W Pin 36 (3V3)  ──[cable]──> Level Converter LV
Pico W Pin 38 (GND)  ──[cable]──> Rail Negativo (-)
Pico W Pin 6 (GP4)   ──[cable]──> Level Converter LV1
Pico W Pin 7 (GP5)   ──[cable]──> Level Converter LV2
```

**Referencia de pines Pico W:**
```
Pico W (vista superior, USB arriba)
     ┌─────────┐
     │  USB    │
     └─────────┘
 GP0  1 ●   ● 40  VBUS
 GP1  2 ●   ● 39  VSYS
 GND  3 ●   ● 38  GND ← CONECTAR
 GP2  4 ●   ● 37  3V3_EN
 GP3  5 ●   ● 36  3V3 ← CONECTAR
 GP4  6 ●   ● 35  
 GP5  7 ●   ● 34  
      ... (más pines)
```

---

### PASO 5: Conectar Arduino a Protoboard

**Cables Dupont macho-macho:**

```
Arduino 5V      ──[cable]──> Level Converter HV
Arduino GND     ──[cable]──> Rail Negativo (-)
Arduino Pin 0 (RX) ──[cable]──> Level Converter HV1
Arduino Pin 1 (TX) ──[cable]──> Level Converter HV2
Arduino Pin 9   ──[cable]──> Servo AMARILLO (PWM)
```

---

### PASO 6: Verificar Conexiones (CHECKLIST)

**Antes de encender, verificar:**

- [ ] Fuente externa (+) → Rail Positivo
- [ ] Fuente externa (-) → Rail Negativo
- [ ] Servo ROJO → Rail Positivo
- [ ] Servo MARRÓN → Rail Negativo
- [ ] Servo AMARILLO → Arduino Pin 9
- [ ] Arduino GND → Rail Negativo
- [ ] Pico W GND → Rail Negativo
- [ ] Level Converter ambos GND → Rail Negativo
- [ ] Pico W 3V3 → Level Converter LV
- [ ] Arduino 5V → Level Converter HV
- [ ] Pico W GP4 → Level Converter LV1
- [ ] Pico W GP5 → Level Converter LV2
- [ ] Level Converter HV1 → Arduino RX (Pin 0)
- [ ] Level Converter HV2 → Arduino TX (Pin 1)

**CRÍTICO - Verificar polaridad:**
- [ ] Condensador: pata larga (+) a positivo, corta (-) a GND
- [ ] Fuente: polaridad correcta (+ y -)

---

### PASO 7: Encender Sistema

**Orden de encendido:**

1. **Conectar Arduino a RPi5** (USB) - Arduino recibe 5V del USB
2. **Conectar Pico W** (USB a laptop/cargador) - Pico recibe 3.3V internamente
3. **Encender fuente externa 5V** - Servo recibe alimentación
4. **Verificar LEDs:**
   - Arduino: LED ON (verde) debe encender
   - Pico W: LED debe parpadear (conectando WiFi)

---

## 🌐 PARTE 4: CONFIGURACIÓN DE RED

### A) Obtener IP del Raspberry Pi 5

En RPi5 (desde terminal):
```bash
hostname -I
# Ejemplo salida: 192.168.1.42
```

**Anotar esta IP:**
- IP del RPi5 (Broker MQTT): `192.168.1.42`

---

### B) Configurar Laptop/PC (Cámara)

**Editar el script de cámara para apuntar al broker en RPi5:**

En tu laptop, editar `videoPublicTopic_mejorado.py`:
```python
BROKER = "192.168.1.42"  # ← IP del RPi5
PORT = 1883
TOPIC = "robot/pico/estado"
```

---

### C) Configurar Pico W

**Editar `secrets.py` en Pico W:**
```python
WIFI_SSID = "TuWiFi"              # ← Tu red WiFi
WIFI_PASSWORD = "TuContraseña"     # ← Tu contraseña
MQTT_BROKER = "192.168.1.42"       # ← IP del RPi5
MQTT_PORT = 1883
```

---

## 🚀 PARTE 5: FLUJO DE OPERACIÓN COMPLETO

### Paso a Paso de Uso:

#### 1. **Iniciar Broker MQTT en Raspberry Pi 5**

En RPi5 (terminal):
```bash
# Verificar que Mosquitto esté corriendo
sudo docker ps | grep mosquitto

# Si no está, iniciarlo
sudo docker start mosquitto

# Verificar logs
sudo docker logs mosquitto
```

---

#### 2. **Cargar código en Arduino desde RPi5**

En RPi5 (terminal o Arduino IDE):
```bash
# Opción A: Arduino IDE
# Abrir arduino/servo_control_mejorado.ino
# Tools → Board → Arduino Uno
# Tools → Port → /dev/ttyUSB0
# Upload

# Opción B: arduino-cli
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno servo_control_mejorado.ino
```

**Verificar en Arduino:**
- LED debe parpadear 3 veces al iniciar
- Monitor serial debe mostrar: `ARDUINO_READY`

---

#### 3. **Programar Pico W desde RPi5 (o laptop)**

Con Thonny:
1. Conectar Pico W por USB
2. Seleccionar: MicroPython (Raspberry Pi Pico)
3. Abrir `picow/secrets.py` → Guardar en dispositivo
4. Abrir `picow/main_mejorado.py` → Guardar como `main.py` en dispositivo
5. Desconectar Pico W
6. Reconectar Pico W (a laptop o cargador USB)

**Verificar en Pico W:**
- LED parpadea 3 veces rápido si hay error WiFi/MQTT
- LED parpadea 1 vez largo si conectó OK
- Consola Thonny muestra: `WiFi conectado`, `MQTT conectado`

---

#### 4. **Ejecutar detección de cámara desde Laptop/PC**

En tu laptop (Windows, donde tienes la cámara):
```bash
cd ruta/al/proyecto/rpi5
python videoPublicTopic_mejorado.py
```

**Deberías ver:**
```
Conectado al broker MQTT en 192.168.1.42:1883
Cámara inicializada: 640x480
Sistema iniciado. Presiona 'q' para salir.
```

---

#### 5. **Probar el sistema completo**

**Cuando se detecte un pistacho con confianza >= 0.6:**

1. **Laptop** detecta y publica a MQTT:
   ```
   📤 MQTT publicado: {'objeto': 'pistachio', 'confianza': 0.85}
   ```

2. **Pico W** recibe mensaje MQTT:
   ```
   [INFO] Mensaje MQTT recibido
   [INFO] PISTACHO VÁLIDO detectado (0.85)
   [INFO] Comando enviado a Arduino: b'A'
   ```

3. **Arduino** ejecuta movimiento:
   ```
   CMD_RX: A
   SERVO_START
   POS: 0
   POS: 180
   POS: 0
   SERVO_DONE
   ```

4. **Servomotor** gira: 0° → 180° → 0°

---

## 🔍 VERIFICACIÓN Y DEBUGGING

### Prueba 1: Verificar MQTT (en RPi5)

Terminal 1 (suscriptor):
```bash
mosquitto_sub -h localhost -t robot/pico/estado -v
```

Terminal 2 (publicador):
```bash
mosquitto_pub -h localhost -t robot/pico/estado -m '{"objeto":"pistachio","confianza":0.8}'
```

**Debe aparecer el mensaje en Terminal 1**

---

### Prueba 2: Verificar Comunicación Serial Pico W ↔ Arduino

**Desde Thonny (Pico W conectada):**
```python
# En consola de Thonny
>>> from machine import UART, Pin
>>> uart = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))
>>> uart.write(b'S')  # Comando Status
1
>>> uart.read()  # Debe recibir respuesta del Arduino
```

**Arduino debe responder con estado**

---

### Prueba 3: Verificar Movimiento del Servo

**Desde monitor serial de Arduino (RPi5):**
```
Enviar: A
```

**Servo debe moverse 0° → 180° → 0°**

---

## ⚠️ SOLUCIÓN DE PROBLEMAS COMUNES

### Problema: Servo no gira o vibra

**Verificar:**
- [ ] Fuente externa encendida y con suficiente amperaje (2-3A)
- [ ] Cable amarillo servo → Arduino Pin 9
- [ ] GND común (todos conectados al rail negativo)
- [ ] Condensador conectado correctamente

**Solución:**
```bash
# Medir voltaje con multímetro:
# Entre Rail (+) y Rail (-) debe haber ~5V
```

---

### Problema: Pico W no recibe mensajes MQTT

**Verificar:**
- [ ] Pico W conectada a WiFi (ver LED o consola Thonny)
- [ ] IP correcta en `secrets.py`
- [ ] Broker MQTT corriendo en RPi5: `sudo docker ps`
- [ ] Laptop y Pico W en la misma red WiFi

**Solución:**
```bash
# Desde laptop, hacer ping al RPi5:
ping 192.168.1.42
```

---

### Problema: Arduino no responde a comandos de Pico W

**Verificar:**
- [ ] Level Converter bien conectado
- [ ] Cables TX/RX cruzados (TX→RX, RX→TX)
- [ ] Ambos GNDs del Level Converter al rail negativo
- [ ] Arduino cargado con `servo_control_mejorado.ino`

**Solución:**
```bash
# Test con minicom desde RPi5:
minicom -D /dev/ttyUSB0 -b 9600
# Presionar 'A', debe ver respuesta
```

---

## ✅ CHECKLIST FINAL ANTES DE OPERAR

### Hardware:
- [ ] Fuente 5V externa conectada y encendida
- [ ] Servo alimentado desde fuente externa (NO desde Arduino)
- [ ] GND común: todos los GND al rail negativo
- [ ] Level Converter con voltajes correctos (LV=3.3V, HV=5V)
- [ ] Arduino conectado a RPi5 por USB
- [ ] Pico W alimentada (USB laptop o cargador)

### Software RPi5:
- [ ] Mosquitto corriendo: `sudo docker ps | grep mosquitto`
- [ ] Arduino programado con `servo_control_mejorado.ino`
- [ ] Pantalla RPi5 mostrando sistema Linux

### Software Pico W:
- [ ] `secrets.py` con credenciales correctas
- [ ] `main_mejorado.py` guardado como `main.py`
- [ ] Conectada a WiFi (verificar en Thonny)
- [ ] Suscrita a MQTT (verificar logs)

### Software Laptop:
- [ ] `videoPublicTopic_mejorado.py` configurado con IP de RPi5
- [ ] Cámara conectada y funcionando
- [ ] Modelo `best.pt` en carpeta `rpi5/`

---

**¡Sistema listo para operar!** 🎯🥜

