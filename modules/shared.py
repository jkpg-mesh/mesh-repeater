import threading

class SharedState:
    def __init__(self):
        # Initialize general shared variables
        self._counter = 0
        # Initialize MET data variables
        self._temp1 = 0.0
        self._temp2 = 0.0
        self._pressure_station = 0.0
        self._pressure_sea = 0.0
        self._humidity = 0.0
        # Initialize GPS related variables
        self.satellites_in_view = {}  # dict of talker -> dict of satellites
        self.satellites_in_fix = {}  # dict of talker -> dict of satellites
        self.gps_time = None # GPS time as a formatted string
        self.gps_fix = False # GPS fix status
        self.gps_pos = {} # latitude, longitude, altitude
        self.gps_track = {} #true_course, magnetic_course, ppeed_kts, speed_kmh
        self.gps_status = "No info" # GPS status message
        # Meshtastic related variables
        self.messages = []
        # lock for thread safety
        self._lock = threading.Lock()

    def get_counter(self):
        """Thread-safe way to read the variable."""
        with self._lock:
            return self._counter
        
    def set_counter(self, value):
        """Thread-safe way to write the variable."""
        with self._lock:
            self._counter = value
   
    def get_metdata(self):
        """Thread-safe way to read multiple variables."""
        with self._lock:
            return {
                'temp1': self._temp1,
                'temp2': self._temp2,
                'pressure_station': self._pressure_station,
                'pressure_sea': self._pressure_sea,
                'humidity': self._humidity
            }
        
    def set_metdata(self, temp1, temp2, pressure_station, pressure_sea, humidity):
        """Thread-safe way to write multiple variables."""
        with self._lock:
            self._temp1 = temp1
            self._temp2 = temp2
            self._pressure_station = pressure_station
            self._pressure_sea = pressure_sea
            self._humidity = humidity
    
    def get_satellites_in_view(self):
        """
        Thread-safe way to read the satellite_in_view variable.
        """
        with self._lock:
            return self.satellites_in_view
        
    def set_satellites_in_view(self,value = {}):
        """
        Thread-safe way to write the satellite_in_view variable.
        """
        with self._lock:
            self.satellites_in_view = value

    def get_satellites_in_fix(self):
        """
        Thread-safe way to read the satellite_in_fix variable.
        """
        with self._lock:
            return self.satellites_in_fix
        
    def set_satellites_in_fix(self,value = {}):
        """
        Thread-safe way to write the satellite_in_fix variable.
        """
        with self._lock:
            self.satellites_in_fix = value

    def get_gps_time(self):
        """ Thread-safe way to read the gps_time variable."""
        with self._lock:
            return self.gps_time
        
    def set_gps_time(self, value=None):
        """ Thread-safe way to write the gps_time variable."""
        with self._lock:
            self.gps_time = value

    def get_gps_fix(self):
        """ Thread-safe way to read the gps_fix variable."""
        with self._lock:
            return self.gps_fix
        
    def set_gps_fix(self, value=False):
        """ Thread-safe way to write the gps_fix variable."""
        with self._lock:
            self.gps_fix = value

    def get_gps_pos(self):
        """ Thread-safe way to read the gps_pos variable."""
        with self._lock:
            return self.gps_pos 
        
    def set_gps_pos(self, value={}):
        """ Thread-safe way to write the gps_pos variable."""
        with self._lock:
            self.gps_pos = value    

    def get_gps_track(self):
        """ Thread-safe way to read the gps_track variable."""
        with self._lock:
            return self.gps_track   
        
    def set_gps_track(self, value={}):
        """ Thread-safe way to write the gps_track variable."""
        with self._lock:
            self.gps_track = value
    
    def get_gps_status(self):
        """ Thread-safe way to read the gps_status variable."""
        with self._lock:
            return self.gps_status
    
    def set_gps_status(self, value="No info"):
        """ Thread-safe way to write the gps_status variable."""
        with self._lock:
            self.gps_status = value
    
    def add_message(self, sender, text):
        self.messages.append({'from': sender, 'text': text})

    def get_messages(self):
        return self.messages