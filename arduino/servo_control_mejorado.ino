/*
 * servo_control_mejorado.ino - Arduino Uno
 * 
 * SOLUCIONES IMPLEMENTADAS:
 * 1. Watchdog timer para evitar bloqueos
 * 2. Flush del buffer serial para evitar comandos acumulados
 * 3. LED de estado para debugging visual
 * 4. Timeout en espera de comandos
 * 5. Confirmación mejorada con ACK
 * 
 * Conexiones:
 * - Arduino TX (Pin 1) -> Level Converter HV2
 * - Arduino RX (Pin 0) -> Level Converter HV1
 * - Servo Signal -> Pin 9
 * - Servo VCC -> Fuente externa 5V (NO al Arduino!)
 * - Servo GND -> GND común (Arduino + Fuente + Level Converter)
 * - LED interno -> Pin 13 (built-in)
 * 
 * Protocolo mejorado:
 * - Recibe 'A' -> Activa servo -> Responde 'D' (Done)
 * - Recibe 'R' -> Reset -> Responde 'K' (OK)
 * - Recibe 'S' -> Status -> Responde estado actual
 */

#include <Servo.h>
#include <avr/wdt.h>  // Watchdog timer para evitar bloqueos

// ========== CONFIGURACIÓN ==========
Servo myServo;
const int SERVO_PIN = 9;
const int LED_PIN = LED_BUILTIN;  // Pin 13

// Posiciones del servo
const int POS_INICIAL = 0;
const int POS_ACTIVO = 180;

// Tiempos (milisegundos)
const unsigned long SERVO_DELAY = 500;        // Delay entre movimientos
const unsigned long SERIAL_TIMEOUT = 100;     // Timeout lectura serial
const unsigned long HEARTBEAT_INTERVAL = 5000; // Intervalo de "latido" (opcional)

// Comandos del protocolo
const char CMD_ACTIVATE = 'A';  // Activar servo
const char CMD_RESET = 'R';     // Reset a posición inicial
const char CMD_STATUS = 'S';    // Solicitar estado

// Respuestas
const char RESP_DONE = 'D';     // Secuencia completada
const char RESP_OK = 'K';       // Comando OK
const char RESP_ERROR = 'E';    // Error

// Estados
enum Estado {
  IDLE,
  EJECUTANDO,
  ERROR_STATE
};

Estado estadoActual = IDLE;
unsigned long lastHeartbeat = 0;

// ========== SETUP ==========
void setup() {
  // Deshabilitar watchdog al inicio (por si quedó activo)
  wdt_disable();
  
  // Configurar LED
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // Inicializar serial con timeout
  Serial.begin(9600);
  Serial.setTimeout(SERIAL_TIMEOUT);
  
  // Esperar estabilización del puerto serial
  delay(100);
  
  // Limpiar buffer serial
  while (Serial.available() > 0) {
    Serial.read();
  }
  
  // Inicializar servo
  myServo.attach(SERVO_PIN);
  myServo.write(POS_INICIAL);
  delay(500);  // Esperar que llegue a posición
  
  // Habilitar watchdog (8 segundos)
  wdt_enable(WDTO_8S);
  
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
  
  estadoActual = IDLE;
  lastHeartbeat = millis();
}

// ========== LOOP ==========
void loop() {
  // Resetear watchdog (mantener sistema vivo)
  wdt_reset();
  
  // Heartbeat opcional (para debugging)
  unsigned long currentMillis = millis();
  if (currentMillis - lastHeartbeat >= HEARTBEAT_INTERVAL) {
    // Parpadeo corto cada 5 segundos
    digitalWrite(LED_PIN, HIGH);
    delay(50);
    digitalWrite(LED_PIN, LOW);
    lastHeartbeat = currentMillis;
  }
  
  // Procesar comandos seriales
  if (Serial.available() > 0) {
    char comando = Serial.read();
    
    // Limpiar buffer de entrada (evitar acumulación)
    delay(10);
    while (Serial.available() > 0) {
      Serial.read();
    }
    
    // Procesar comando
    procesarComando(comando);
  }
  
  // Delay corto para no saturar CPU
  delay(10);
}

// ========== FUNCIONES ==========

void procesarComando(char cmd) {
  Serial.print("CMD_RX: ");
  Serial.println(cmd);
  
  switch (cmd) {
    case CMD_ACTIVATE:
      if (estadoActual == IDLE) {
        ejecutarSecuenciaServo();
      } else {
        Serial.println("WARN: Sistema ocupado");
        Serial.write(RESP_ERROR);
      }
      break;
      
    case CMD_RESET:
      resetearServo();
      break;
      
    case CMD_STATUS:
      enviarEstado();
      break;
      
    default:
      Serial.print("ERR: Comando desconocido: ");
      Serial.println(cmd);
      Serial.write(RESP_ERROR);
      break;
  }
  
  Serial.flush();
}

void ejecutarSecuenciaServo() {
  estadoActual = EJECUTANDO;
  digitalWrite(LED_PIN, HIGH);  // LED ON durante ejecución
  
  Serial.println("SERVO_START");
  
  // Secuencia: 0° -> 180° -> 0°
  Serial.println("POS: 0");
  myServo.write(POS_INICIAL);
  wdt_reset();  // Reset watchdog durante operación larga
  delay(SERVO_DELAY);
  
  Serial.println("POS: 180");
  myServo.write(POS_ACTIVO);
  wdt_reset();
  delay(SERVO_DELAY);
  
  Serial.println("POS: 0");
  myServo.write(POS_INICIAL);
  wdt_reset();
  delay(SERVO_DELAY);
  
  Serial.println("SERVO_DONE");
  
  // Enviar confirmación
  Serial.write(RESP_DONE);
  Serial.flush();
  
  digitalWrite(LED_PIN, LOW);  // LED OFF
  estadoActual = IDLE;
}

void resetearServo() {
  Serial.println("RESET");
  myServo.write(POS_INICIAL);
  delay(SERVO_DELAY);
  estadoActual = IDLE;
  digitalWrite(LED_PIN, LOW);
  
  Serial.write(RESP_OK);
  Serial.flush();
}

void enviarEstado() {
  Serial.print("STATUS: ");
  
  switch (estadoActual) {
    case IDLE:
      Serial.println("IDLE");
      break;
    case EJECUTANDO:
      Serial.println("EJECUTANDO");
      break;
    case ERROR_STATE:
      Serial.println("ERROR");
      break;
    default:
      Serial.println("DESCONOCIDO");
      break;
  }
  
  Serial.print("SERVO_POS: ");
  Serial.println(myServo.read());
  
  Serial.write(RESP_OK);
  Serial.flush();
}
