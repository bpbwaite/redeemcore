#!/bin/bash

if [ "$(whoami)" != "root" ]; then
    echo "WARN: Pi GPIO Daemon (pigpiod) cannot start without root"
    echo "WARN: Please run 'sudo pigpiod' if you plan on using IO"
else
    echo "NOTICE: Starting Pi GPIO Daemon"
    pigpiod
fi

echo "NOTICE: Getting required libraries"
echo "NOTICE: Building project"
pip install .

echo ""
echo "NOTICE: Done! Starting program"
python3 -m RedemptionCore &
