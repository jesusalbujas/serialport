import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time

class SerialReaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Lector de Puerto Serie")
        self.root.geometry("620x480")
        
        self.serial_port = None
        self.is_reading = False
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame de configuracion
        config_frame = ttk.LabelFrame(self.root, text="Configuración")
        config_frame.pack(padx=10, pady=10, fill="x")
        
        # Puerto
        ttk.Label(config_frame, text="Puerto:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.port_cb = ttk.Combobox(config_frame, values=[p.device for p in serial.tools.list_ports.comports()])
        self.port_cb.grid(row=0, column=1, padx=5, pady=5)
        if self.port_cb['values']:
            self.port_cb.current(0)
            
        # Botón para refrescar puertos disponibles
        ttk.Button(config_frame, text="↻", width=3, command=self.refresh_ports).grid(row=0, column=2, padx=5, pady=5)
            
        # Velocidad (Speed)
        ttk.Label(config_frame, text="Velocidad:").grid(row=0, column=3, padx=5, pady=5, sticky="e")
        self.speed_cb = ttk.Combobox(config_frame, values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.speed_cb.set("2400")
        self.speed_cb.grid(row=0, column=4, padx=5, pady=5)
        
        # Bits de Datos
        ttk.Label(config_frame, text="Bits Datos:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.data_cb = ttk.Combobox(config_frame, values=["5", "6", "7", "8"])
        self.data_cb.set("8")
        self.data_cb.grid(row=1, column=1, padx=5, pady=5)
        
        # Bits de Parada
        ttk.Label(config_frame, text="Bits Parada:").grid(row=1, column=3, padx=5, pady=5, sticky="e")
        self.stop_cb = ttk.Combobox(config_frame, values=["1", "1.5", "2"])
        self.stop_cb.set("1")
        self.stop_cb.grid(row=1, column=4, padx=5, pady=5)
        
        # Paridad
        ttk.Label(config_frame, text="Paridad:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.parity_cb = ttk.Combobox(config_frame, values=["Ninguna (0)", "Impar (1)", "Par (2)", "Marca (3)", "Espacio (4)"])
        self.parity_cb.set("Ninguna (0)")
        self.parity_cb.grid(row=2, column=1, padx=5, pady=5)
        
        # Control de Flujo
        ttk.Label(config_frame, text="Ctrl Flujo:").grid(row=2, column=3, padx=5, pady=5, sticky="e")
        self.flow_cb = ttk.Combobox(config_frame, values=["Ninguno (0)", "RTS/CTS (1)", "XON/XOFF (4)"])
        self.flow_cb.set("Ninguno (0)")
        self.flow_cb.grid(row=2, column=4, padx=5, pady=5)
        
        # Botones Conectar / Desconectar
        self.connect_btn = ttk.Button(config_frame, text="Conectar", command=self.connect)
        self.connect_btn.grid(row=3, column=1, pady=10)
        
        self.disconnect_btn = ttk.Button(config_frame, text="Desconectar", command=self.disconnect, state="disabled")
        self.disconnect_btn.grid(row=3, column=3, pady=10)
        
        # Consola de salida
        self.console = scrolledtext.ScrolledText(self.root, width=70, height=15, state='disabled', bg='black', fg='white')
        self.console.pack(padx=10, pady=10, fill="both", expand=True)

    def refresh_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_cb['values'] = ports
        if ports:
            self.port_cb.current(0)
            
    def log(self, message):
        self.console.configure(state='normal')
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.configure(state='disabled')
        
    def connect(self):
        port_name = self.port_cb.get()
        if not port_name:
            messagebox.showerror("Error", "Seleccione o escriba un puerto (ej. COM1).")
            return
            
        speed = int(self.speed_cb.get())
        data_bits_arg = int(self.data_cb.get())
        
        stop_val = self.stop_cb.get()
        if stop_val == "1":
            stop_bits = serial.STOPBITS_ONE
        elif stop_val == "1.5":
            stop_bits = serial.STOPBITS_ONE_POINT_FIVE
        else:
            stop_bits = serial.STOPBITS_TWO
            
        parity_str = self.parity_cb.get()
        if "0" in parity_str: parity = serial.PARITY_NONE
        elif "1" in parity_str: parity = serial.PARITY_ODD
        elif "2" in parity_str: parity = serial.PARITY_EVEN
        elif "3" in parity_str: parity = serial.PARITY_MARK
        else: parity = serial.PARITY_SPACE
        
        flow_str = self.flow_cb.get()
        xonxoff = "4" in flow_str
        rtscts = "1" in flow_str
        
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=speed,
                bytesize=data_bits_arg,
                parity=parity,
                stopbits=stop_bits,
                xonxoff=xonxoff,
                rtscts=rtscts,
                timeout=1
            )
            self.log(f"Abriendo {port_name} ...")
            self.log("Parametrizando Puerto...")
            self.log("Puerto Listo ...")
            
            self.connect_btn.config(state="disabled")
            self.disconnect_btn.config(state="normal")
            
            self.is_reading = True
            self.read_thread = threading.Thread(target=self.read_loop, daemon=True)
            self.read_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error de Conexión", str(e))
            
    def disconnect(self):
        self.is_reading = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.log("Cerrado")
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        
    def read_loop(self):
        while self.is_reading:
            try:
                if self.serial_port.in_waiting > 0:
                    time.sleep(0.2)
                    while self.serial_port.in_waiting > 0 and self.is_reading:
                        data = self.serial_port.read(1)
                        if data:
                            bit = data[0]
                            char_val = chr(bit) if 32 <= bit <= 126 else chr(bit)
                            self.log(f"=>>[{char_val}|{bit}]")
                else:
                    time.sleep(0.1)
            except Exception as e:
                if self.is_reading:
                    self.log(f"Error leyendo: {e}")
                break

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialReaderApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect(), root.destroy()))
    root.mainloop()
