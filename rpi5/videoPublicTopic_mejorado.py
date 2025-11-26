#!/usr/bin/env python3
"""
videoPublicTopic_mejorado.py
Sistema mejorado de detección de pistachos con YOLO para Raspberry Pi 5
Soluciona problemas de conexión MQTT y comunicación con Arduino

Características:
- Detección con umbral configurable (>= 0.6 por defecto)
- Reconexión automática MQTT
- Publicación solo cuando hay detección válida
- Manejo robusto de errores de cámara
- Logs detallados para debugging
"""

import cv2
import numpy as np
import paho.mqtt.client as mqtt
import json
import os
import time
import logging
from ultralytics import YOLO
from datetime import datetime

# ============ CONFIGURACIÓN ============
# MQTT
BROKER = "localhost"  # Usa la IP del RPi5 si es desde otra máquina
PORT = 1883
TOPIC_DETECCION = "robot/pico/estado"  # Topic para enviar detecciones
QOS = 1  # Quality of Service: 0, 1 o 2

# Detección
CONFIDENCE_THRESHOLD = 0.6  # Umbral mínimo de confianza (60%)
PUB_COOLDOWN = 1.0  # Segundos entre publicaciones (evita spam)

# Cámara
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS_TARGET = 15

# Logging
LOG_LEVEL = logging.INFO
LOG_FILE = "deteccion_pistachos.log"

