# main_mejorado.py (MicroPython para Pico W)
# 
# MEJORAS IMPLEMENTADAS:
# 1. Validación de umbral de confianza (>= 0.6)
# 2. Reconexión automática WiFi y MQTT
# 3. Manejo robusto de errores UART
# 4. Heartbeat para verificar conexión
# 5. Timeouts configurables
# 6. Logs detallados para debugging
#
# Conexiones:
# - Pico W GP4 (Pin 6, TX) -> Level Converter LV1 -> Arduino RX
# - Pico W GP5 (Pin 7, RX) -> Level Converter LV2 -> Arduino TX
# - Pico W 3V3 (Pin 36) -> Level Converter LV
# - Pico W GND (Pin 38) -> Level Converter GND

import time
import network
import ujson
from umqtt.simple import MQTTClient
from machine import UART, Pin, reset
import secrets

# ========== CONFIGURACIÓN ==========
# UART
UART_ID = 1
UART_BAUDRATE = 9600
UART_TX_PIN = 4  # GP4
UART_RX_PIN = 5  # GP5

# MQTT
TOPIC_DETECCION = b"robot/pico/estado"
QOS = 1

# Umbral de confianza
CONFIDENCE_THRESHOLD = 0.6  # 60%

# Timeouts (milisegundos)
WIFI_TIMEOUT = 15000
MQTT_TIMEOUT = 10000
ARDUINO_TIMEOUT = 3000
HEARTBEAT_INTERVAL = 10000

# Reintentos
MAX_RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 5000  # ms

# LED interno
led = Pin("LED", Pin.OUT)

# ========== VARIABLES GLOBALES ==========
uart = None
wlan = None
mqtt_client = None
last_heartbeat = 0
reconnect_count = 0

# ========== FUNCIONES DE UTILIDAD ==========
def log(msg, level="INFO"):
    """Imprime log con timestamp"""
    timestamp = time.ticks_ms()
    print(f"[{timestamp}] [{level}] {msg}")

def blink_led(times=1, delay_ms=200):
    """Parpadea el LED interno"""
    for _ in range(times):
        led.on()
        time.sleep_ms(delay_ms)
        led.off()
        time.sleep_ms(delay_ms)

def blink_error():
    """Patrón de parpadeo para error (3 parpadeos rápidos)"""
    blink_led(3, 100)

def blink_success():
    """Patrón de parpadeo para éxito (1 parpadeo largo)"""
    led.on()
    time.sleep_ms(500)
    led.off()

# ========== INICIALIZACIÓN UART ==========
def init_uart():
    """Inicializa comunicación UART con Arduino"""
    global uart
    
    try:
        log("Inicializando UART...")
        uart = UART(UART_ID, baudrate=UART_BAUDRATE, tx=Pin(UART_TX_PIN), rx=Pin(UART_RX_PIN))
        uart.init(bits=8, parity=None, stop=2)
        
        # Limpiar buffer
        time.sleep_ms(100)
        while uart.any():
            uart.read()
        
        log("UART inicializado correctamente")
        return True
        
    except Exception as e:
        log(f"Error inicializando UART: {e}", "ERROR")
        blink_error()
        return False

# ========== COMUNICACIÓN UART ==========
def send_to_arduino(command):
    """Envía comando al Arduino
    
    Args:
        command: String o bytes a enviar
        
    Returns:
        bool: True si se envió correctamente
    """
    global uart
    
    if uart is None:
        log("UART no inicializado", "ERROR")
        return False
    
    try:
        if isinstance(command, str):
            command = command.encode()
        
        uart.write(command)
        log(f"Comando enviado a Arduino: {command}")
        return True
        
    except Exception as e:
        log(f"Error enviando a Arduino: {e}", "ERROR")
        return False

