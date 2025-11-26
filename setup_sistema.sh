#!/bin/bash
# setup_sistema.sh
# Script de configuración automática para el sistema de detección de pistachos
# Ejecutar en Raspberry Pi 5

set -e  # Salir si hay errores

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  SETUP AUTOMÁTICO - Sistema Detección de Pistachos          ║"
echo "║  Raspberry Pi 5 + Arduino Uno + Pico W                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar que se ejecuta en RPi5
if [ ! -f /etc/rpi-issue ]; then
    echo -e "${YELLOW}⚠ Advertencia: No parece ser un Raspberry Pi${NC}"
    read -p "¿Continuar de todas formas? (s/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

echo -e "${BLUE}[1/7] Actualizando sistema...${NC}"
sudo apt update
echo -e "${GREEN}✓ Sistema actualizado${NC}"

echo -e "\n${BLUE}[2/7] Instalando dependencias del sistema...${NC}"
sudo apt install -y \
    python3-pip \
    python3-opencv \
    mosquitto-clients \
    minicom \
    curl \
    git

echo -e "${GREEN}✓ Dependencias instaladas${NC}"

echo -e "\n${BLUE}[3/7] Instalando paquetes Python...${NC}"
pip3 install --upgrade pip
pip3 install pyserial paho-mqtt numpy ultralytics opencv-python

echo -e "${GREEN}✓ Paquetes Python instalados${NC}"

echo -e "\n${BLUE}[4/7] Configurando permisos de usuario...${NC}"
CURRENT_USER=${SUDO_USER:-$USER}

# Agregar usuario a grupos necesarios
if groups $CURRENT_USER | grep -q '\bdialout\b'; then
    echo -e "${GREEN}✓ Usuario ya está en grupo 'dialout'${NC}"
else
    echo -e "${YELLOW}Agregando usuario al grupo 'dialout'...${NC}"
    sudo usermod -a -G dialout $CURRENT_USER
    echo -e "${GREEN}✓ Usuario agregado a 'dialout'${NC}"
fi

if groups $CURRENT_USER | grep -q '\btty\b'; then
    echo -e "${GREEN}✓ Usuario ya está en grupo 'tty'${NC}"
else
    echo -e "${YELLOW}Agregando usuario al grupo 'tty'...${NC}"
    sudo usermod -a -G tty $CURRENT_USER
    echo -e "${GREEN}✓ Usuario agregado a 'tty'${NC}"
fi

echo -e "\n${BLUE}[5/7] Verificando/instalando Docker...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker ya está instalado${NC}"
else
    echo -e "${YELLOW}Instalando Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Agregar usuario a grupo docker
    sudo usermod -a -G docker $CURRENT_USER
    echo -e "${GREEN}✓ Docker instalado${NC}"
fi

echo -e "\n${BLUE}[6/7] Configurando Mosquitto MQTT...${NC}"
MOSQUITTO_DIR="$HOME/mosquitto"

if [ -d "$MOSQUITTO_DIR" ]; then
    echo -e "${YELLOW}Directorio mosquitto ya existe${NC}"
else
    mkdir -p $MOSQUITTO_DIR/{config,data,log}
    echo -e "${GREEN}✓ Directorios creados${NC}"
fi

# Crear archivo de configuración
cat > $MOSQUITTO_DIR/config/mosquitto.conf <<EOF
# mosquitto.conf - Configuración para desarrollo
listener 1883
allow_anonymous true
persistence true
persistence_location /mosquitto/data/
log_dest file /mosquitto/log/mosquitto.log
log_type all
EOF

echo -e "${GREEN}✓ Configuración de Mosquitto creada${NC}"

# Verificar si el contenedor ya existe
if sudo docker ps -a | grep -q mosquitto; then
    echo -e "${YELLOW}Contenedor mosquitto ya existe${NC}"
    
    # Verificar si está corriendo
    if sudo docker ps | grep -q mosquitto; then
        echo -e "${GREEN}✓ Mosquitto está corriendo${NC}"
    else
        echo -e "${YELLOW}Iniciando contenedor mosquitto...${NC}"
        sudo docker start mosquitto
        echo -e "${GREEN}✓ Mosquitto iniciado${NC}"
    fi