# ============ CONFIGURACIÓN DE LOGGING ============
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============ CLASE MQTT CON RECONEXIÓN ============
class MQTTPublisher:
    """Cliente MQTT con reconexión automática"""
    
    def __init__(self, broker, port, topic):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = None
        self.connected = False
        self.reconnect_delay = 5  # segundos
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker"""
        if rc == 0:
            self.connected = True
            logger.info(f"✓ Conectado al broker MQTT en {self.broker}:{self.port}")
        else:
            self.connected = False
            logger.error(f"✗ Error de conexión MQTT. Código: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        """Callback cuando se desconecta del broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"⚠ Desconectado inesperadamente. Código: {rc}")
            
    def connect(self):
        """Conecta al broker MQTT con reintentos"""
        try:
            self.client = mqtt.Client(client_id=f"rpi5_detector_{int(time.time())}")
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            
            logger.info(f"Intentando conectar a MQTT broker {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()  # Loop en background
            
            # Esperar conexión con timeout
            timeout = 10
            start = time.time()
            while not self.connected and (time.time() - start) < timeout:
                time.sleep(0.5)
                
            if not self.connected:
                raise ConnectionError("Timeout esperando conexión MQTT")
                
            return True
            
        except Exception as e:
            logger.error(f"Error conectando a MQTT: {e}")
            return False
            
    def publish(self, payload):
        """Publica un mensaje en el topic con validación"""
        if not self.connected:
            logger.warning("No conectado a MQTT. Intentando reconectar...")
            if not self.connect():
                return False
                
        try:
            result = self.client.publish(self.topic, json.dumps(payload), qos=QOS)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"📤 MQTT publicado: {payload}")
                return True
            else:
                logger.error(f"Error publicando. Código: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Excepción publicando: {e}")
            return False
            
    def disconnect(self):
        """Desconecta del broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Desconectado de MQTT")


# ============ CLASE DETECTOR DE PISTACHOS ============
class PistachioDetector:
    """Detector de pistachos usando YOLO"""
    
    def __init__(self, model_path, confidence_threshold=0.6):
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.last_publish_time = 0
        
        # Cargar modelo
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
            
        logger.info(f"Cargando modelo YOLO desde {model_path}...")
        self.model = YOLO(model_path)
        logger.info("✓ Modelo YOLO cargado correctamente")
        
    def detect(self, frame):
        """
        Detecta pistachos en un frame
        
        Returns:
            list: Lista de detecciones [{'class': str, 'confidence': float, 'bbox': tuple}]
        """
        results = self.model(frame, verbose=False)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls)
                class_name = result.names[class_id]
                confidence = float(box.conf)
                
                # Filtrar por clase y confianza
                if "pistachio" in class_name.lower() and confidence >= self.confidence_threshold:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    detections.append({
                        'class': class_name,
                        'confidence': confidence,
                        'bbox': (x1, y1, x2, y2)
                    })
                    
        return detections
        
    def should_publish(self, cooldown=1.0):
        """Verifica si ha pasado suficiente tiempo desde la última publicación"""
        current_time = time.time()
        if current_time - self.last_publish_time >= cooldown:
            self.last_publish_time = current_time
            return True
        return False


# ============ INICIALIZACIÓN ============
def initialize_camera(index, width, height):
    """Inicializa la cámara con reintentos"""
    logger.info(f"Inicializando cámara {index}...")
    
    for attempt in range(3):
        cap = cv2.VideoCapture(index)
        
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, FPS_TARGET)
            
            # Verificar lectura
            ret, frame = cap.read()
            if ret:
                logger.info(f"✓ Cámara inicializada: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
                return cap
            else:
                cap.release()
                
        logger.warning(f"Intento {attempt + 1}/3 falló. Reintentando...")
        time.sleep(2)
        
    raise RuntimeError("No se pudo inicializar la cámara después de 3 intentos")


# ============ LOOP PRINCIPAL ============
def main():
    logger.info("="*60)
    logger.info("Sistema de Detección de Pistachos - RPi5")
    logger.info(f"Umbral de confianza: {CONFIDENCE_THRESHOLD*100}%")
    logger.info(f"Broker MQTT: {BROKER}:{PORT}")
    logger.info(f"Topic: {TOPIC_DETECCION}")
    logger.info("="*60)
    
    # Inicializar componentes
    mqtt_publisher = None
    cap = None
    detector = None
    
    try:
        # Cargar modelo
        script_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(script_dir, "best.pt")
        detector = PistachioDetector(model_path, CONFIDENCE_THRESHOLD)
        
        # Conectar MQTT
        mqtt_publisher = MQTTPublisher(BROKER, PORT, TOPIC_DETECCION)
        if not mqtt_publisher.connect():
            logger.error("No se pudo conectar a MQTT. Verifica que el broker esté corriendo:")
            logger.error("  sudo docker ps  # Verificar contenedor mosquitto")
            return
        
        # Inicializar cámara
        cap = initialize_camera(CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT)
        
        # Crear ventana
        window_name = f"Detección Pistachos (>= {int(CONFIDENCE_THRESHOLD*100)}%)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        
        logger.info("\n🚀 Sistema iniciado. Presiona 'q' para salir.\n")
        
        # Estadísticas
        frame_count = 0
        detection_count = 0
        start_time = time.time()
        
        # Loop de detección
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Error leyendo frame de cámara")
                time.sleep(0.1)
                continue
                
            frame_count += 1
            
            # Detectar pistachos
            detections = detector.detect(frame)
            
            # Dibujar detecciones
            annotated_frame = frame.copy()
            for det in detections:
                x1, y1, x2, y2 = det['bbox']
                confidence = det['confidence']
                class_name = det['class']
                
                # Dibujar bounding box
                color = (0, 255, 0)  # Verde para detección válida
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                
                # Texto con confianza
                label = f"{class_name}: {confidence:.2f}"
                cv2.putText(annotated_frame, label, (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Publicar en MQTT (con cooldown)
                if detector.should_publish(PUB_COOLDOWN):
                    payload = {
                        "objeto": class_name,
                        "confianza": round(confidence, 3),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    if mqtt_publisher.publish(payload):
                        detection_count += 1
                        logger.info(f"🎯 Detección #{detection_count}: {class_name} ({confidence:.2%})")
            
            # Mostrar FPS y estadísticas
            elapsed = time.time() - start_time
            fps = frame_count / elapsed if elapsed > 0 else 0
            
            stats_text = f"FPS: {fps:.1f} | Detecciones: {detection_count}"
            cv2.putText(annotated_frame, stats_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Mostrar frame
            cv2.imshow(window_name, annotated_frame)
            
            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("\n👋 Saliendo del sistema...")
                break
                
    except KeyboardInterrupt:
        logger.info("\n⚠ Interrupción por usuario (Ctrl+C)")
        
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}", exc_info=True)
        
    finally:
        # Limpiar recursos
        if cap:
            cap.release()
            logger.info("Cámara liberada")
            
        if mqtt_publisher:
            mqtt_publisher.disconnect()
            
        cv2.destroyAllWindows()
        
        logger.info("Sistema detenido correctamente")


if __name__ == "__main__":
    main()
