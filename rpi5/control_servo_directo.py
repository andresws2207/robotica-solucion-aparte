#!/usr/bin/env python3
"""
control_servo_directo.py
SOLUCIÓN SIMPLE: Python escucha MQTT y controla Arduino directamente por USB

ARQUITECTURA:
- Laptop: Ejecuta cámara, publica a MQTT
- RPi5: Ejecuta ESTE script (escucha MQTT + controla Arduino)
- Arduino: Conectado a RPi5 por USB, mueve servomotor

FUNCIONAMIENTO:
- Si detecta pistacho (confianza >= 0.6): Servo a 180° (derecha)
- Si no detecta nada por 5 segundos: Servo a 0° (izquierda)
- Movimiento cada 5 segundos máximo
"""

import paho.mqtt.client as mqtt
import serial
import json
import time
import logging
from datetime import datetime

# ============ CONFIGURACIÓN ============
# MQTT
BROKER = "localhost"  # RPi5 ejecuta el broker
PORT = 1883
TOPIC = "robot/pico/estado"

# Serial Arduino
SERIAL_PORT = "/dev/ttyUSB0"  # Cambiar a /dev/ttyACM0 si es necesario
BAUDRATE = 9600
TIMEOUT = 2

# Detección
CONFIDENCE_THRESHOLD = 0.6  # 60% mínimo
NO_DETECTION_TIMEOUT = 5.0  # 5 segundos sin detección

# Comandos Arduino
CMD_ACTIVATE = b'A'  # Mover a 180° (pistacho detectado)
CMD_RESET = b'R'     # Mover a 0° (sin detección)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ VARIABLES GLOBALES ============
arduino_serial = None
last_detection_time = None
last_movement_time = 0
MOVEMENT_COOLDOWN = 5.0  # Mover servo cada 5 segundos como máximo

# ============ FUNCIONES SERIAL ============

def conectar_arduino():
    """Conecta con Arduino por serial USB"""
    global arduino_serial
    
    try:
        logger.info(f"Conectando a Arduino en {SERIAL_PORT}...")
        arduino_serial = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUDRATE,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=TIMEOUT
        )
        
        # Esperar inicialización Arduino (reset por DTR)
        time.sleep(2)
        
        # Leer mensaje de inicio
        if arduino_serial.in_waiting > 0:
            msg = arduino_serial.read(arduino_serial.in_waiting)
            logger.info(f"Arduino dice: {msg.decode('utf-8', errors='ignore')}")
        
        logger.info("✓ Conexión Arduino establecida")
        return True
        
    except serial.SerialException as e:
        logger.error(f"✗ Error conectando Arduino: {e}")
        logger.error(f"Verifica que Arduino esté conectado en {SERIAL_PORT}")
        logger.error("Ejecuta: ls -l /dev/ttyUSB* /dev/ttyACM*")
        return False

def enviar_comando(comando):
    """Envía comando al Arduino y espera respuesta
    
    Args:
        comando (bytes): Comando a enviar (b'A', b'R', b'S')
        
    Returns:
        bool: True si se ejecutó correctamente
    """
    global arduino_serial
    
    if arduino_serial is None or not arduino_serial.is_open:
        logger.error("Arduino no conectado")
        return False
    
    try:
        # Limpiar buffer
        arduino_serial.reset_input_buffer()
        
        # Enviar comando
        arduino_serial.write(comando)
        arduino_serial.flush()
        
        logger.debug(f"Comando enviado: {comando}")
        
        # Esperar respuesta (timeout 2 segundos)
        time.sleep(0.5)
        
        if arduino_serial.in_waiting > 0:
            respuesta = arduino_serial.read(arduino_serial.in_waiting)
            logger.debug(f"Arduino responde: {respuesta}")
            
            # Verificar respuesta esperada
            if comando == CMD_ACTIVATE and b'D' in respuesta:
                logger.info("✓ Arduino completó secuencia ACTIVATE (180°)")
                return True
            elif comando == CMD_RESET and b'K' in respuesta:
                logger.info("✓ Arduino completó RESET (0°)")
                return True
        
        logger.warning("Arduino no respondió como esperado")
        return True  # Comando enviado aunque no haya confirmación
        
    except Exception as e:
        logger.error(f"Error enviando comando: {e}")
        return False

def mover_servo_pistacho():
    """Mueve servo a posición de pistacho detectado (180°)"""
    logger.info("🥜 PISTACHO DETECTADO → Moviendo servo a 180°")
    return enviar_comando(CMD_ACTIVATE)

def mover_servo_default():
    """Mueve servo a posición por defecto (0°) - Sin detección"""
    logger.info("⏸ SIN DETECCIÓN → Moviendo servo a 0°")
    return enviar_comando(CMD_RESET)

# ============ FUNCIONES MQTT ============

