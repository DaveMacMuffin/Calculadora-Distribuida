import socket
import json
import re
import uuid
from datetime import datetime

class MathEngine:
    def calculate(self, expression):
        try:
            expr = expression.replace(" ", "")
            if expr.startswith("-"):
                expr = "0" + expr
            expr = expr.replace("(-", "(0-")

            tokens = re.findall(r'\d+\.\d+|\d+|[+\-*/^()]', expr)
            postfix = self.infix_to_postfix(tokens)
            result = self.evaluate_postfix(postfix)
            
            if result == int(result):
                return str(int(result))
            else:
                return str(round(result, 8))
                
        except Exception as e:
            return "Error"

    def infix_to_postfix(self, tokens):
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
        output = []
        op_stack = []

        for token in tokens:
            if re.match(r'\d+\.\d+|\d+', token):
                output.append(float(token))
            elif token == '(':
                op_stack.append(token)
            elif token == ')':
                while op_stack and op_stack[-1] != '(':
                    output.append(op_stack.pop())
                if op_stack:
                    op_stack.pop()
            elif token in precedence:
                while (op_stack and op_stack[-1] != '(' and 
                       ((token != '^' and precedence.get(op_stack[-1], 0) >= precedence[token]) or
                        (token == '^' and precedence.get(op_stack[-1], 0) > precedence[token]))):
                    output.append(op_stack.pop())
                op_stack.append(token)

        while op_stack:
            output.append(op_stack.pop())
        return output

    def evaluate_postfix(self, postfix):
        eval_stack = []
        for token in postfix:
            if isinstance(token, float):
                eval_stack.append(token)
            else:
                if len(eval_stack) < 2:
                    raise ValueError("Invalid Expression")
                b = eval_stack.pop()
                a = eval_stack.pop()
                
                if token == '+': eval_stack.append(a + b)
                elif token == '-': eval_stack.append(a - b)
                elif token == '*': eval_stack.append(a * b)
                elif token == '/': eval_stack.append(a / b)
                elif token == '^': eval_stack.append(a ** b)

        return eval_stack[0]

def start_server():
    server_id = str(uuid.uuid4())[:8]
    log_file = f"log_servidor_{server_id}.txt"
    engine = MathEngine()
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', 5000))
        # Mensaje de autenticación
        sock.sendall(b"AUTH:SERVER\n")
        print(f"[SERVIDOR {server_id}] Conectado al middleware exitosamente.")
    except Exception as e:
        print(f"[SERVIDOR] No se pudo conectar al middleware: {e}")
        return

    def log_action(message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    log_action("INICIO: Servidor iniciado y conectado al middleware.")

    f_stream = sock.makefile('r', encoding='utf-8')
    while True:
        try:
            line = f_stream.readline()
            if not line:
                print("[SERVIDOR] Conexión perdida con el middleware.")
                break
                
            data = json.loads(line)
            client_id = data.get("client_id")
            expr = data.get("expr")
            
            print(f"[SERVIDOR {server_id}] Procesando solicitud del cliente {client_id}: {expr}")
            
            # Ejecutar operacion
            result = engine.calculate(expr)
            
            # Loggeo de resultados
            log_action(f"OPERACION_PROCESADA: {expr} = {result} | Solicitante: {client_id}")
            
            # Retornar resultados
            response = {
                "client_id": client_id,
                "server_id": server_id,
                "expr": expr,
                "result": result
            }
            
            payload = json.dumps(response) + "\n"
            sock.sendall(payload.encode('utf-8'))
            
        except Exception as e:
            print(f"[SERVIDOR {server_id}] Error en el procesamiento: {e}")
            log_action(f"ERROR: {e}")
            break
            
    sock.close()


start_server()