else
    echo -e "${YELLOW}Creando contenedor mosquitto...${NC}"
    sudo docker pull eclipse-mosquitto:latest
    
    sudo docker run -d \
        --name mosquitto \
        --restart unless-stopped \
        -p 1883:1883 \
        -v $MOSQUITTO_DIR/config:/mosquitto/config \
        -v $MOSQUITTO_DIR/data:/mosquitto/data \
        -v $MOSQUITTO_DIR/log:/mosquitto/log \
        eclipse-mosquitto:latest
    
    echo -e "${GREEN}✓ Contenedor mosquitto creado y iniciado${NC}"
fi

echo -e "\n${BLUE}[7/7] Deshabilitando ModemManager (puede interferir con Arduino)...${NC}"
if systemctl is-active --quiet ModemManager; then
    sudo systemctl stop ModemManager
    sudo systemctl disable ModemManager
    echo -e "${GREEN}✓ ModemManager deshabilitado${NC}"
else
    echo -e "${GREEN}✓ ModemManager ya está deshabilitado${NC}"
fi

echo -e "\n${BLUE}Instalando arduino-cli (opcional)...${NC}"
if command -v arduino-cli &> /dev/null; then
    echo -e "${GREEN}✓ arduino-cli ya está instalado${NC}"
else
    read -p "¿Deseas instalar arduino-cli para cargar sketches? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/local/bin sh
        
        # Configurar arduino-cli
        arduino-cli config init
        arduino-cli core update-index
        arduino-cli core install arduino:avr
        
        echo -e "${GREEN}✓ arduino-cli instalado${NC}"
    else
        echo -e "${YELLOW}⊘ arduino-cli no instalado (puedes usar Arduino IDE)${NC}"
    fi
fi

# Resumen final
echo -e "\n${GREEN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    ✓ INSTALACIÓN COMPLETA                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${BLUE}Información del sistema:${NC}"
echo "  Usuario: $CURRENT_USER"
echo "  Grupos: $(groups $CURRENT_USER)"
echo ""

echo -e "${BLUE}IP del Raspberry Pi 5:${NC}"
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo "  $IP_ADDRESS"
echo ""
echo -e "${YELLOW}⚠ Actualiza este valor en picow/secrets.py:${NC}"
echo "  MQTT_BROKER = \"$IP_ADDRESS\""
echo ""

echo -e "${BLUE}Servicios:${NC}"
echo "  MQTT Broker: $(sudo docker ps | grep mosquitto &> /dev/null && echo '✓ Corriendo' || echo '✗ No corriendo')"
echo ""

echo -e "${BLUE}Puertos seriales detectados:${NC}"
if ls /dev/ttyUSB* &> /dev/null || ls /dev/ttyACM* &> /dev/null; then
    ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | awk '{print "  " $NF " (" $3 ":" $4 ")"}'
else
    echo "  Ninguno (conecta el Arduino y vuelve a verificar)"
fi
echo ""

echo -e "${YELLOW}⚠ IMPORTANTE: Cambios de grupo requieren reiniciar sesión${NC}"
echo "  Opciones:"
echo "    1. Cerrar sesión y volver a entrar"
echo "    2. Ejecutar: newgrp dialout"
echo "    3. Reiniciar el sistema"
echo ""

echo -e "${BLUE}Próximos pasos:${NC}"
echo "  1. Editar picow/secrets.py con tus credenciales WiFi"
echo "  2. Cargar servo_control_mejorado.ino en Arduino"
echo "  3. Cargar main_mejorado.py en Pico W (con Thonny)"
echo "  4. Ejecutar: python3 rpi5/diagnostico_arduino.py"
echo "  5. Ejecutar: python3 rpi5/videoPublicTopic_mejorado.py"
echo ""

echo -e "${GREEN}¡Sistema listo para usar!${NC}"
