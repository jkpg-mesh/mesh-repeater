# -*- coding: utf-8 -*-
import time
import board
import busio
import adafruit_ahtx0
import adafruit_bmp280

class METService:
    """
    This class handles the reading of temperature, humidity, and pressure
    from AHT20 and BMP280 sensors. It updates the shared state with the
    latest readings in a thread-safe manner.
    It supports dynamic enabling/disabling via the 'met_on' config flag.
    """

    def __init__(self, logging, shared_data, config):
        self.shared_data = shared_data
        self.logging = logging
        self.config = config
        self.status = False

        self.i2c = None
        self.aht20 = None
        self.bmp280 = None

    def _init_sensors(self):
        """Initialize I2C bus and sensors dynamically."""
        try:
            self.i2c = busio.I2C(board.SCL, board.SDA)
            self.aht20 = adafruit_ahtx0.AHTx0(self.i2c)
            self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(self.i2c)

            self.bmp280.overscan_pressure = adafruit_bmp280.OVERSCAN_X16
            self.bmp280.overscan_temperature = adafruit_bmp280.OVERSCAN_X2
            self.bmp280.filter = adafruit_bmp280.IIR_FILTER_X16
            self.bmp280.standby_period = adafruit_bmp280.STANDBY_TC_500

            self.logging.info("METService sensors initialized dynamically")
            return True
        except Exception as e:
            self.logging.error(f"Failed to initialize MET sensors: {e}")
            self.aht20 = None
            self.bmp280 = None
            self.i2c = None
            return False

    def _cleanup_sensors(self):
        """Cleanup sensors and release I2C resources."""
        if self.aht20 or self.bmp280:
            self.logging.info("Cleaning up METService sensors")
        self.aht20 = None
        self.bmp280 = None
        self.i2c = None

    def start(self):
        """Start the MET reading loop."""
        self.status = True
        sensors_initialized = False

        while self.status:
            met_on = self.config.get("met_on", "Disabled") == "Enabled"

            if met_on and not sensors_initialized:
                sensors_initialized = self._init_sensors()
            elif not met_on and sensors_initialized:
                self._cleanup_sensors()
                sensors_initialized = False

            if not met_on or not sensors_initialized:
                time.sleep(1)
                continue

            # Read sensor data safely
            try:
                t_aht = self.aht20.temperature
                rh = self.aht20.relative_humidity
                t_bmp = self.bmp280.temperature
                p_station = self.bmp280.pressure

                p_sea = self._sea_level_pressure_hpa(
                    p_station,
                    t_aht,
                    int(self.config.get("altitude", 0))
                )

                self.shared_data.set_metdata(
                    temp1=t_aht,
                    temp2=t_bmp,
                    pressure_station=p_station,
                    pressure_sea=p_sea,
                    humidity=rh
                )

                if self.config.get("met_logging", "Disabled") == "Enabled":
                    self.logging.info(f"AHT20 Temp: {t_aht:.2f} °C Humidity: {rh:.1f}%")
                    self.logging.info(f"BMP280 Temp: {t_bmp:.2f} °C Station Pressure: {p_station:.2f} hPa Sea-level: {p_sea:.2f} hPa")
            except Exception as e:
                self.logging.error(f"Error reading MET sensors: {e}")

            time.sleep(int(self.config.get("met_interval", 60)))

    def stop(self):
        """Stop the MET reading loop and cleanup sensors."""
        self.status = False
        self._cleanup_sensors()

    def _sea_level_pressure_hpa(self, station_hpa, temp_c, altitude_m):
        """
        Convert station pressure to sea-level pressure using the barometric formula.
        Uses the standard temperature lapse rate. Good for small altitude corrections.
        """
        T = temp_c + 273.15       # Kelvin
        L = 0.0065                # K/m (standard lapse rate)
        g = 9.80665               # m/s^2
        M = 0.0289644             # kg/mol
        R = 8.3144598             # J/(mol*K)

        factor = (1 - (L * altitude_m) / T) ** (-g * M / (R * L))
        return station_hpa * factor
