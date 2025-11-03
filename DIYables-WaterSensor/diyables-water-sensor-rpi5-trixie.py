# DIYables Water Sensor + Adafruit ADS1115 script (Gemini 2.5 Pro)
# to add: logging and such!

"""
testing environment: Raspberry Pi 5
                 OS: Raspberry Pi OS / Debian 13 (trixie)
             Python: 3.13.x (ensured compatibility with Python 3.10 for other testing environments)
"""

import time
from datetime import datetime
import board
import busio
import digitalio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# --- Configuration ---

# This is the GPIO pin powering the sensor (VCC)
SENSOR_POWER_PIN = board.D17 

# This is a placeholder. You MUST calibrate this value!
# See the calibration section below.
WATER_THRESHOLD = 4500  

# --- Setup ---

# Set up the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADC object
try:
    ads = ADS.ADS1115(i2c)
except ValueError:
    print("I2C Error: ADS1115 not found. Check your wiring!")
    exit()

# Create an analog input channel on pin A0
chan = AnalogIn(ads, 0)

# Setup the sensor power pin as an output
sensor_power = digitalio.DigitalInOut(SENSOR_POWER_PIN)
sensor_power.direction = digitalio.Direction.OUTPUT

print("Water sensor test script running.")
print("Press Ctrl+C to exit.\n")

# --- Main Loop ---

try:
    while True:
        # Power ON the sensor
        sensor_power.value = True
        
        # Wait a fraction of a second for the sensor to stabilize
        time.sleep(0.1) 
        
        # Read the raw analog value
        # The ADS1115 gives a 16-bit value (0-65535)
        raw_value = chan.value
        
        # Power OFF the sensor to prevent corrosion
        sensor_power.value = False

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Logic ---
        print(f"Time: {timestamp}")

        if raw_value > WATER_THRESHOLD:
            print(f"Sensor Value: {raw_value} - WATER DETECTED\n")
        else:
            print(f"Sensor Value: {raw_value} - Dry\n")
        
        # Wait 3 seconds before the next reading
        # (same value as DHT22 script)
        time.sleep(3) 

except KeyboardInterrupt:
    print("Script stopped by user.")
    sensor_power.value = False # Ensure sensor is off