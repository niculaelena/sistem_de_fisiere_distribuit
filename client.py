# client.py
import socket
import threading
import os
import json
import base64
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileMovedEvent

LOCAL_DIR = os.environ.get("LOCAL_DIR", "./local")

def encode_file(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

def decode_to_file(encoded_str, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(base64.b64decode(encoded_str.encode()))

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, conn):
        self.conn = conn

    def on_modified(self, event):
        if not event.is_directory:
            rel_path = os.path.relpath(event.src_path, LOCAL_DIR)
            content = encode_file(event.src_path)
            msg = {"action": "file_change", "change": "modify", "path": rel_path, "content": content}
            self.conn.sendall(json.dumps(msg).encode())

    def on_created(self, event):
        if not event.is_directory:
            rel_path = os.path.relpath(event.src_path, LOCAL_DIR)
            content = encode_file(event.src_path)
            msg = {"action": "file_change", "change": "create", "path": rel_path, "content": content}
            self.conn.sendall(json.dumps(msg).encode())

    def on_deleted(self, event):
        if not event.is_directory:
            rel_path = os.path.relpath(event.src_path, LOCAL_DIR)
            msg = {"action": "file_change", "change": "delete", "path": rel_path}
            self.conn.sendall(json.dumps(msg).encode())

    def on_moved(self, event: FileMovedEvent):
        rel_src = os.path.relpath(event.src_path, LOCAL_DIR)
        rel_dest = os.path.relpath(event.dest_path, LOCAL_DIR)
        msg = {"action": "file_change", "change": "rename", "path": rel_src, "new_path": rel_dest}
        self.conn.sendall(json.dumps(msg).encode())

def listen_to_server(conn):
    while True:
        try:
            data = conn.recv(16384)
            if not data:
                break
            msg = json.loads(data.decode())

            if msg["action"] == "sync_data":
                for f in msg["files"]:
                    path = os.path.join(LOCAL_DIR, f["path"])
                    decode_to_file(f["content"], path)

            elif msg["action"] == "file_change":
                full_path = os.path.join(LOCAL_DIR, msg["path"])

                if msg["change"] in ["create", "modify"]:
                    decode_to_file(msg["content"], full_path)

                elif msg["change"] == "delete":
                    if os.path.exists(full_path):
                        os.remove(full_path)

                elif msg["change"] == "rename":
                    new_path = os.path.join(LOCAL_DIR, msg["new_path"])
                    if os.path.exists(full_path):
                        os.rename(full_path, new_path)

        except Exception as e:
            print(f"[!] Eroare client: {e}")
            break

def main():
    os.makedirs(LOCAL_DIR, exist_ok=True)
    conn = socket.socket()
    conn.connect(('127.0.0.1', 9999))

    conn.sendall(json.dumps({"action": "sync_request"}).encode())
    threading.Thread(target=listen_to_server, args=(conn,), daemon=True).start()

    handler = ChangeHandler(conn)
    observer = Observer()
    observer.schedule(handler, LOCAL_DIR, recursive=True)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

if __name__ == '__main__':
    try:
        conn.connect(('127.0.0.1', 9999))
    except ConnectionRefusedError:
        raise
