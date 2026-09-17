import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import serial
import serial.tools.list_ports
from serial_reader import SerialReader
import base64
from io import BytesIO
from PIL import Image

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
        self.disconnect_btn.grid(row=12, column=0, padx=20, pady=(5, 10), sticky="ew")
        
        github_b64 = b"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAMAAADXqc3KAAACu1BMVEUAAAAcHBwcICQcHiMbHyMaHyQbHyMbHyMbHyMbHyMbHyMcHyQcICQeHh4AAAAeHiQcHiMaHyMbHyMaHyMWISEcHiMbHiMbHyMbHyMXIyMkJCQaHiQbICMbHyMbHyMbHyMbHiMXFy4cICUaHyMbHyMbHyMaHyMcISEaHiIbHyQbHyMaHiIbHyMbHyMbHiQbHyIbHyMaHyMaICMbHyMbHyMbHyMbHyMcHiIAAAAZISEbHyMaIiIaHSQbHyQbHiQAAEAaICQrKysbICMbHyIaIyMYHiQbHiMbHyMcISEbHiIbHyIcHiQbHyMcHyIcHyMbHyIbHyMzMzMbHyMbHiQbHiQcHyMaICQbHyMcHiIbHyMbHyMbHiMbHyMbHiIbHyMcHyIVFSsXHycAAAAfHx8bHyMaICIaHyMbICMaHiIaICAcHyMbHiIcHiIaHyQYJCQcICQbHyMbHyMbHyMcHyIbGygbHyQbHyMcHyMbHiMgICAcHyIcICQdHScSJCQaHyMbHyMaHyQZHyUgICAbICQcHyIcHyMbICMcHyIbHyMbICQdHSIbHyMbHiMcHBwbICMaGiYaICMbHiQbHyMbICMbICIbHyQbHyQaGhobHyMdISUcHyMdHSMbHyIbICMbHyQcHiMbHyMaHyMaHyQcHyMbHyMgICAbHyMZHSEbICQaICIaISQbHyMdHSQbHyMbHyIaHiMbHyMbICMbICMbHyMbHyMcHyQbICMaHiIbHyQbHyMiIiIbHyMbICIbIiIbHyQcICIaHiMYICAcHCYcHCMbHyMbHyMcHCIcICMZHiMcICMbHyQbICQdHSIbHiMcHyMbHyIaHiMaICMbHyMaHyMcHyMcHyMUJycaHyMaISEaHiIcICMcHCIaHyQcHyIbHyMbHyMaHiEaHyQbHyMbGyQbICIaHyMbHiMbHyP////+rYhMAAAA53RSTlMAEkBlhaW+0eTu9WQ/EQErba7jbBdmqOinFgdNqvr8u14LN5vw75o2PLPERMfOVc/NOpH9/qLrbwMfxR5O7VQEiAbKyB0q4uYuTEtc+1tR9PYFxsmPi0/sudP52tiG3ZQMIQIZw1nLZ8EopkN3YxWBtvjzShOe5cygCFOAGg6S4aQpGDicSZDe6bo135gJXxRYXbSxaZbXCq0+8SyrYDlu23Rrr/cQtT15YUaDI9ajuLzSob/cnZl+enMPQXAm0Hg7IBske+oliTPCrHE0n5OVdldCt9WKDecnf0gtMVryhEUyvRyy1JfEOwSMAAAAmklEQVR4nGNggALR52AgyoAKniMBJGH75yjAESbu/RwN+ELEA9HFYXqAjAyELQwMOVB70OxDiIAoVywSoth1MDOgOx3mKTC5ClUiCS6BFgwMcAkeVHE+uASalnpcEhChuSDSBFm8Axpc6GEN58PMiwKJHkWOlOfPCxngepAjyxHToEAI5+7z52dQJHxhPPvnKEY5MqCYgMbACQCEVd0ovvSH6QAAAABJRU5ErkJggg=="
        github_img_data = base64.b64decode(github_b64)
        self.github_icon = ctk.CTkImage(light_image=Image.open(BytesIO(github_img_data)), dark_image=Image.open(BytesIO(github_img_data)), size=(30, 30))
        
        self.github_btn = ctk.CTkButton(self.sidebar, image=self.github_icon, text=" Developed by jesusalbujas", fg_color="transparent", hover_color="#34495E", text_color="#3498DB", font=ctk.CTkFont(size=14, underline=True), command=self.open_github, compound="left")
        self.github_btn.grid(row=13, column=0, padx=20, pady=(10, 20), sticky="s")
        
    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/jesusalbujas/serialport")

    def create_main_view(self):
        self.main_view = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.main_view.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_view.grid_rowconfigure(3, weight=1) # El textbox ocupa el resto
        self.main_view.grid_columnconfigure(0, weight=1)
        
        # Top Panel: Data extraction
        self.extraction_frame = ctk.CTkFrame(self.main_view, height=120)
        self.extraction_frame.grid(row=0, column=0, pady=(0, 15), sticky="ew")
        self.extraction_frame.grid_columnconfigure(2, weight=1)
        
                controls_frame = ctk.CTkFrame(self.extraction_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=0, padx=15, pady=10, sticky="w")
        
        ctk.CTkLabel(controls_frame, text="Char Inicio (ASCII):").grid(row=0, column=0, sticky="w", padx=5)
        self.char_start_ascii = ctk.CTkEntry(controls_frame, width=50)
        self.char_start_ascii.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(controls_frame, text="Longitud Trama:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.frame_length = ctk.CTkEntry(controls_frame, width=50)
        self.frame_length.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(controls_frame, text="Corte Inicio (Pos):").grid(row=0, column=2, sticky="w", padx=(15, 5))
        self.cut_start = ctk.CTkEntry(controls_frame, width=50)
        self.cut_start.grid(row=0, column=3, padx=5)
        
        ctk.CTkLabel(controls_frame, text="Corte Fin (Pos):").grid(row=1, column=2, sticky="w", padx=(15, 5), pady=5)
        self.cut_end = ctk.CTkEntry(controls_frame, width=50)
        self.cut_end.grid(row=1, column=3, padx=5, pady=5)
        
        # Display large extracted value
        right_frame = ctk.CTkFrame(self.extraction_frame, fg_color="transparent")
        right_frame.grid(row=0, column=2, padx=20, pady=10, sticky="e")
        
        ctk.CTkLabel(right_frame, text="VALOR EXTRAÍDO", font=ctk.CTkFont(size=24, weight="bold")).pack()
        self.extracted_value_label = ctk.CTkLabel(right_frame, text="--", font=ctk.CTkFont(size=120, weight="bold"), text_color="#F1C40F")
        self.extracted_value_label.pack()
        
        # Middle Panel: Extra Settings
        self.top_settings = ctk.CTkFrame(self.main_view, height=50)
        self.top_settings.grid(row=1, column=0, pady=(0, 15), sticky="ew")
        
        ctk.CTkLabel(self.top_settings, text="Paridad:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5), pady=10)
        self.parity_cb = ctk.CTkComboBox(self.top_settings, width=150, values=["Ninguna (0)", "Impar (1)", "Par (2)", "Marca (3)", "Espacio (4)"])
        self.parity_cb.set("Par (2)")
        self.parity_cb.pack(side="left", padx=5, pady=10)
        
        ctk.CTkLabel(self.top_settings, text="Control Flujo:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(25, 5), pady=10)
        self.flow_cb = ctk.CTkComboBox(self.top_settings, width=150, values=["None", "RTSCTS IN", "RTSCTS OUT", "XON/XOFF IN", "XON/XOFF OUT"])
        self.flow_cb.set("RTSCTS IN")
        self.flow_cb.pack(side="left", padx=5, pady=10)
        
        # Console Header
        self.console_header = ctk.CTkFrame(self.main_view, fg_color="transparent")
        self.console_header.grid(row=2, column=0, sticky="ew", pady=(10, 5))
        ctk.CTkLabel(self.console_header, text="Log de Datos:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(self.console_header, text="Limpiar Log", width=100, command=self.clear_log)
        self.clear_btn.pack(side="right", padx=5)
        
        # Terminal view (Raw Data)
        self.console = ctk.CTkTextbox(self.main_view, font=ctk.CTkFont(family="Consolas", size=14), fg_color="#1E1E1E", text_color="#00FF00")
        self.console.grid(row=3, column=0, sticky="nsew")
        self.console.configure(state="disabled")

    def clear_log(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        self.extracted_value_label.configure(text="--")
        self.buffer = ""

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
        xonxoff = "XON/XOFF" in flow_str
        rtscts = "RTSCTS" in flow_str
        
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

    def auto_fill_config(self, text):
        # Clean newlines
        clean_text = text.replace('\r', '').replace('\n', '')
        
        # 1. Ignore short frames
        if len(clean_text) < 8:
            return
            
        # 2. Start character
        start_ascii = ord(clean_text[0])
        # Ignore non-alphanumeric chars
        if not (65 <= start_ascii <= 90 or 97 <= start_ascii <= 122 or 48 <= start_ascii <= 57):
            return
            
        # 3. Find number boundaries
        import re
        match = re.search(r'[-+]?\s*\d+\.?\d*\s*[a-zA-Z]*', clean_text)
        if match:
                        self.char_start_ascii.delete(0, "end")
            self.char_start_ascii.insert(0, str(start_ascii))
            
            # Leave length blank to use newline as terminator
            self.frame_length.delete(0, "end")
            
            self.cut_start.delete(0, "end")
            self.cut_start.insert(0, str(match.start()))
            
            self.cut_end.delete(0, "end")
            self.cut_end.insert(0, str(match.end()))
            
            # Process buffer immediately
            self.process_buffer(clean_text)

    def process_buffer(self, text):
        try:
            start_idx = int(self.cut_start.get())
            end_idx = int(self.cut_end.get())
            
            # Cut using indices and format cleanly
            if len(text) >= end_idx:
                # Extraemos y condensamos los espacios múltiples en uno solo
                raw_val = text[start_idx:end_idx]
                value = " ".join(raw_val.split())
                self.extracted_value_label.configure(text=value)
        except ValueError:
            pass

    def on_data_received(self, char_val, bit):
        # We don't log byte-by-byte to prevent UI lag on continuous streams
        
        try:
            start_char_ascii = int(self.char_start_ascii.get())
        except ValueError:
            start_char_ascii = -1
            
        try:
            expected_length = int(self.frame_length.get())
        except ValueError:
            expected_length = 0
            
        # Reset buffer if empty
        if len(self.buffer) == 0 and start_char_ascii != -1:
            if bit == start_char_ascii:
                self.buffer = char_val
            return # Ignore if empty and not start char
            
        self.buffer += char_val
            
        # Check expected length
        if expected_length > 0 and len(self.buffer) == expected_length:
            self.after(0, self.log, f"Trama recibida: {self.buffer}")
            self.after(0, self.process_buffer, self.buffer)
            self.buffer = ""
            
        # Fallback: Process on newline
        elif bit == 10 or bit == 13:
            if len(self.buffer.strip()) > 0:
                self.after(0, self.log, f"Trama recibida: {self.buffer}")
                # Auto-calculate if fields empty
                if self.char_start_ascii.get() == "" and self.frame_length.get() == "":
                    self.after(0, self.auto_fill_config, self.buffer)
                else:
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
