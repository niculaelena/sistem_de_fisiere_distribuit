import socket
import threading
import os
import json
import base64

SHARED_FOLDER = "shared"
HOST = '0.0.0.0'
PORT = 9000
clients = []

def get_file_data(folder):
    data = {}
    for root, _, files in os.walk(folder):
        for file in files:
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, folder)
            with open(path, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode('utf-8')
                data[rel_path] = encoded
    return data

def apply_file_data(folder, file_data):
    for rel_path, b64content in file_data.items():
        abs_path = os.path.join(folder, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'wb') as f:
            f.write(base64.b64decode(b64content.encode('utf-8')))
        print(f"[SERVER] File created/modified: {rel_path}")

def apply_changes(folder, changes):
    for change in changes:
        ctype = change["type"]
        rel_path = change.get("path", "")
        if ctype in ["create", "modify"]:
            abs_path = os.path.join(folder, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            content = base64.b64decode(change["content"].encode('utf-8'))
            with open(abs_path, 'wb') as f:
                f.write(content)
            print(f"[SERVER] {ctype.capitalize()} file: {rel_path}")
        elif ctype == "delete":
            abs_path = os.path.join(folder, rel_path)
            if os.path.exists(abs_path):
                os.remove(abs_path)
                print(f"[SERVER] Deleted file: {rel_path}")
        elif ctype == "rename":
            old_path = os.path.join(folder, change["old_path"])
            new_path = os.path.join(folder, change["new_path"])
            if os.path.exists(old_path):
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                os.rename(old_path, new_path)
                print(f"[SERVER] Renamed file: {change['old_path']} -> {change['new_path']}")

def broadcast_changes(origin_conn, changes):
    msg = json.dumps({"type": "sync_changes", "changes": changes}).encode('utf-8')
    for client in clients:
        if client != origin_conn:
            try:
                client.sendall(msg)
                print("[SERVER] Broadcasting changes to clients...")
            except:
                continue

def handle_client(conn, addr):
    print(f"[SERVER] [+] New client connected from {addr}")
    clients.append(conn)
    try:
        server_data = get_file_data(SHARED_FOLDER)
        conn.sendall(json.dumps({"type": "sync", "data": server_data}).encode('utf-8'))
        print(f"[SERVER] Sent full sync data to client {addr}")

        while True:
            data = conn.recv(10_000_000)
            if not data:
                break
            msg = json.loads(data.decode('utf-8'))
            if msg["type"] == "update":
                apply_file_data(SHARED_FOLDER, msg["data"])
                broadcast_changes(conn, [{"type": "create", "path": p, "content": c} for p, c in msg["data"].items()])
            elif msg["type"] == "update_changes":
                apply_changes(SHARED_FOLDER, msg["changes"])
                broadcast_changes(conn, msg["changes"])

    except Exception as e:
        print(f"[SERVER] [ERROR] {e}")
    finally:
        conn.close()
        if conn in clients:
            clients.remove(conn)
        print(f"[SERVER] [-] Client disconnected: {addr}")

def start_server():
    if not os.path.exists(SHARED_FOLDER):
        os.makedirs(SHARED_FOLDER)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[SERVER] Listening on {HOST}:{PORT}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()