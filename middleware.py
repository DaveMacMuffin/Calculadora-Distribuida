import socket
import threading

# Listas tipos de conexiones
clients = []
servers = []
clients_lock = threading.Lock()
servers_lock = threading.Lock()

def handle_connection(conn, addr):
    f = conn.makefile('r', encoding='utf-8')
    conn_type = "UNKNOWN"
    try:
        # Lee primer mensaje para identificar rol
        auth_msg = f.readline().strip()
        
        if auth_msg == "AUTH:CLIENT":
            conn_type = "CLIENT"
            print(f"[MIDDLEWARE] Nuevo Cliente conectado desde {addr}")
            with clients_lock:
                clients.append(conn)
                
            while True:
                msg = f.readline()
                if not msg:
                    break
                print(f"[MIDDLEWARE] Solicitud de Cliente recibida, distribuyendo a servidores: {msg.strip()}")
                
                # Reenvía solicitud a todos los servidores
                with servers_lock:
                    for srv in servers:
                        try:
                            srv.sendall(msg.encode('utf-8'))
                        except Exception as e:
                            print(f"[MIDDLEWARE] Error enviando a servidor: {e}")

        elif auth_msg == "AUTH:SERVER":
            conn_type = "SERVER"
            print(f"[MIDDLEWARE] Nuevo Servidor conectado desde {addr}")
            with servers_lock:
                servers.append(conn)
                
            while True:
                msg = f.readline()
                if not msg:
                    break
                print(f"[MIDDLEWARE] Resultado de Servidor recibido, distribuyendo a clientes: {msg.strip()}")
                
                # Reenvía resultados a todos los clientes
                with clients_lock:
                    for cli in clients:
                        try:
                            cli.sendall(msg.encode('utf-8'))
                        except Exception as e:
                            print(f"[MIDDLEWARE] Error enviando a cliente: {e}")
        else:
            print(f"[MIDDLEWARE] Conexión no reconocida desde {addr}")

    except Exception as e:
        print(f"[MIDDLEWARE] Error en conexión {addr}: {e}")
    finally:
        print(f"[MIDDLEWARE] Desconexión de {conn_type} en {addr}")
        if conn_type == "CLIENT":
            with clients_lock:
                if conn in clients: clients.remove(conn)
        elif conn_type == "SERVER":
            with servers_lock:
                if conn in servers: servers.remove(conn)
        conn.close()

def start_middleware(host='0.0.0.0', port=5000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen()
    
    print(f"[MIDDLEWARE] Iniciado y escuchando en el puerto {port}")
    print("[MIDDLEWARE] Esperando conexiones de Clientes o Servidores...")
    
    while True:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("[MIDDLEWARE] Apagando...")
            break


start_middleware()