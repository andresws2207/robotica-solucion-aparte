# GUÍA RÁPIDA DE INICIO
## Sistema de Detección de Pistachos - RPi5 + Arduino + Pico W

---

## 🚀 INICIO RÁPIDO (5 minutos)

### Paso 1: Instalación Automática
```bash
cd robotica-pico-rpi5-main
chmod +x setup_sistema.sh
./setup_sistema.sh
```

### Paso 2: Reiniciar Sesión
```bash
# Opción 1: Cerrar sesión y volver a entrar
logout

# Opción 2: Aplicar grupo dialout sin reiniciar
newgrp dialout
```

### Paso 3: Configurar Credenciales
```bash
# Editar archivo de credenciales
nano picow/secrets.py
```

Modificar estos valores:
```python
WIFI_SSID = "TuNombreWiFi"           # ← Tu red WiFi
WIFI_PASSWORD = "TuContraseñaWiFi"   # ← Tu contraseña
MQTT_BROKER = "192.168.1.XX"         # ← IP mostrada por setup_sistema.sh
MQTT_PORT = 1883
```

### Paso 4: Cargar Código en Dispositivos

**Arduino Uno** (opción A - Arduino IDE):
1. Abrir `arduino/servo_control_mejorado.ino`
2. Seleccionar Board: Arduino Uno
3. Seleccionar Port: `/dev/ttyUSB0` (o el que aparezca)
4. Hacer clic en Upload
5. Cerrar Arduino IDE

**Arduino Uno** (opción B - arduino-cli):
```bash
cd arduino
arduino-cli upload -p /dev/ttyUSB0 --fqbn arduino:avr:uno servo_control_mejorado.ino
```

**Raspberry Pi Pico W** (con Thonny):
1. Abrir Thonny
2. Conectar Pico W por USB
3. Seleccionar intérprete: MicroPython (Raspberry Pi Pico)
4. Abrir `picow/secrets.py` → Guardar en dispositivo
5. Abrir `picow/main_mejorado.py` → Guardar en dispositivo como `main.py`
6. Desconectar y reconectar Pico W (auto-inicia)

### Paso 5: Verificar Sistema
```bash
python3 rpi5/diagnostico_arduino.py
```

**Debe mostrar**:
- ✓ OK - OS
- ✓ OK - GROUPS
- ✓ OK - PERMISSIONS
- ✓ OK - COMMUNICATION
- ✓ OK - PACKAGES
- ✓ OK - PROCESSES

### Paso 6: ¡Ejecutar!
```bash
cd rpi5
python3 videoPublicTopic_mejorado.py
```

**Presiona `q` para salir**

---

## 🔍 VERIFICACIÓN RÁPIDA DE PROBLEMAS

### ❌ Error: "Permission denied" en puerto serial
```bash
# Solución:
sudo usermod -a -G dialout $USER
newgrp dialout
```

### ❌ Arduino no responde
```bash
# Verificar puerto:
ls -l /dev/ttyUSB*

# Monitorear comunicación:
minicom -D /dev/ttyUSB0 -b 9600
# Dentro de minicom, presionar 'A' (debe responder)
# Salir: Ctrl+A, luego Q
```

### ❌ MQTT no conecta
```bash
# Verificar broker:
sudo docker ps | grep mosquitto

# Si no está corriendo:
sudo docker start mosquitto

# Ver logs:
sudo docker logs mosquitto
```

### ❌ Pico W no conecta a WiFi
```bash
# Verificar credenciales en secrets.py
# Verificar LED de Pico:
# - 3 parpadeos rápidos = Error WiFi/MQTT
# - 1 parpadeo largo = Conectado OK
# - 2 parpadeos = Comando enviado
```

### ❌ Servo no gira
```bash
# Verificar alimentación:
# ¿Servo conectado a fuente EXTERNA de 5V?
# ¿GND común entre Arduino, fuente y servo?
# ¿Pin 9 Arduino conectado a señal servo?
```

---

## 📋 CHECKLIST PRE-EJECUCIÓN

Hardware:
- [ ] Arduino conectado por USB al RPi5
- [ ] Servo alimentado por **fuente externa** (NO Arduino)
- [ ] GND común: Arduino + Fuente + Level Converter + Servo
- [ ] Level Converter: LV=3.3V, HV=5V
- [ ] Pico W conectada por USB