def wait_arduino_response(expected_response=b'D', timeout_ms=ARDUINO_TIMEOUT):
    """Espera respuesta del Arduino con timeout
    
    Args:
        expected_response: Respuesta esperada (bytes)
        timeout_ms: Timeout en milisegundos
        
    Returns:
        bool: True si se recibió la respuesta esperada
    """
    global uart
    
    if uart is None:
        return False
    
    start_time = time.ticks_ms()
    
    while time.ticks_diff(time.ticks_ms(), start_time) < timeout_ms:
        if uart.any():
            data = uart.read()
            if data:
                log(f"Respuesta Arduino: {data}")
                
                if expected_response in data:
                    log("✓ Respuesta correcta recibida")
                    return True
        
        time.sleep_ms(50)
    
    log(f"⚠ Timeout esperando respuesta de Arduino ({timeout_ms}ms)", "WARN")
    return False

# ========== CONEXIÓN WIFI ==========
def connect_wifi():
    """Conecta a WiFi con reintentos
    
    Returns:
        bool: True si se conectó correctamente
    """
    global wlan, reconnect_count
    
    log("Conectando a WiFi...")
    log(f"SSID: {secrets.WIFI_SSID}")
    
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    if wlan.isconnected():
        log("WiFi ya conectado")
        log(f"IP: {wlan.ifconfig()[0]}")
        return True
    
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
    
    # Esperar conexión con timeout
    start_time = time.ticks_ms()
    while not wlan.isconnected():
        if time.ticks_diff(time.ticks_ms(), start_time) > WIFI_TIMEOUT:
            log("Timeout conectando a WiFi", "ERROR")
            blink_error()
            reconnect_count += 1
            return False
        
        time.sleep_ms(500)
        led.toggle()  # Parpadeo durante conexión
    
    led.off()
    log("✓ WiFi conectado")
    log(f"IP: {wlan.ifconfig()[0]}")
    blink_success()
    reconnect_count = 0
    
    return True

# ========== CONEXIÓN MQTT ==========
def connect_mqtt():
    """Conecta al broker MQTT
    
    Returns:
        MQTTClient o None si falla
    """
    global mqtt_client
    
    try:
        client_id = b"pico_w_%d" % (time.ticks_ms() & 0xFFFF)
        
        log(f"Conectando a MQTT broker {secrets.MQTT_BROKER}...")
        
        mqtt_client = MQTTClient(
            client_id, 
            secrets.MQTT_BROKER, 
            port=secrets.MQTT_PORT,
            keepalive=60
        )
        
        mqtt_client.set_callback(mqtt_callback)
        mqtt_client.connect()
        
        log("✓ MQTT conectado")
        
        # Suscribirse al topic
        mqtt_client.subscribe(TOPIC_DETECCION)
        log(f"Suscrito a: {TOPIC_DETECCION}")
        
        blink_success()
        return mqtt_client
        
    except Exception as e:
        log(f"Error conectando a MQTT: {e}", "ERROR")
        blink_error()
        return None

# ========== CALLBACK MQTT ==========
def mqtt_callback(topic, msg):
    """Procesa mensajes MQTT recibidos
    
    Args:
        topic: Topic del mensaje (bytes)
        msg: Payload del mensaje (bytes)
    """
    try:
        log(f"\n{'='*40}")
        log(f"Mensaje MQTT recibido")
        log(f"Topic: {topic.decode()}")
        log(f"Payload: {msg.decode()}")
        
        # Parsear JSON
        payload = ujson.loads(msg)
        
        # Validar estructura
        if 'objeto' not in payload or 'confianza' not in payload:
            log("Payload sin campos requeridos", "WARN")
            return
        
        objeto = payload['objeto']
        confianza = float(payload['confianza'])
        
        log(f"Objeto: {objeto}")
        log(f"Confianza: {confianza:.2%}")
        
        # VALIDACIÓN DE UMBRAL
        if confianza < CONFIDENCE_THRESHOLD:
            log(f"⚠ Confianza {confianza:.2%} < {CONFIDENCE_THRESHOLD:.0%} - IGNORADO", "WARN")
            return
        
        # VALIDACIÓN DE CLASE
        if "pistachio" not in objeto.lower():
            log(f"Objeto '{objeto}' no es pistacho - IGNORADO")
            return
        
        # ACTIVAR ARDUINO
        log(f"🎯 PISTACHO VÁLIDO detectado ({confianza:.2%})")
        log("Enviando comando ACTIVATE al Arduino...")
        
        if send_to_arduino(b'A'):
            blink_led(2, 100)  # Parpadeo de confirmación
            
            # Esperar respuesta
            if wait_arduino_response(b'D', ARDUINO_TIMEOUT):
                log("✓ Arduino completó secuencia exitosamente")
                blink_success()
            else:
                log("✗ Arduino no respondió", "ERROR")
                blink_error()
        else:
            log("✗ Error enviando comando a Arduino", "ERROR")
            blink_error()
        
        log(f"{'='*40}\n")
        
    except ValueError as e:
        log(f"Error parseando JSON: {e}", "ERROR")
    except Exception as e:
        log(f"Error en callback: {e}", "ERROR")
        blink_error()

