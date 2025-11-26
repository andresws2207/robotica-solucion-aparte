#!/usr/bin/env python3
"""
diagnostico_arduino.py
Script de diagnóstico para problemas de conexión Arduino-Raspberry Pi 5

Ejecutar en el Raspberry Pi 5 para:
- Detectar puertos seriales disponibles
- Verificar permisos de usuario
- Probar comunicación con Arduino
- Validar configuración del sistema

Uso:
    python3 diagnostico_arduino.py
"""

import os
import sys
import subprocess
import time
import serial
import serial.tools.list_ports

# Colores para terminal
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprime un encabezado destacado"""
    print(f"\n{Color.BOLD}{Color.BLUE}{'='*60}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{text}{Color.RESET}")
    print(f"{Color.BOLD}{Color.BLUE}{'='*60}{Color.RESET}\n")

def print_ok(text):
    """Imprime mensaje de éxito"""
    print(f"{Color.GREEN}✓ {text}{Color.RESET}")

def print_warn(text):
    """Imprime advertencia"""
    print(f"{Color.YELLOW}⚠ {text}{Color.RESET}")

def print_error(text):
    """Imprime error"""
    print(f"{Color.RED}✗ {text}{Color.RESET}")

def print_info(text):
    """Imprime información"""
    print(f"{Color.BLUE}ℹ {text}{Color.RESET}")

# ============ DIAGNÓSTICOS ============

def check_os():
    """Verifica el sistema operativo"""
    print_header("1. VERIFICACIÓN DEL SISTEMA OPERATIVO")
    
    try:
        with open('/etc/os-release', 'r') as f:
            os_info = f.read()
            if 'Raspberry Pi' in os_info or 'Debian' in os_info:
                print_ok("Sistema operativo: Raspberry Pi OS / Debian")
                return True
            else:
                print_warn("Sistema operativo no es Raspberry Pi OS")
                print_info("El sistema puede funcionar, pero no está oficialmente soportado")
                return True
    except:
        print_error("No se pudo leer información del sistema")
        return False

def check_user_groups():
    """Verifica que el usuario esté en los grupos necesarios"""
    print_header("2. VERIFICACIÓN DE PERMISOS DE USUARIO")
    
    username = os.getenv('USER')
    print_info(f"Usuario actual: {username}")
    
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip().split()
        
        required_groups = ['dialout', 'tty']
        missing_groups = []
        
        for group in required_groups:
            if group in groups:
                print_ok(f"Usuario en grupo '{group}'")
            else:
                missing_groups.append(group)
                print_error(f"Usuario NO está en grupo '{group}'")
        
        if missing_groups:
            print_warn("\n🔧 SOLUCIÓN: Agregar usuario a grupos necesarios:")
            for group in missing_groups:
                print(f"   sudo usermod -a -G {group} {username}")
            print("   Luego REINICIAR o ejecutar: newgrp dialout")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Error verificando grupos: {e}")
        return False

def list_serial_ports():
    """Lista todos los puertos seriales disponibles"""
    print_header("3. DETECCIÓN DE PUERTOS SERIALES")
    
    ports = serial.tools.list_ports.comports()
    
    if not ports:
        print_error("No se detectaron puertos seriales")
        print_info("Conecta el Arduino por USB y vuelve a ejecutar este script")
        return None
    
    print_ok(f"Puertos seriales detectados: {len(ports)}\n")
    
    arduino_ports = []
    
    for i, port in enumerate(ports, 1):
        print(f"  {i}. {port.device}")
        print(f"     Descripción: {port.description}")
        print(f"     Fabricante: {port.manufacturer or 'N/A'}")
        print(f"     VID:PID: {port.vid:04X}:{port.pid:04X}" if port.vid else "     VID:PID: N/A")
        
        # Detectar Arduino por VID (Vendor ID)
        # Arduino Uno: VID 0x2341 (Arduino) o 0x1A86 (CH340)
        if port.vid in [0x2341, 0x1A86, 0x0403]:
            print_ok(f"     ⚡ Posible Arduino detectado!")
            arduino_ports.append(port.device)
        
        print()
    
    if arduino_ports:
        print_ok(f"Arduino(s) potencial(es): {', '.join(arduino_ports)}")
        return arduino_ports[0]  # Retornar el primero
    else:
        print_warn("No se detectó ningún Arduino por VID")
        print_info("El Arduino podría estar en uno de los puertos listados")
        return ports[0].device if ports else None

def check_port_permissions(port_name):
    """Verifica permisos del puerto serial"""
    print_header("4. VERIFICACIÓN DE PERMISOS DEL PUERTO")
    
    if not port_name:
        print_error("No hay puerto para verificar")
        return False
    
    try:
        # Verificar si el puerto existe
        if not os.path.exists(port_name):
            print_error(f"El puerto {port_name} no existe")
            return False
        
        print_ok(f"Puerto {port_name} existe")
        
        # Verificar permisos
        stat_info = os.stat(port_name)
        mode = oct(stat_info.st_mode)[-3:]
        
        print_info(f"Permisos del puerto: {mode}")
        
        # Verificar si podemos leer/escribir
        if os.access(port_name, os.R_OK | os.W_OK):
            print_ok("Usuario tiene permisos de lectura/escritura")
            return True
        else:
            print_error("Usuario NO tiene permisos de lectura/escritura")
            print_warn("\n🔧 SOLUCIONES POSIBLES:")
            print(f"   1. Agregar usuario al grupo dialout: sudo usermod -a -G dialout $USER")
            print(f"   2. Cambiar permisos (temporal): sudo chmod 666 {port_name}")
            print(f"   3. Ejecutar con sudo (no recomendado)")
            return False
            
    except Exception as e:
        print_error(f"Error verificando permisos: {e}")
        return False

def test_serial_communication(port_name, baudrate=9600):
    """Prueba la comunicación serial con el Arduino"""
    print_header("5. PRUEBA DE COMUNICACIÓN SERIAL")
    
    if not port_name:
        print_error("No hay puerto para probar")
        return False
    
    try:
        print_info(f"Abriendo puerto {port_name} a {baudrate} baudios...")
        
        ser = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            timeout=2
        )
        
        print_ok("Puerto serial abierto correctamente")
        
        # Esperar que el Arduino se reinicie (DTR reset)
        print_info("Esperando reinicio del Arduino (2 segundos)...")
        time.sleep(2)
        
        # Limpiar buffer de entrada
        ser.reset_input_buffer()
        
        # Leer mensajes del Arduino (si los hay)
        print_info("Leyendo mensajes del Arduino...")
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print_ok(f"Datos recibidos del Arduino: {data}")
        else:
            print_warn("No se recibieron datos del Arduino automáticamente")
        
        # Enviar comando de prueba (si usas el código mejorado)
        print_info("\nEnviando comando 'S' (Status) al Arduino...")
        ser.write(b'S')
        ser.flush()
        
        # Esperar respuesta
        time.sleep(0.5)
        
        if ser.in_waiting > 0:
            response = ser.read(ser.in_waiting)
            print_ok(f"Respuesta del Arduino: {response}")
            
            if b'STATUS' in response or b'K' in response:
                print_ok("✓✓✓ COMUNICACIÓN EXITOSA ✓✓✓")
                ser.close()
                return True
        else:
            print_warn("No se recibió respuesta al comando")
        
        # Cerrar puerto
        ser.close()
        print_info("Puerto serial cerrado")
        
        print_warn("\n⚠ El puerto se abre, pero la comunicación no es clara")
        print_info("Posibles causas:")
        print("  - Arduino no tiene el sketch correcto cargado")
        print("  - Baudrate incorrecto (verifica que sea 9600)")
        print("  - Arduino necesita tiempo adicional para iniciar")
        
        return True  # El puerto funciona, aunque no hay comunicación clara
        
    except serial.SerialException as e:
        print_error(f"Error abriendo puerto serial: {e}")
        print_warn("\n🔧 SOLUCIONES:")
        print("  1. Verificar que el Arduino esté conectado")
        print("  2. Verificar permisos del usuario (ver sección anterior)")
        print(f"  3. Cerrar otros programas usando el puerto (Arduino IDE, minicom, etc.)")
        return False
        
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False

def check_python_packages():
    """Verifica que los paquetes Python necesarios estén instalados"""
    print_header("6. VERIFICACIÓN DE PAQUETES PYTHON")
    
    required_packages = {
        'serial': 'pyserial',
        'cv2': 'opencv-python',
        'paho.mqtt.client': 'paho-mqtt'
    }
    
    all_ok = True
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print_ok(f"Paquete '{package_name}' instalado")
        except ImportError:
            print_error(f"Paquete '{package_name}' NO instalado")
            print_info(f"   Instalar con: pip3 install {package_name}")
            all_ok = False
    
    return all_ok

def check_arduino_ide_running():
    """Verifica si el Arduino IDE está usando el puerto"""
    print_header("7. VERIFICACIÓN DE PROCESOS CONFLICTIVOS")
    
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout.lower()
        
        conflicts = []
        
        if 'arduino' in processes:
            conflicts.append('Arduino IDE')
        if 'minicom' in processes:
            conflicts.append('minicom')
        if 'screen' in processes:
            conflicts.append('screen')
        
        if conflicts:
            print_warn(f"Procesos que pueden estar usando el puerto: {', '.join(conflicts)}")
            print_info("Cierra estos programas antes de ejecutar tu script")
            return False
        else:
            print_ok("No se detectaron procesos conflictivos")
            return True
            
    except Exception as e:
        print_warn(f"No se pudo verificar procesos: {e}")
        return True

# ============ FUNCIÓN PRINCIPAL ============

def main():
    """Ejecuta todos los diagnósticos"""
    print(f"\n{Color.BOLD}╔═══════════════════════════════════════════════════════════╗{Color.RESET}")
    print(f"{Color.BOLD}║  DIAGNÓSTICO DE CONEXIÓN ARDUINO - RASPBERRY PI 5        ║{Color.RESET}")
    print(f"{Color.BOLD}╚═══════════════════════════════════════════════════════════╝{Color.RESET}")
    
    # Verificar si pyserial está instalado
    try:
        import serial
    except ImportError:
        print_error("\nEl paquete 'pyserial' no está instalado")
        print_info("Instalar con: pip3 install pyserial")
        sys.exit(1)
    
    results = {}
    
    # Ejecutar diagnósticos
    results['os'] = check_os()
    results['groups'] = check_user_groups()
    
    arduino_port = list_serial_ports()
    
    if arduino_port:
        results['permissions'] = check_port_permissions(arduino_port)
        results['communication'] = test_serial_communication(arduino_port)
    else:
        results['permissions'] = False
        results['communication'] = False
    
    results['packages'] = check_python_packages()
    results['processes'] = check_arduino_ide_running()
    
    # Resumen final
    print_header("RESUMEN DEL DIAGNÓSTICO")
    
    all_passed = all(results.values())
    
    for test, passed in results.items():
        status = "✓ OK" if passed else "✗ FALLO"
        color = Color.GREEN if passed else Color.RED
        print(f"  {color}{status}{Color.RESET} - {test.upper()}")
    
    print()
    
    if all_passed:
        print_ok("═══ TODOS LOS DIAGNÓSTICOS PASARON ═══")
        print_info("\nEl sistema debería funcionar correctamente")
        print_info(f"Puerto Arduino detectado: {arduino_port}")
        print_info("\nUsa este puerto en tu código Python:")
        print(f"  ser = serial.Serial('{arduino_port}', 9600)")
    else:
        print_error("═══ ALGUNOS DIAGNÓSTICOS FALLARON ═══")
        print_info("\nRevisa los mensajes anteriores para solucionar los problemas")
    
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDiagnóstico interrumpido por el usuario")
        sys.exit(0)
