import serial
import time
import threading

class SerialReader:
    """Core class to handle serial port connection and reading logic."""
    def __init__(self, port, baudrate, bytesize, parity, stopbits, xonxoff, rtscts):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.xonxoff = xonxoff
        self.rtscts = rtscts
        
        self.serial_port = None
        self.is_reading = False
        self.read_thread = None

    def connect(self):
        """Opens the serial port with the configured parameters."""
        self.serial_port = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=self.bytesize,
            parity=self.parity,
            stopbits=self.stopbits,
            xonxoff=self.xonxoff,
            rtscts=self.rtscts,
            timeout=1
        )
        self.is_reading = True

    def disconnect(self):
        """Stops reading and closes the serial port."""
        self.is_reading = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()

    def start_reading(self, on_data_callback, on_error_callback):
        """Starts a background thread to continuously read data from the port."""
        self.read_thread = threading.Thread(
            target=self._read_loop, 
            args=(on_data_callback, on_error_callback), 
            daemon=True
        )
        self.read_thread.start()

    def _read_loop(self, on_data, on_error):
        """Internal loop that waits for data and triggers the callback."""
        while self.is_reading:
            try:
                if self.serial_port.in_waiting > 0:
                    # Delay to ensure data buffering, matching original Java behavior
                    time.sleep(0.2)
                    while self.serial_port.in_waiting > 0 and self.is_reading:
                        data = self.serial_port.read(1)
                        if data:
                            bit = data[0]
                            char_val = chr(bit) if 32 <= bit <= 126 else chr(bit)
                            on_data(char_val, bit)
                else:
                    time.sleep(0.1)
            except Exception as e:
                if self.is_reading:
                    on_error(str(e))
                break