# ========== HEARTBEAT ==========
def check_heartbeat():
    """Verifica conexiones periódicamente"""
    global last_heartbeat, wlan, mqtt_client
    
    current_time = time.ticks_ms()
    
    if time.ticks_diff(current_time, last_heartbeat) >= HEARTBEAT_INTERVAL:
        log("❤ Heartbeat - Verificando conexiones...")
        
        # Verificar WiFi
        if not wlan.isconnected():
            log("WiFi desconectado - Reconectando...", "WARN")
            if not connect_wifi():
                return False
        
        # Verificar MQTT con ping
        try:
            mqtt_client.ping()
            log("✓ Conexiones OK")
        except:
            log("MQTT desconectado - Reconectando...", "WARN")
            mqtt_client = connect_mqtt()
            if mqtt_client is None:
                return False
        
        last_heartbeat = current_time
        blink_led(1, 50)  # Parpadeo corto de heartbeat
    
    return True

# ========== LOOP PRINCIPAL ==========
def main():
    """Función principal del sistema"""
    global mqtt_client, wlan, last_heartbeat, reconnect_count
    
    log("="*50)
    log("Sistema Pico W - Control de Servo con IA")
    log(f"Umbral de confianza: {CONFIDENCE_THRESHOLD:.0%}")
    log("="*50)
    
    # Inicializar UART
    if not init_uart():
        log("FALLO CRÍTICO: No se pudo inicializar UART", "ERROR")
        blink_error()
        time.sleep(5)
        reset()  # Reiniciar Pico
    
    # Conectar WiFi
    if not connect_wifi():
        log("FALLO: No se pudo conectar a WiFi", "ERROR")
        if reconnect_count >= MAX_RECONNECT_ATTEMPTS:
            log("Máximo de reintentos alcanzado - Reiniciando...", "ERROR")
            time.sleep(5)
            reset()
        time.sleep_ms(RECONNECT_DELAY)
    
    # Conectar MQTT
    mqtt_client = connect_mqtt()
    if mqtt_client is None:
        log("FALLO: No se pudo conectar a MQTT", "ERROR")
        time.sleep_ms(RECONNECT_DELAY)
    
    last_heartbeat = time.ticks_ms()
    
    log("\n🚀 Sistema iniciado - Esperando detecciones...\n")
    blink_led(3, 200)  # 3 parpadeos de inicio
    
    # Loop infinito
    while True:
        try:
            # Verificar heartbeat
            if not check_heartbeat():
                log("Heartbeat falló - Reintentando...", "WARN")
                time.sleep_ms(RECONNECT_DELAY)
                continue
            
            # Procesar mensajes MQTT
            if mqtt_client:
                try:
                    mqtt_client.check_msg()
                except OSError as e:
                    log(f"Error MQTT: {e}", "ERROR")
                    mqtt_client = connect_mqtt()
            
            # Delay corto
            time.sleep_ms(100)
            
        except KeyboardInterrupt:
            log("\n⚠ Interrupción por usuario")
            break
            
        except Exception as e:
            log(f"Error en loop principal: {e}", "ERROR")
            blink_error()
            time.sleep_ms(1000)
    
    # Limpieza
    log("Cerrando conexiones...")
    if mqtt_client:
        try:
            mqtt_client.disconnect()
        except:
            pass
    
    if wlan:
        wlan.disconnect()
    
    log("Sistema detenido")

# ========== INICIO ==========
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"EXCEPCIÓN CRÍTICA: {e}", "ERROR")
        blink_error()
        time.sleep(10)
        reset()  # Reiniciar en caso de error crítico
