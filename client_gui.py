# client_gui.py
import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import threading
from client import main as run_sync_client

LOCAL_DIR = './local'

def create_file():
    name = simpledialog.askstring("Nume fișier", "Introdu numele fișierului:")
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
    new_name = simpledialog.askstring("Redenumește", f"Redenumește {old_name} în:")
    if new_name:
        os.rename(os.path.join(LOCAL_DIR, old_name), os.path.join(LOCAL_DIR, new_name))
        refresh_list()

def refresh_list():
    file_listbox.delete(0, tk.END)
    for file in os.listdir(LOCAL_DIR):
        if os.path.isfile(os.path.join(LOCAL_DIR, file)):
            file_listbox.insert(tk.END, file)

def start_sync_thread():
    thread = threading.Thread(target=run_sync_client, daemon=True)
    thread.start()

app = tk.Tk()
app.title("Client DFS")

btn_create = tk.Button(app, text="Crează fișier", command=create_file)
btn_create.pack()

btn_delete = tk.Button(app, text="Șterge fișier", command=delete_file)
btn_delete.pack()

btn_rename = tk.Button(app, text="Redenumește fișier", command=rename_file)
btn_rename.pack()

file_listbox = tk.Listbox(app, width=50)
file_listbox.pack(pady=10)

btn_refresh = tk.Button(app, text="Reîncarcă lista", command=refresh_list)
btn_refresh.pack()

refresh_list()
start_sync_thread()
app.mainloop()