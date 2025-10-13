#!/usr/bin/env python3
"""
DHT11 Temperature and Humidity Sensor Data Logger
Compatible with Python 3.11 and Raspberry Pi Zero W
"""

import time
import board
import adafruit_dht
import csv
import json
from datetime import datetime
from pathlib import Path
import signal
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dht11_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DHT11SensorLogger:
    """Class to handle DHT11 sensor data recording"""
    
    def __init__(self, gpio_pin=board.D4, data_dir="sensor_data"):
        """
        Initialize the DHT11 sensor logger
        
        Args:
            gpio_pin: GPIO pin where DHT11 data pin is connected (default: GPIO4/Pin 7)
            data_dir: Directory to store data files
        """
        self.sensor = adafruit_dht.DHT11(gpio_pin)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Generate filenames with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_file = self.data_dir / f"dht11_data_{timestamp}.csv"
        self.json_file = self.data_dir / f"dht11_data_{timestamp}.json"
        
        # Initialize CSV file with headers
        self._init_csv_file()
        
        logger.info(f"DHT11 Sensor Logger initialized on pin {gpio_pin}")
        logger.info(f"Data will be saved to {self.data_dir}")
    
    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Shutdown signal received. Cleaning up...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def _init_csv_file(self):
        """Initialize CSV file with headers"""
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'temperature_c', 'temperature_f', 'humidity_percent'])
        logger.info(f"CSV file created: {self.csv_file}")
    
    def read_sensor(self):
        """
        Read temperature and humidity from DHT11 sensor
        
        Returns:
            dict: Sensor data or None if read failed
        """
        try:
            temperature_c = self.sensor.temperature
            humidity = self.sensor.humidity
            
            if temperature_c is not None and humidity is not None:
                temperature_f = temperature_c * 9.0 / 5.0 + 32.0
                
                data = {
                    'timestamp': datetime.now().isoformat(),
                    'temperature_c': round(temperature_c, 1),
                    'temperature_f': round(temperature_f, 1),
                    'humidity_percent': round(humidity, 1)
                }
                
                logger.debug(f"Sensor read successful: Temp={temperature_c}°C, Humidity={humidity}%")
                return data
            else:
                logger.warning("Sensor returned None values")
                return None
                
        except RuntimeError as e:
            # DHT sensors can be finicky, errors are expected occasionally
            logger.debug(f"Sensor read error (expected occasionally): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading sensor: {e}")
            return None
    
    def save_to_csv(self, data):
        """Save sensor data to CSV file"""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data['timestamp'],
                    data['temperature_c'],
                    data['temperature_f'],
                    data['humidity_percent']
                ])
            logger.debug("Data saved to CSV")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def save_to_json(self, data):
        """Save sensor data to JSON file"""
        try:
            # Read existing data if file exists
            if self.json_file.exists():
                with open(self.json_file, 'r') as f:
                    json_data = json.load(f)
            else:
                json_data = []
            
            # Append new data
            json_data.append(data)
            
            # Write updated data
            with open(self.json_file, 'w') as f:
                json.dump(json_data, f, indent=2)
            
            logger.debug("Data saved to JSON")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
    
    def display_data(self, data):
        """Display sensor data in console"""
        print("\n" + "="*50)
        print(f"Timestamp: {data['timestamp']}")
        print(f"Temperature: {data['temperature_c']}°C / {data['temperature_f']}°F")
        print(f"Humidity: {data['humidity_percent']}%")
        print("="*50)
    
    def get_statistics(self):
        """Calculate and return statistics from collected data"""
        try:
            data_points = []
            with open(self.csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data_points.append({
                        'temperature_c': float(row['temperature_c']),
                        'humidity_percent': float(row['humidity_percent'])
                    })
            
            if data_points:
                temps = [d['temperature_c'] for d in data_points]
                humidities = [d['humidity_percent'] for d in data_points]
                
                stats = {
                    'readings_count': len(data_points),
                    'temperature': {
                        'min': min(temps),
                        'max': max(temps),
                        'avg': sum(temps) / len(temps)
                    },
                    'humidity': {
                        'min': min(humidities),
                        'max': max(humidities),
                        'avg': sum(humidities) / len(humidities)
                    }
                }
                return stats
            return None
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return None
    
    def run(self, interval=2.0, display=True, save_csv=True, save_json=False):
        """
        Main loop to continuously read and record sensor data
        
        Args:
            interval: Time between readings in seconds (minimum 2.0 for DHT11)
            display: Whether to display readings in console
            save_csv: Whether to save data to CSV file
            save_json: Whether to save data to JSON file
        """
        logger.info(f"Starting sensor monitoring (interval={interval}s)")
        logger.info("Press Ctrl+C to stop")
        
        consecutive_errors = 0
        max_consecutive_errors = 10
        readings_count = 0
        
        while self.running:
            try:
                # Read sensor
                data = self.read_sensor()
                
                if data:
                    readings_count += 1
                    consecutive_errors = 0
                    
                    # Display data
                    if display:
                        self.display_data(data)
                    
                    # Save to files
                    if save_csv:
                        self.save_to_csv(data)
                    if save_json:
                        self.save_to_json(data)
                    
                    # Log statistics every 10 readings
                    if readings_count % 10 == 0:
                        stats = self.get_statistics()
                        if stats:
                            logger.info(f"Statistics after {stats['readings_count']} readings:")
                            logger.info(f"  Temp: {stats['temperature']['min']:.1f}-{stats['temperature']['max']:.1f}°C (avg: {stats['temperature']['avg']:.1f}°C)")
                            logger.info(f"  Humidity: {stats['humidity']['min']:.1f}-{stats['humidity']['max']:.1f}% (avg: {stats['humidity']['avg']:.1f}%)")
                else:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many consecutive errors ({max_consecutive_errors}). Check sensor connection!")
                        consecutive_errors = 0  # Reset counter but continue trying
                
                # Wait before next reading
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                self.running = False
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(interval)
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.sensor.exit()
            logger.info("Sensor cleanup completed")
            
            # Print final statistics
            stats = self.get_statistics()
            if stats:
                logger.info("Final Statistics:")
                logger.info(f"  Total readings: {stats['readings_count']}")
                logger.info(f"  Temperature range: {stats['temperature']['min']:.1f}-{stats['temperature']['max']:.1f}°C")
                logger.info(f"  Average temperature: {stats['temperature']['avg']:.1f}°C")
                logger.info(f"  Humidity range: {stats['humidity']['min']:.1f}-{stats['humidity']['max']:.1f}%")
                logger.info(f"  Average humidity: {stats['humidity']['avg']:.1f}%")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main function to run the DHT11 sensor logger"""
    
    # Configuration
    GPIO_PIN = board.D4  # GPIO4 (Physical Pin 7 on Pi Zero W)
    # Other common pins: board.D17, board.D27, board.D22
    
    READING_INTERVAL = 2.0  # Seconds between readings (minimum 2.0 for DHT11)
    DISPLAY_DATA = True     # Show readings in console
    SAVE_TO_CSV = True      # Save data to CSV file
    SAVE_TO_JSON = False    # Save data to JSON file
    DATA_DIRECTORY = "sensor_data"  # Directory for data files
    
    try:
        # Create and run sensor logger
        sensor_logger = DHT11SensorLogger(
            gpio_pin=GPIO_PIN,
            data_dir=DATA_DIRECTORY
        )
        
        sensor_logger.run(
            interval=READING_INTERVAL,
            display=DISPLAY_DATA,
            save_csv=SAVE_TO_CSV,
            save_json=SAVE_TO_JSON
        )
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
