import socket
import os
import sys
import json
import base64
import threading
import time
import hashlib

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9000
LOCAL_FOLDER = sys.argv[1] if len(sys.argv) > 1 else "client_data"

def file_hash(content_bytes):
    return hashlib.md5(content_bytes).hexdigest()

def get_local_files_info():
    info = {}
    for root, _, files in os.walk(LOCAL_FOLDER):
        for file in files:
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, LOCAL_FOLDER)
            with open(path, 'rb') as f:
                content = f.read()
                info[rel_path] = {
                    'hash': file_hash(content),
                    'content': base64.b64encode(content).decode('utf-8')
                }
    return info

def detect_changes(old, new):
    changes = []
    old_paths = set(old.keys())
    new_paths = set(new.keys())

    for path in old_paths - new_paths:
        changes.append({"type": "delete", "path": path})
    for path in new_paths - old_paths:
        changes.append({"type": "create", "path": path, "content": new[path]['content']})
    for path in old_paths & new_paths:
        if old[path]['hash'] != new[path]['hash']:
            changes.append({"type": "modify", "path": path, "content": new[path]['content']})

    return changes

def apply_change(change):
    ctype = change["type"]
    rel_path = change.get("path")

    if ctype in ("create", "modify"):
        abs_path = os.path.join(LOCAL_FOLDER, rel_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        content = base64.b64decode(change["content"].encode('utf-8'))
        with open(abs_path, 'wb') as f:
            f.write(content)
        print(f"[SYNC] {ctype.upper()} {rel_path}")

    elif ctype == "delete":
        abs_path = os.path.join(LOCAL_FOLDER, rel_path)
        if os.path.exists(abs_path):
            os.remove(abs_path)
        print(f"[SYNC] DELETE {rel_path}")

    elif ctype == "rename":
        old_path = os.path.join(LOCAL_FOLDER, change["old_path"])
        new_path = os.path.join(LOCAL_FOLDER, change["new_path"])
        if os.path.exists(old_path):
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            os.rename(old_path, new_path)
        print(f"[SYNC] RENAME {change['old_path']} -> {change['new_path']}")

def listen_for_server(sock):
    while True:
        try:
            data = sock.recv(10_000_000)
            if not data:
                break
            msg = json.loads(data.decode('utf-8'))
            if msg["type"] == "sync":
                print("[SERVER] Sincronizare initiala...")
                for rel_path, content in msg["data"].items():
                    apply_change({"type": "create", "path": rel_path, "content": content})
            elif msg["type"] == "sync_changes":
                print(f"[SERVER] Primit modificari de sincronizat: {len(msg['changes'])} fisiere")
                for change in msg["changes"]:
                    apply_change(change)
        except Exception as e:
            print(f"[ERROR] {e}")
            break

def watch_and_send_changes(sock):
    old_state = get_local_files_info()
    while True:
        time.sleep(2)
        new_state = get_local_files_info()
        changes = detect_changes(old_state, new_state)
        if changes:
            try:
                msg = {"type": "update_changes", "changes": changes}
                sock.sendall(json.dumps(msg).encode('utf-8'))
                print(f"[CLIENT] Trimite modificari catre server: {[c['type'] + ' ' + c['path'] for c in changes]}")
                old_state = new_state
            except Exception as e:
                print(f"[ERROR] {e}")
                break

def main():
    if not os.path.exists(LOCAL_FOLDER):
        os.makedirs(LOCAL_FOLDER)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_HOST, SERVER_PORT))
        print("[CLIENT] Conectat la server.")

        threading.Thread(target=listen_for_server, args=(s,), daemon=True).start()
        threading.Thread(target=watch_and_send_changes, args=(s,), daemon=True).start()

        input("\n[CLIENT] Apasa ENTER pentru a iesi...\n")

if __name__ == "__main__":
    main()
