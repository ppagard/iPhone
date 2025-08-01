#!/bin/bash

# Startskript för utgiftshanteraren

echo "Startar Utgiftshanteraren..."

# Kontrollera om virtuell miljö finns
if [ ! -d "venv" ]; then
    echo "Skapar virtuell miljö..."
    python3 -m venv venv
fi

# Aktivera virtuell miljö och installera beroenden
echo "Aktiverar virtuell miljö och installerar beroenden..."
source venv/bin/activate
pip install -r requirements.txt

# Kör programmet
echo "Startar programmet..."
python main.py