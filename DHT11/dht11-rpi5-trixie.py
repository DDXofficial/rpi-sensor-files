# new DHT11 script for Raspberry Pi 5 (Gemini 2.5 Pro)
# to add: logging (CSV, JSON, et al.)

"""
testing environment: Raspberry Pi 5
                 OS: Raspberry Pi OS / Debian 13 (trixie)
             Python: 3.13.x
"""

# core libraries
import time
import board
import adafruit_dht
import sys

# new imports
from datetime import datetime
import os
import subprocess
import signal
import logging
import csv
import json

# --- Configuration ---
# The GPIO pin number the DHT11 data pin is connected to.
# This uses the board numbering scheme (e.g., board.D4 is GPIO4).
# You can change this to any other valid GPIO pin.

DHT_PIN = board.D4 # GPIO pin 7 on Raspberry Pi 5

# --- Initialization ---
# Initialize the DHT sensor.
# For a DHT22 sensor, you would use adafruit_dht.DHT22.
# The 'use_pulseio=False' is important for Raspberry Pi 5 with libgpiod.

try:
    dht_sensor = adafruit_dht.DHT11(DHT_PIN, use_pulseio=False)
except ImportError:
    print("Error: A required library is not installed.")
    print("Please run: pip install adafruit-circuitpython-dht")
    sys.exit()
except Exception as e:
    print(f"An unexpected error occurred during sensor initialization: {e}")
    sys.exit()

# --- Logging (WIP) ---

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("dht11_sensor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# --- Main Loop ---
print("Sensor initialized. Starting readings...")
print("Press Ctrl+C to exit.")

while True:
    try:
        # Attempt to read from the sensor
        temperature_c = dht_sensor.temperature
        humidity = dht_sensor.humidity

        if humidity is not None and temperature_c is not None:
            temperature_f = temperature_c * (9 / 5) + 32
            print(f"{datetime.now()} - ", end="")
            print(f"Temperature: {temperature_c:.1f}°C ({temperature_f:.1f}°F) | Humidity: {humidity}%")
        else:
            print("Failed to retrieve data from sensor. Retrying...")

    # Time delay between readings (minimum 2 seconds for DHT11)
    # Set to 3 seconds for more consistent results
        time.sleep(3.0)

    except RuntimeError as error:
        # Errors happen fairly often with DHT sensors due to timing.
        # This is a normal part of their operation.
        print(f"Sensor reading failed: {error.args[0]}. Retrying...")
    except Exception as error:
        # Handle other potential errors and perform a clean exit.
        dht_sensor.exit()
        raise error
    except KeyboardInterrupt:
        print("")
        dht_sensor.exit()
        sys.exit(0)

    

