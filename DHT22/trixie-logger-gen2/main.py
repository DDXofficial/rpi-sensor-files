# new DHT22 script for Raspberry Pi 5 (Gemini 2.5 Pro)

"""
testing environment: Raspberry Pi 5
                 OS: Raspberry Pi OS / Debian 13 (trixie)
             Python: 3.13.x (ensured compatibility with Python 3.9 for other testing environments)
"""

import time
import board
import adafruit_dht
import csv
import os
from datetime import datetime

# --- Configuration ---
# The GPIO pin connected to the DHT22 data pin.
# board.D4 corresponds to GPIO4.
SENSOR_PIN = board.D4

# Time to wait between sensor readings, in seconds.
SAMPLE_INTERVAL = 3

# The name of the CSV file to log data to.
LOG_BASENAME = "dht22.csv"

# --- Main Script ---
def main():
    """
    Initializes the sensor, sets up the CSV file, and enters a loop
    to read and log sensor data.
    """

    print("DHT22 RPi Data Logger Version 0.1 - by DDX")
    print("")

    print(f"GPIO pin: {SENSOR_PIN.id}")
    print(f"Sample interval: {SAMPLE_INTERVAL} seconds")
    print("")

    # --- NEW: Generate a unique, timestamped filename ---
    try:
        # Format the current time for a filename
        run_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        CSV_FILE_PATH = f"{run_timestamp}_{LOG_BASENAME}"
    except Exception as e:
        print(f"Error generating timestamp for log file: {e}")
        return

    # Initialize the DHT22 sensor object.
    # The 'use_pulseio=False' argument is crucial for modern Raspberry Pi OS
    # and ensures it uses the digitalio backend.
    try:
        dht_sensor = adafruit_dht.DHT22(SENSOR_PIN, use_pulseio=False)
    except ValueError as ve:
        print(f"Error: Could not initialize sensor. Is it connected to GPIO{SENSOR_PIN.id}?")
        print(f"Details: {ve}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during sensor initialization: {e}")
        return

    # --- NEW: 'logs' directory ---
    try:
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)
        CSV_DIR_FILE_PATH = os.path.join(logs_dir, CSV_FILE_PATH)
    except Exception as e:
        print(f"Error creating logs directory: {e}")
        return

    # --- NEW: Always create a new file and write the header ---
    try:
        with open(CSV_DIR_FILE_PATH, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Temperature-C', 'Temperature-F', 'Humidity_Percent'])
        print(f"Logging to new file: {CSV_FILE_PATH}")
    except IOError as e:
        print(f"Error: Could not create log file. Check permissions.")
        print(f"Details: {e}")
        return

    print("")
    print("--- Starting Temperature & Humidity Logging ---")
    print("Press Ctrl+C to stop.")
    print("")

    try:
        while True:
            try:
                # Read temperature and humidity from the sensor
                temperature_c = dht_sensor.temperature
                humidity = dht_sensor.humidity

                # Added Fahrenheit after the fact (Gemini can't u see the muricans DO NOT RESPECT CELSIUS LMAO)
                temperature_f = temperature_c * 9 / 5 + 32 if temperature_c is not None else None

                # The DHT22 can sometimes return None, especially on startup.
                if humidity is not None and temperature_c is not None:
                    # Get the current timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Print the readings to the console
                    print(
                        f"Timestamp: {timestamp} | "
                        f"Temperature (C): {temperature_c:.1f}°C | "
                        f"Temperature (F): {temperature_f:.1f}°F | "
                        f"Humidity: {humidity:.1f}%"
                    )

                    # Append the data to the CSV file
                    with open(CSV_DIR_FILE_PATH, mode='a', newline='') as file:
                        writer = csv.writer(file)
                        writer.writerow([timestamp, f"{temperature_c:.1f}", f"{temperature_f:.1f}", f"{humidity:.1f}"])

                else:
                    print("Sensor read failure. Retrying...")

            except RuntimeError as error:
                # DHT sensors can be finicky. This catches read errors.
                print(f"Error reading from sensor: {error.args[0]}")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
            
            # Wait for the specified interval before the next reading
            time.sleep(SAMPLE_INTERVAL)

    except KeyboardInterrupt:
        print("\nLogging stopped by user.")
    finally:
        # Clean up the sensor resources
        dht_sensor.exit()
        print("Sensor resources released. Exiting.")


if __name__ == "__main__":
    main()