def on_connect(client, userdata, flags, rc):
    """Callback cuando se conecta al broker MQTT"""
    if rc == 0:
        logger.info(f"✓ Conectado al broker MQTT en {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        logger.info(f"✓ Suscrito al topic: {TOPIC}")
    else:
        logger.error(f"✗ Error de conexión MQTT. Código: {rc}")

def on_message(client, userdata, msg):
    """Callback cuando llega un mensaje MQTT"""
    global last_detection_time, last_movement_time
    
    try:
        payload = msg.payload.decode()
        logger.debug(f"MQTT recibido: {payload}")
        
        # Parsear JSON
        data = json.loads(payload)
        
        if 'objeto' not in data or 'confianza' not in data:
            logger.warning("Mensaje MQTT sin campos requeridos")
            return
        
        objeto = data['objeto']
        confianza = float(data['confianza'])
        
        logger.info(f"📡 Detección: {objeto} ({confianza:.2%})")
        
        # VALIDAR: Solo pistachos con confianza >= 60%
        if "pistachio" in objeto.lower() and confianza >= CONFIDENCE_THRESHOLD:
            # Actualizar timestamp de última detección
            last_detection_time = time.time()
            
            # Verificar cooldown de movimiento (no mover muy seguido)
            time_since_last_move = time.time() - last_movement_time
            
            if time_since_last_move >= MOVEMENT_COOLDOWN:
                logger.info(f"🎯 PISTACHO VÁLIDO ({confianza:.2%}) - Activando servo")
                if mover_servo_pistacho():
                    last_movement_time = time.time()
            else:
                wait_time = MOVEMENT_COOLDOWN - time_since_last_move
                logger.info(f"⏳ Cooldown activo. Espera {wait_time:.1f}s más")
        else:
            if confianza < CONFIDENCE_THRESHOLD:
                logger.info(f"⚠ Confianza {confianza:.2%} < {CONFIDENCE_THRESHOLD:.0%} - IGNORADO")
            else:
                logger.info(f"⚠ Objeto '{objeto}' no es pistacho - IGNORADO")
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON: {e}")
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")

def verificar_timeout_deteccion():
    """Verifica si han pasado 5 segundos sin detección"""
    global last_detection_time, last_movement_time
    
    if last_detection_time is None:
        return
    
    tiempo_sin_deteccion = time.time() - last_detection_time
    
    if tiempo_sin_deteccion >= NO_DETECTION_TIMEOUT:
        # Han pasado 5 segundos sin detección
        time_since_last_move = time.time() - last_movement_time
        
        if time_since_last_move >= MOVEMENT_COOLDOWN:
            logger.info(f"⏱ {NO_DETECTION_TIMEOUT}s sin detección - Reseteando servo")
            if mover_servo_default():
                last_movement_time = time.time()
                last_detection_time = None  # Reset para no ejecutar repetidamente

# ============ MAIN ============

def main():
    """Función principal"""
    global arduino_serial
    
    logger.info("="*60)
    logger.info("Control Directo Servo - RPi5 → Arduino")
    logger.info(f"Broker MQTT: {BROKER}:{PORT}")
    logger.info(f"Arduino: {SERIAL_PORT} @ {BAUDRATE}")
    logger.info(f"Umbral confianza: {CONFIDENCE_THRESHOLD:.0%}")
    logger.info(f"Timeout sin detección: {NO_DETECTION_TIMEOUT}s")
    logger.info("="*60)
    
    # 1. Conectar Arduino
    if not conectar_arduino():
        logger.error("No se pudo conectar con Arduino. Abortando.")
        logger.error("\nSOLUCIONES:")
        logger.error("1. Verifica que Arduino esté conectado: ls -l /dev/ttyUSB*")
        logger.error("2. Verifica permisos: groups | grep dialout")
        logger.error("3. Si no estás en dialout: sudo usermod -a -G dialout $USER")
        logger.error("4. Prueba con otro puerto: SERIAL_PORT = '/dev/ttyACM0'")
        return
    
    # 2. Conectar MQTT
    try:
        client = mqtt.Client(client_id=f"rpi5_control_{int(time.time())}")
        client.on_connect = on_connect
        client.on_message = on_message
        
        logger.info(f"Conectando a broker MQTT...")
        client.connect(BROKER, PORT, 60)
        client.loop_start()
        
    except Exception as e:
        logger.error(f"Error conectando a MQTT: {e}")
        logger.error("\nSOLUCIONES:")
        logger.error("1. Verifica que Mosquitto esté corriendo: sudo docker ps | grep mosquitto")
        logger.error("2. Inicia el broker: sudo docker start mosquitto")
        arduino_serial.close()
        return
    
    # 3. Loop principal
    logger.info("\n🚀 Sistema iniciado. Presiona Ctrl+C para salir.\n")
    
    try:
        # Posición inicial
        time.sleep(1)
        logger.info("Posicionando servo en estado inicial (0°)...")
        mover_servo_default()
        
        while True:
            # Verificar timeout de detección cada segundo
            verificar_timeout_deteccion()
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n\n⚠ Interrupción por usuario (Ctrl+C)")
    
    finally:
        # Limpieza
        logger.info("Cerrando conexiones...")
        
        if arduino_serial and arduino_serial.is_open:
            logger.info("Reseteando servo a posición inicial...")
            enviar_comando(CMD_RESET)
            time.sleep(1)
            arduino_serial.close()
            logger.info("✓ Arduino desconectado")
        
        client.loop_stop()
        client.disconnect()
        logger.info("✓ MQTT desconectado")
        
        logger.info("Sistema detenido correctamente")

if __name__ == "__main__":
    main()
