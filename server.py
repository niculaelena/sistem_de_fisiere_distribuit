# server.py
import socket
import threading
import os
import json
import base64

SHARED_DIR = './shared'
clients = []

def broadcast(data, sender=None):
    for client in clients:
        if client != sender:
            try:
                client.sendall(data)
            except:
                clients.remove(client)

def handle_client(conn, addr):
    print(f"[+] Client conectat: {addr}")
    clients.append(conn)

    try:
        while True:
            data = conn.recv(16384)
            if not data:
                break

            msg = json.loads(data.decode())

            if msg["action"] == "sync_request":
                file_list = []
                for root, _, files in os.walk(SHARED_DIR):
                    for name in files:
                        rel_path = os.path.relpath(os.path.join(root, name), SHARED_DIR)
                        full_path = os.path.join(SHARED_DIR, rel_path)
                        with open(full_path, 'rb') as f:
                            encoded = base64.b64encode(f.read()).decode()
                        file_list.append({"path": rel_path, "content": encoded})

                payload = {"action": "sync_data", "files": file_list}
                conn.sendall(json.dumps(payload).encode())

            elif msg["action"] == "file_change":
                path = os.path.join(SHARED_DIR, msg["path"])

                if msg["change"] in ["create", "modify"]:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "wb") as f:
                        f.write(base64.b64decode(msg["content"]))

                elif msg["change"] == "delete":
                    if os.path.exists(path):
                        os.remove(path)

                elif msg["change"] == "rename":
                    new_path = os.path.join(SHARED_DIR, msg["new_path"])
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)
                    if os.path.exists(path):
                        os.rename(path, new_path)

                broadcast(data, sender=conn)

    except Exception as e:
        print(f"[!] Eroare cu {addr}: {e}")
    finally:
        conn.close()
        clients.remove(conn)

def main():
    os.makedirs(SHARED_DIR, exist_ok=True)
    s = socket.socket()
    s.bind(('0.0.0.0', 9999))
    s.listen()
    print("[*] Serverul ascultă pe portul 9999...")

    while True:
        conn, addr = s.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    main()