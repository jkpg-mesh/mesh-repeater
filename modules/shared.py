import threading

class SharedState:
    def __init__(self):
        self._counter = 0
        self._temp1 = 0.0
        self._temp2 = 0.0
        self._pressure_station = 0.0
        self._pressure_sea = 0.0
        self._humidity = 0.0
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