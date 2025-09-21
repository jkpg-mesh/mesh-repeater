# -*- coding: utf-8 -*-
import serial
import pynmea2
import pytz
import time
from datetime import datetime,timedelta

class mygps:
    """
    This class handles reading and parsing NMEA sentences from a GPS module
    connected via a serial port. It extracts information such as position,
    time, fix status, and satellite details. It also corrects for GPS Week
    Number Rollover and converts UTC time to a specified timezone."""
    LAST_ROLLOVER = pytz.utc.localize(datetime(2019, 4, 6, 0, 0, 0)) # The date of the last GPS Week Number Rollover (April 6, 2019)
    WEEKS_TO_ADD = 1024 # Number of weeks to add for each rollover

    def _correct_date(self, dt):
        """
        Fixes the date for GPS Week Number Rollover.
        Args:
            dt (datetime.datetime): A timezone-naive datetime object from the GPS.
        Returns:
            datetime.datetime: The corrected timezone-naive datetime object.
        """
        if dt < self.LAST_ROLLOVER:
            return dt + timedelta(weeks=self.WEEKS_TO_ADD)
        return dt

    def _convert_timezone(self, dt, tz_name='Europe/Paris'):
        """
        Convert a UTC datetime to a specified timezone.
        Args:
            dt (datetime): A timezone-naive datetime object in UTC.
            tz_name (str): The name of the target timezone (default is "Europe/Stockholm").
        Returns:
            datetime: A timezone-aware datetime object in the specified timezone.
        """
        utc_dt = dt.replace(tzinfo=pytz.UTC)
        local_tz = pytz.timezone(tz_name)
        return utc_dt.astimezone(local_tz)

    def __init__(self, logging, shared_data, config):
        """
        Initialize the GPS reader.
        Args:
            port (str): Serial port to which the GPS module is connected.
            baudrate (int): Baud rate for the serial communication.
            timeout (int): Read timeout in seconds.
            logging: Logger instance for logging messages.
            shared_data: Shared data object to store GPS data.
            config: Configuration dictionary.
        """
        self.shared_data = shared_data
        self.logging = logging
        self.config = config
        self.status = False

        self.TZ_NAME = config.get("timezone", "Europe/Paris")

        self.port = config.get("gps_port", None)
        self.baudrate = config.get("gps_baudrate", None)
        self.timeout = 1
        self.ser = None

        self.satellites_in_view = {}  # dict of talker -> dict of satellites
        self.satellites_in_fix = {}  # dict of talker -> dict of satellites
        self.gps_time = None # GPS time as a formatted string
        self.gps_fix = False # GPS fix status
        self.gps_pos = {} # latitude, longitude, altitude
        self.gps_track = {} #true_course, magnetic_course, ppeed_kts, speed_kmh
        self.gps_status = "No info"

    def _init_sensor(self):
        """
        Initialize the GPS sensor by opening the serial port.
        Returns:
            bool: True if initialization is successful, False otherwise.
        """
        if not self.port or not self.baudrate:
            self.logging.error("Invalid GPS configuration: port or baudrate missing.")
            raise ValueError("GPS port and baudrate must be specified in config.")
        
        try:
            self.ser = serial.Serial(self.port, baudrate=self.baudrate, timeout=self.timeout)
            self.logging.info(f"Initialized GPS on port {self.port} at {self.baudrate} baud.")
            return True
        except serial.SerialException as e:
            self.logging.error(f"Failed to initialize GPS on port {self.port}: {e}")
            self.ser = None
            return False 

    def _cleanup_sensor(self):
        """
        Cleanup the GPS sensor by closing the serial port.
        """
        if self.ser and self.ser.is_open:
            self.logging.info("Closing GPS serial port.")
            self.ser.close()
        self.ser = None

    def start(self):
        """
        Main loop to read and parse NMEA sentences from the GPS module.
        """
        self.status = True
        sensors_initialized = False

        while self.status:
            gps_on = self.config.get("gps_on", "Disabled") == "Enabled"
            
            if gps_on and not sensors_initialized:
                sensors_initialized = self._init_sensor()
            elif not gps_on and sensors_initialized:
                self._cleanup_sensor()
                sensors_initialized = False
            # Skip reading if GPS is disabled or sensor not initialized
            if not gps_on or not sensors_initialized:
                time.sleep(1)
                continue
            
            # Read and parse NMEA sentences
            try:
                while gps_on:
                    line = self.ser.readline().decode('ascii', errors='replace').strip()
                    if line.startswith("$"):
                        try:
                            data = pynmea2.parse(line)
                        except pynmea2.ParseError as e:
                            self.logging.warning(f"Failed to parse NMEA sentence: {line}, error: {e}")
                            continue
                        match data.sentence_type:
                            case "GGA":
                                # Convert latitude/longitude to signed decimal
                                lat = float(data.latitude)
                                if data.lat_dir == "S":
                                    lat = -lat
                                lon = float(data.longitude)
                                if data.lon_dir == "W":
                                    lon = -lon
                                # Update gps_pos dictionary
                                self.gps_pos = {
                                    "latitude": lat,
                                    "longitude": lon,
                                    "altitude": float(data.altitude) if data.altitude else None,
                                    "altitude_units": data.altitude_units,
                                    "fix_quality": data.gps_qual,
                                    "num_sats": data.num_sats,
                                    "hdop": data.horizontal_dil,
                                    "geoid_sep": data.geo_sep,
                                    "geoid_units": data.geo_sep_units,
                                    "system": data.talker,  # 'GP', 'GL', 'GA', 'BD', etc.
                                }
                                self.shared_data.set_gps_pos(value = self.gps_pos)
                            case "GSA":
                                # Update gps_fix status and satellites_in_fix dictionary
                                if data.mode_fix_type != '1':  # '1' means no fix
                                    self.gps_fix = True
                                    # Ensure the talker key exists
                                    talker = data.talker
                                    if talker not in self.satellites_in_fix:
                                        self.satellites_in_fix[talker] = {}
                                    # Clear previous satellites for this fix
                                    self.satellites_in_fix[talker] = {}
                                    # Iterate over SV ID fields dynamically
                                    sv_fields = [attr for label, attr in data.fields if attr.startswith('sv_id')]
                                    # Collect satellites from this sentence
                                    for attr in sv_fields:
                                        prn = getattr(data, attr, None)
                                        if prn:  # skip empty slots
                                            # Store in the dict under talker
                                            self.satellites_in_fix[talker][prn] = {
                                                "prn": prn,
                                            }
                                else:
                                    self.gps_fix = False
                                    # Clear previous fix if no valid fix
                                    self.satellites_in_fix[data.talker] = {}
                                # You can also store PDOP, HDOP, VDOP if needed -not used for now
                                PDOP = data.pdop
                                HDOP = data.hdop
                                VDOP = data.vdop
                                self.shared_data.set_gps_fix(value= self.gps_fix)
                                self.shared_data.set_satellites_in_fix(value = self.satellites_in_fix)
                            case "GSV":
                                talker = data.talker  # e.g. "GP", "GA", "GL", "BD"
                                # Ensure talker key exists
                                if talker not in self.satellites_in_view or data.msg_num == 1:
                                    # New cycle or first time we’ve seen this talker
                                    self.satellites_in_view[talker] = {}
                                # Collect satellites from this sentence
                                for i in range(1, 5):
                                    prn  = getattr(data, f'sv_prn_num_{i}', None)
                                    elev = getattr(data, f'elevation_deg_{i}', None)
                                    azim = getattr(data, f'azimuth_{i}', None)
                                    snr  = getattr(data, f'snr_{i}', None)
                                    if prn:
                                        sat_info = {
                                            "prn": prn,
                                            "elevation": elev,
                                            "azimuth": azim,
                                            "snr": snr,
                                        }
                                        self.satellites_in_view[talker][prn] = sat_info
                                self.shared_data.set_satellites_in_view(value = self.satellites_in_view)
                            case "VTG":
                                #update gps_track dictionary
                                self.gps_track = {
                                    "true_course": float(data.true_track) if data.true_track else None,
                                    "magnetic_course": float(data.mag_track) if data.mag_track else None,
                                    "speed_kts": float(data.spd_over_grnd_kts) if data.spd_over_grnd_kts else None,
                                    "speed_kmh": float(data.spd_over_grnd_kmph) if data.spd_over_grnd_kmph else None,
                                }
                                self.shared_data.set_gps_track(value= self.gps_track)
                            case "ZDA":
                                gps_time = datetime.combine(data.datestamp, data.timestamp)
                                corrected_datetime = self._correct_date(dt=gps_time)
                                self.gps_time = f"{self._convert_timezone(dt=corrected_datetime).strftime('%Y-%m-%d %H:%M:%S')} ({self.TZ_NAME})"
                                self.shared_data.set_gps_time(value = self.gps_time)
                            case "TXT":
                                self.gps_status = data.text
                                self.shared_data.set_gps_status(value = self.gps_status)
                    gps_on = self.config.get("gps_on", "Disabled") == "Enabled"               
            except serial.SerialException as e:
                self.logging.error(f"Serial error while reading GPS data: {e}")
                self._cleanup_sensor()
                sensors_initialized = False
        
    def stop(self):
        """
        Stop the GPS reading loop and cleanup resources.
        """
        self.status = False
        self._cleanup_sensor()
