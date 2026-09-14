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
        self.geometry("800x550")
        self.minsize(700, 500)
        
        self.reader = None
        
        # Grid layout (1 row, 2 columns)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.create_sidebar()
        self.create_main_view()
        
    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        
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
        self.connect_btn.grid(row=9, column=0, padx=20, pady=(10, 5), sticky="ew")
        
        self.disconnect_btn = ctk.CTkButton(self.sidebar, text="DESCONECTAR", fg_color="#C0392B", hover_color="#E74C3C", font=ctk.CTkFont(weight="bold"), command=self.disconnect, state="disabled")
        self.disconnect_btn.grid(row=10, column=0, padx=20, pady=(5, 20), sticky="ew")
        
    def create_main_view(self):
        self.main_view = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_view.grid_rowconfigure(1, weight=1)
        self.main_view.grid_columnconfigure(0, weight=1)
        
        # Header settings (Parity and Flow control in one row)
        self.top_settings = ctk.CTkFrame(self.main_view, height=50)
        self.top_settings.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        
        ctk.CTkLabel(self.top_settings, text="Paridad:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5), pady=10)
        self.parity_cb = ctk.CTkComboBox(self.top_settings, width=150, values=["Ninguna (0)", "Impar (1)", "Par (2)", "Marca (3)", "Espacio (4)"])
        self.parity_cb.set("Ninguna (0)")
        self.parity_cb.pack(side="left", padx=5, pady=10)
        
        ctk.CTkLabel(self.top_settings, text="Control Flujo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(25, 5), pady=10)
        self.flow_cb = ctk.CTkComboBox(self.top_settings, width=150, values=["Ninguno (0)", "RTS/CTS (1)", "XON/XOFF (4)"])
        self.flow_cb.set("Ninguno (0)")
        self.flow_cb.pack(side="left", padx=5, pady=10)
        
        # Terminal view
        self.console = ctk.CTkTextbox(self.main_view, font=ctk.CTkFont(family="Consolas", size=14), fg_color="#1E1E1E", text_color="#00FF00")
        self.console.grid(row=1, column=0, sticky="nsew")
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

    def on_data_received(self, char_val, bit):
        self.after(0, self.log, f"=>>[{char_val}|{bit}]")

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