Software:
- [ ] `sudo docker ps | grep mosquitto` → debe aparecer
- [ ] `groups | grep dialout` → debe aparecer
- [ ] `ls /dev/ttyUSB0` → debe existir
- [ ] Arduino IDE cerrado
- [ ] `secrets.py` editado con tus credenciales

Código:
- [ ] `servo_control_mejorado.ino` cargado en Arduino
- [ ] `main_mejorado.py` en Pico W (como `main.py`)
- [ ] `secrets.py` en Pico W

---

## 🎯 FLUJO DE USO DIARIO

### Encender Sistema:
```bash
# 1. Verificar MQTT
sudo docker ps | grep mosquitto

# 2. Conectar Pico W (auto-inicia)

# 3. Ejecutar detección
cd rpi5
python3 videoPublicTopic_mejorado.py
```

### Apagar Sistema:
1. Presionar `q` en ventana de detección
2. Desconectar Pico W (opcional)
3. MQTT puede quedarse corriendo

---

## 📞 COMANDOS DE EMERGENCIA

```bash
# Reiniciar todo
sudo docker restart mosquitto
sudo reboot

# Ver logs de detección
tail -f rpi5/deteccion_pistachos.log

# Test manual MQTT
mosquitto_pub -h localhost -t robot/pico/estado -m '{"objeto":"pistachio","confianza":0.8}'

# Ver puertos seriales
dmesg | grep tty

# Matar procesos que usan puerto
sudo lsof /dev/ttyUSB0
sudo kill -9 <PID>
```

---

## 📊 VALORES IMPORTANTES

### Umbral de Detección:
- **Mínimo requerido**: 0.6 (60% de confianza)
- Solo pistachos con ≥60% activan servo
- Configurable en `videoPublicTopic_mejorado.py`:
  ```python
  CONFIDENCE_THRESHOLD = 0.6
  ```

### Puertos y Baudrates:
- **MQTT**: `localhost:1883`
- **Serial Arduino**: `9600 baud, 8N2`
- **UART Pico W**: `GP4 (TX), GP5 (RX), 9600 baud`

### Tiempos:
- **Servo delay**: 500ms entre movimientos
- **Cooldown MQTT**: 1 segundo entre publicaciones
- **Timeout Arduino**: 3 segundos
- **Heartbeat Pico W**: 10 segundos

---

## 🆘 SOPORTE

### Si nada funciona:
1. **Ejecutar diagnóstico completo**:
   ```bash
   python3 rpi5/diagnostico_arduino.py
   ```

2. **Leer documentación completa**:
   - `README.md` → Sección 11: Solución de Problemas
   - `MEJORAS_IMPLEMENTADAS.md` → Resumen técnico

3. **Verificar conexiones físicas**:
   - GND común es CRÍTICO
   - Alimentación servo EXTERNA es OBLIGATORIA
   - Level Converter con voltajes correctos (LV=3.3V, HV=5V)

4. **Ver logs**:
   ```bash
   # Logs de Python
   cat rpi5/deteccion_pistachos.log
   
   # Logs de MQTT
   sudo docker logs mosquitto
   
   # Logs de Pico W
   # Conectar con Thonny y ver consola
   ```

---

## ✅ SISTEMA FUNCIONANDO CORRECTAMENTE

**Deberías ver**:

1. **En Pico W** (Thonny):
   ```
   [12345] [INFO] WiFi conectado
   [12350] [INFO] MQTT conectado
   [15000] [INFO] Mensaje MQTT recibido
   [15001] [INFO] PISTACHO VÁLIDO detectado (0.85)
   [15002] [INFO] Comando enviado a Arduino: b'A'
   [15500] [INFO] ✓ Arduino completó secuencia
   ```

2. **En RPi5** (consola):
   ```
   Conectado al broker MQTT en localhost:1883
   Cámara inicializada: 640x480
   Sistema iniciado. Presiona 'q' para salir.
   
   📤 MQTT publicado: {'objeto': 'pistachio', 'confianza': 0.85}
   🎯 Detección #1: pistachio (85.00%)
   ```

3. **Arduino** (LED):
   - Parpadea 3 veces al inicio
   - Se enciende durante movimiento servo
   - Parpadea brevemente cada 5 segundos (heartbeat)

4. **Servo**:
   - Se mueve: 0° → 180° → 0°
   - Movimiento suave y completo
   - Regresa a posición inicial

---

**¡Sistema listo para detectar pistachos! 🥜✨**
