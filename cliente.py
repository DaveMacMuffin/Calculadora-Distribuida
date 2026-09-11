import tkinter as tk
from tkinter import messagebox
import socket
import threading
import json
import uuid
from datetime import datetime

class ClientCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora Cliente")
        self.root.geometry("320x450")
        
        # GEneracion de ID
        self.client_id = str(uuid.uuid4())[:8]
        self.log_file = f"log_cliente_{self.client_id}.txt"
        
        # palleta de colores para la calculadora
        self.bg_color = "#0B132B"
        self.btn_color = "#1C2541"
        self.accent_color = "#4CC9F0"
        
        self.root.configure(bg=self.bg_color)
        
        self.create_widgets()
        self.connect_to_middleware()

    def create_widgets(self):
        self.display_var = tk.StringVar()
        
        screen_frame = tk.Frame(
            self.root, 
            bg=self.bg_color, 
            highlightbackground=self.accent_color, 
            highlightcolor=self.accent_color, 
            highlightthickness=2
        )
        screen_frame.pack(pady=20, padx=15, fill="x")

        self.display = tk.Entry(
            screen_frame,
            textvariable=self.display_var,
            font=("Arial", 24),
            bg=self.bg_color,
            fg=self.accent_color,
            insertbackground=self.accent_color,
            bd=0,
            justify="right"
        )
        self.display.pack(ipadx=10, ipady=15, fill="x")

        btn_frame = tk.Frame(self.root, bg=self.bg_color)
        btn_frame.pack(padx=15, pady=20, fill="both", expand=True)

        buttons = [
            ('C', 0, 0), ('(', 0, 1), (')', 0, 2), ('/', 0, 3),
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('*', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('-', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('+', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('^', 4, 2), ('=', 4, 3)
        ]

        for (text, row, col) in buttons:
            self.create_button(btn_frame, text, row, col)

        for i in range(5):
            btn_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            btn_frame.grid_columnconfigure(i, weight=1)

    def create_button(self, parent, text, row, col):
        action = lambda x=text: self.on_button_click(x)
        btn = tk.Button(
            parent,
            text=text,
            font=("Arial", 16, "bold"),
            bg=self.btn_color,
            fg=self.accent_color,
            activebackground=self.bg_color,
            activeforeground=self.accent_color,
            bd=1,
            relief="solid",
            command=action
        )
        btn.config(highlightbackground=self.accent_color, highlightthickness=1)
        btn.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)

    def on_button_click(self, char):
        if char == 'C':
            self.display_var.set("")
        elif char == '=':
            self.request_calculation()
        else:
            current = self.display_var.get()
            if current == "Calculando...":
                current = ""
            self.display_var.set(current + char)

    def connect_to_middleware(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(('127.0.0.1', 5000))
            # Mensaje de autenticación
            self.sock.sendall(b"AUTH:CLIENT\n")
            
            # Hilo para recibir respuestas
            threading.Thread(target=self.listen_for_results, daemon=True).start()
            self.log_action("SISTEMA", "Conectado al middleware exitosamente.")
        except Exception as e:
            messagebox.showerror("Error de Conexión", "No se pudo conectar al Middleware en el puerto 5000.")
            self.log_action("ERROR", f"Conexión fallida: {e}")

    def log_action(self, action_type, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{action_type}] {message}\n")

    def request_calculation(self):
        expression = self.display_var.get()
        if not expression or expression == "Calculando...":
            return
            
        self.log_action("SOLICITUD", f"Enviando operación: {expression}")
        
        payload = json.dumps({"client_id": self.client_id, "expr": expression}) + "\n"
        try:
            self.sock.sendall(payload.encode('utf-8'))
            self.display_var.set("Calculando...")
        except Exception as e:
            messagebox.showerror("Error", "Se perdió la conexión con el middleware.")
            self.log_action("ERROR", "Fallo al enviar solicitud.")

    def listen_for_results(self):
        f_stream = self.sock.makefile('r', encoding='utf-8')
        while True:
            try:
                line = f_stream.readline()
                if not line:
                    break
                    
                data = json.loads(line)
                
                # logea resultados recibidos incluso los broadcast de otros clientes
                self.log_action("RESULTADO_RECIBIDO", f"Operación: {data['expr']} = {data['result']} | Server: {data['server_id']} | Solicitado por: {data['client_id']}")
                
                # Actualizar pantalla solo si el resultado era para ese cliente
                if data.get("client_id") == self.client_id:
                    self.root.after(0, self.display_var.set, data['result'])
                    
            except Exception as e:
                self.log_action("ERROR", f"Fallo al leer respuesta: {e}")
                break


root = tk.Tk()
app = ClientCalculator(root)
root.mainloop()
