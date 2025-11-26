/*
 * servo_control_simple.ino - Arduino Uno
 * 
 * SOLUCIÓN SIMPLE SIN WATCHDOG
 * Controla servomotor basado en comandos seriales desde RPi5
 * 
 * Conexiones:
 * - Servo Signal -> Pin 9
 * - Servo VCC -> Fuente externa 5V (¡NO al Arduino!)
 * - Servo GND -> GND común (Arduino + Fuente)
 * - LED interno -> Pin 13 (automático)
 * 
 * Comandos:
 * - 'A' -> Mover a 180° (pistacho detectado)
 * - 'R' -> Mover a 0° (reset/sin detección)
 * - 'S' -> Enviar estado actual
 */

#include <Servo.h>

// ========== CONFIGURACIÓN ==========
Servo myServo;
const int SERVO_PIN = 9;
const int LED_PIN = LED_BUILTIN;  // Pin 13

// Posiciones del servo
const int POS_IZQUIERDA = 0;      // Sin detección
const int POS_DERECHA = 180;      // Pistacho detectado

// Tiempos
const unsigned long SERVO_DELAY = 500;  // Delay entre movimientos (ms)

// Comandos
const char CMD_ACTIVATE = 'A';    // Mover a derecha (180°)
const char CMD_RESET = 'R';       // Mover a izquierda (0°)
const char CMD_STATUS = 'S';      // Estado

// Respuestas
const char RESP_DONE = 'D';       // Comando completado
const char RESP_OK = 'K';         // OK

// Variables de estado
int posicionActual = POS_IZQUIERDA;

// ========== SETUP ==========
void setup() {
  // Configurar LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Inicializar serial
  Serial.begin(9600);
  
  // Esperar estabilización
  delay(500);
  
  // Limpiar buffer serial
  while (Serial.available() > 0) {
    Serial.read();
  }
  
  // Inicializar servo
  myServo.attach(SERVO_PIN);
  myServo.write(POS_IZQUIERDA);
  posicionActual = POS_IZQUIERDA;
  delay(1000);  // Esperar que llegue a posición
  
  // Señal de inicio (3 parpadeos)
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
  
  // Mensaje de inicio
  Serial.println("ARDUINO_READY");
  Serial.flush();
}

// ========== LOOP ==========
void loop() {
  // Procesar comandos seriales
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    // Limpiar buffer (evitar acumulación)
    delay(10);
    while (Serial.available() > 0) {
      Serial.read();
    }
    
    // Procesar comando
    procesarComando(comando);
  }
  
  delay(10);  // Pequeño delay para no saturar
}

// ========== FUNCIONES ==========

void procesarComando(char cmd) {
  Serial.print("CMD_RX: ");
  Serial.println(cmd);
  
  switch (cmd) {
    case CMD_ACTIVATE:
      moverDerecha();
      break;
      
    case CMD_RESET:
      moverIzquierda();
      break;
      
    case CMD_STATUS:
      enviarEstado();
      break;
      
    default:
      Serial.print("ERR: Comando desconocido: ");
      Serial.println(cmd);
      break;
  }
  
  Serial.flush();
}

void moverDerecha() {
  // Mover a 180° (pistacho detectado)
  digitalWrite(LED_PIN, HIGH);
  
  Serial.println("MOVER_DERECHA_START");
  Serial.print("POS_ACTUAL: ");
  Serial.println(posicionActual);
  Serial.print("POS_DESTINO: ");
  Serial.println(POS_DERECHA);
  
  myServo.write(POS_DERECHA);
  posicionActual = POS_DERECHA;
  delay(SERVO_DELAY);
  
  Serial.println("MOVER_DERECHA_DONE");
  Serial.write(RESP_DONE);
  Serial.flush();
  
  digitalWrite(LED_PIN, LOW);
}

void moverIzquierda() {
  // Mover a 0° (sin detección)
  digitalWrite(LED_PIN, HIGH);
  
  Serial.println("MOVER_IZQUIERDA_START");
  Serial.print("POS_ACTUAL: ");
  Serial.println(posicionActual);
  Serial.print("POS_DESTINO: ");
  Serial.println(POS_IZQUIERDA);
  
  myServo.write(POS_IZQUIERDA);
  posicionActual = POS_IZQUIERDA;
  delay(SERVO_DELAY);
  
  Serial.println("MOVER_IZQUIERDA_DONE");
  Serial.write(RESP_OK);
  Serial.flush();
  
  digitalWrite(LED_PIN, LOW);
}

void enviarEstado() {
  Serial.print("STATUS: IDLE - POS: ");
  Serial.println(posicionActual);
  Serial.write(RESP_OK);
  Serial.flush();
}
