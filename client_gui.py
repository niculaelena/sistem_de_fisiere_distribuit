# client_gui.py (versiune actualizată fără „Reîncarcă lista”)
import os
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from client import main as run_sync_client

LOCAL_DIR = './local'
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9999

def test_server_connection(host=SERVER_HOST, port=SERVER_PORT, timeout=2):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def ensure_local_dir():
    os.makedirs(LOCAL_DIR, exist_ok=True)

def show_connection_error():
    def try_again():
        if test_server_connection():
            error_window.destroy()
            launch_gui()
        else:
            messagebox.showwarning("Încă nu merge", "Serverul tot nu răspunde.")

    error_window = tk.Tk()
    error_window.title("Conexiune eșuată")
    tk.Label(error_window, text="Nu s-a putut conecta la server.\nTe rog rulează: python server.py", padx=20, pady=10).pack()
    tk.Button(error_window, text="Reîncearcă", command=try_again, width=20).pack(pady=10)
    tk.Button(error_window, text="Ieși", command=error_window.destroy, width=20).pack()
    error_window.mainloop()

def start_sync_thread():
    thread = threading.Thread(target=run_sync_client, daemon=True)
    thread.start()

def launch_gui():
    ensure_local_dir()

    app = tk.Tk()
    app.title("Client DFS")
    app.geometry("420x400")
    app.resizable(False, False)

    style = ttk.Style()
    style.configure("TButton", padding=6, font=("Segoe UI", 10))

    def create_file():
        name = simpledialog.askstring("Crează fișier", "Introdu numele fișierului:")
        if name:
            path = os.path.join(LOCAL_DIR, name)
            if os.path.exists(path):
                messagebox.showwarning("Eroare", "Fișierul există deja.")
                return
            with open(path, 'w') as f:
                f.write("")
            refresh_list()

    def delete_file():
        selection = file_listbox.curselection()
        if not selection:
            return
        filename = file_listbox.get(selection[0])
        path = os.path.join(LOCAL_DIR, filename)
        os.remove(path)
        refresh_list()

    def rename_file():
        selection = file_listbox.curselection()
        if not selection:
            return
        old_name = file_listbox.get(selection[0])
        new_name = simpledialog.askstring("Redenumește fișier", f"Redenumește '{old_name}' în:")
        if new_name:
            os.rename(os.path.join(LOCAL_DIR, old_name), os.path.join(LOCAL_DIR, new_name))
            refresh_list()

    def refresh_list():
        file_listbox.delete(0, tk.END)
        for file in sorted(os.listdir(LOCAL_DIR)):
            full_path = os.path.join(LOCAL_DIR, file)
            if os.path.isfile(full_path):
                file_listbox.insert(tk.END, file)

    frame_buttons = tk.Frame(app)
    frame_buttons.pack(pady=10)

    ttk.Button(frame_buttons, text="Crează fișier", command=create_file).grid(row=0, column=0, padx=5)
    ttk.Button(frame_buttons, text="Șterge fișier", command=delete_file).grid(row=0, column=1, padx=5)
    ttk.Button(frame_buttons, text="Redenumește", command=rename_file).grid(row=0, column=2, padx=5)

    frame_list = tk.Frame(app)
    frame_list.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    scrollbar = tk.Scrollbar(frame_list)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    file_listbox = tk.Listbox(frame_list, width=50, height=15, yscrollcommand=scrollbar.set)
    file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=file_listbox.yview)

    refresh_list()
    start_sync_thread()
    app.mainloop()

if __name__ == "__main__":
    if test_server_connection():
        launch_gui()
    else:
        show_connection_error()
