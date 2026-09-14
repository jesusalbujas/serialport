import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports
from serial_reader import SerialReader

# Configuracion de apariencia moderna
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SerialReaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Lector de Puerto Serie")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        self.reader = None
        self.buffer = ""
        
        # Grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_main_view()
        
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)
        
        logo = ctk.CTkLabel(self.sidebar, text="Serial Reader", font=ctk.CTkFont(size=22, weight="bold"))
        logo.grid(row=0, column=0, padx=20, pady=(20, 20))
        
        # Port
        ctk.CTkLabel(self.sidebar, text="Puerto COM:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=20, pady=(5, 0), sticky="w")
        
        self.port_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.port_frame.grid(row=2, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        self.port_cb = ctk.CTkComboBox(self.port_frame, values=self.get_ports())
        self.port_cb.pack(side="left", fill="x", expand=True)
        
        self.refresh_btn = ctk.CTkButton(self.port_frame, text="↻", width=30, command=self.refresh_ports)
        self.refresh_btn.pack(side="right", padx=(5, 0))
        
        # Speed
        ctk.CTkLabel(self.sidebar, text="Velocidad (Baud):", font=ctk.CTkFont(weight="bold")).grid(row=3, column=0, padx=20, pady=(5, 0), sticky="w")
        self.speed_cb = ctk.CTkComboBox(self.sidebar, values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        self.speed_cb.set("2400")
        self.speed_cb.grid(row=4, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Data Bits
        ctk.CTkLabel(self.sidebar, text="Bits de Datos:", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, padx=20, pady=(5, 0), sticky="w")
        self.data_cb = ctk.CTkComboBox(self.sidebar, values=["5", "6", "7", "8"])
        self.data_cb.set("8")
        self.data_cb.grid(row=6, column=0, padx=20, pady=(0, 15), sticky="ew")
        
        # Stop Bits
        ctk.CTkLabel(self.sidebar, text="Bits Parada:", font=ctk.CTkFont(weight="bold")).grid(row=7, column=0, padx=20, pady=(5, 0), sticky="w")
        self.stop_cb = ctk.CTkComboBox(self.sidebar, values=["1", "1.5", "2"])
        self.stop_cb.set("1")
        self.stop_cb.grid(row=8, column=0, padx=20, pady=(0, 15), sticky="nw")
        
        # Connect / Disconnect Buttons
        self.connect_btn = ctk.CTkButton(self.sidebar, text="CONECTAR", fg_color="#27AE60", hover_color="#2ECC71", font=ctk.CTkFont(weight="bold"), command=self.connect)
        self.connect_btn.grid(row=11, column=0, padx=20, pady=(10, 5), sticky="ew")
        
        self.disconnect_btn = ctk.CTkButton(self.sidebar, text="DESCONECTAR", fg_color="#C0392B", hover_color="#E74C3C", font=ctk.CTkFont(weight="bold"), command=self.disconnect, state="disabled")
        self.disconnect_btn.grid(row=12, column=0, padx=20, pady=(5, 20), sticky="ew")
        
    def create_main_view(self):
        self.main_view = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_view.grid_rowconfigure(2, weight=1) # El textbox ocupa el resto
        self.main_view.grid_columnconfigure(0, weight=1)
        
        # Panel Superior: Extracción de datos
        self.extraction_frame = ctk.CTkFrame(self.main_view, height=120)
        self.extraction_frame.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        self.extraction_frame.grid_columnconfigure(2, weight=1)
        
        # Controles de extracción
        controls_frame = ctk.CTkFrame(self.extraction_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, padx=15, pady=15, sticky="w")
        
        ctk.CTkLabel(controls_frame, text="Inicio de corte (ej: +):").grid(row=0, column=0, sticky="w", padx=5)
        self.char_start = ctk.CTkEntry(controls_frame, width=50)
        self.char_start.insert(0, "+")
        self.char_start.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(controls_frame, text="Fin de corte (ej: k):").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        self.char_end = ctk.CTkEntry(controls_frame, width=50)
        self.char_end.insert(0, "k")
        self.char_end.grid(row=1, column=1, padx=5, pady=10)
        
        # Mostrar valor extraído grande
        self.extracted_value_label = ctk.CTkLabel(self.extraction_frame, text="--", font=ctk.CTkFont(size=60, weight="bold"), text_color="#F1C40F")
        self.extracted_value_label.grid(row=0, column=2, padx=20, pady=15, sticky="e")
        
        # Panel Medio: Configuraciones extra (Paridad, Flujo)
        self.top_settings = ctk.CTkFrame(self.main_view, height=50)
        self.top_settings.grid(row=1, column=0, pady=(0, 15), sticky="ew")
        
        ctk.CTkLabel(self.top_settings, text="Paridad:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5), pady=10)
        self.parity_cb = ctk.CTkComboBox(self.top_settings, width=150, values=["Ninguna (0)", "Impar (1)", "Par (2)", "Marca (3)", "Espacio (4)"])
        self.parity_cb.set("Ninguna (0)")
        self.parity_cb.pack(side="left", padx=5, pady=10)
        
        ctk.CTkLabel(self.top_settings, text="Control Flujo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(25, 5), pady=10)
        self.flow_cb = ctk.CTkComboBox(self.top_settings, width=150, values=["Ninguno (0)", "RTS/CTS (1)", "XON/XOFF (4)"])
        self.flow_cb.set("Ninguno (0)")
        self.flow_cb.pack(side="left", padx=5, pady=10)
        
        # Terminal view (Raw Data)
        self.console = ctk.CTkTextbox(self.main_view, font=ctk.CTkFont(family="Consolas", size=14), fg_color="#1E1E1E", text_color="#00FF00")
        self.console.grid(row=2, column=0, sticky="nsew")
        self.console.configure(state="disabled")

    def get_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        return ports if ports else ["No hay puertos"]

    def refresh_ports(self):
        self.port_cb.configure(values=self.get_ports())
        self.port_cb.set(self.get_ports()[0])

    def log(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", message + "\n")
        self.console.see("end")
        self.console.configure(state="disabled")
        
    def connect(self):
        port_name = self.port_cb.get()
        if not port_name or port_name == "No hay puertos":
            messagebox.showerror("Error", "Seleccione o escriba un puerto válido (ej. COM1).")
            return
            
        speed = int(self.speed_cb.get())
        data_bits_arg = int(self.data_cb.get())
        
        stop_val = self.stop_cb.get()
        if "1.5" in stop_val: stop_bits = serial.STOPBITS_ONE_POINT_FIVE
        elif "2" in stop_val: stop_bits = serial.STOPBITS_TWO
        else: stop_bits = serial.STOPBITS_ONE
            
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
            self.buffer = ""
            self.reader = SerialReader(
                port=port_name,
                baudrate=speed,
                bytesize=data_bits_arg,
                parity=parity,
                stopbits=stop_bits,
                xonxoff=xonxoff,
                rtscts=rtscts
            )
            self.reader.connect()
            self.log(f"--- Abriendo {port_name} ---")
            self.log("--- Parametrizando Puerto ---")
            self.log("--- Puerto Listo ---")
            
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            
            self.reader.start_reading(
                on_data_callback=self.on_data_received,
                on_error_callback=self.on_error
            )
            
        except Exception as e:
            messagebox.showerror("Error de Conexión", str(e))

    def process_buffer(self, text):
        c_start = self.char_start.get()
        c_end = self.char_end.get()
        
        if c_start and c_end:
            start_idx = text.find(c_start)
            end_idx = text.find(c_end, start_idx + 1) if start_idx != -1 else text.find(c_end)
            
            if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
                # Extraemos el valor entre el caracter de inicio (exclusivo) y fin (exclusivo)
                # Opcionalmente, si quieren incluir el signo, extraemos desde start_idx
                # La lógica clásica es tomar todo después del + y antes de la k, y quitar espacios.
                value = text[start_idx+1:end_idx].strip()
                self.extracted_value_label.configure(text=value)

    def on_data_received(self, char_val, bit):
        self.after(0, self.log, f"=>>[{char_val}|{bit}]")
        
        # Lógica de acumulación en buffer para extraer el valor
        self.buffer += char_val
        # Si recibimos Enter (13 o 10), procesamos la linea
        if bit == 10 or bit == 13:
            if len(self.buffer.strip()) > 0:
                self.after(0, self.process_buffer, self.buffer)
            self.buffer = ""

    def on_error(self, error_msg):
        self.after(0, self.log, f"Error leyendo: {error_msg}")
        self.after(0, self.disconnect)

    def disconnect(self):
        if self.reader:
            self.reader.disconnect()
            self.reader = None
        self.log("--- Cerrado ---")
        self.connect_btn.configure(state="normal")
        self.disconnect_btn.configure(state="disabled")

if __name__ == "__main__":
    app = SerialReaderApp()
    app.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect(), app.destroy()))
    app.mainloop()
