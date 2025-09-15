import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox

def get_formats():
    url = url_entry.get().strip()
    if not url:
        messagebox.showerror("Error", "Ingrese una URL válida")
        return
    
    ydl_opts = {'quiet': True}
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [(f"{f['format_id']} - {f['format_note']} - {f['ext']}", f['format_id']) for f in info['formats'] if f.get('vcodec') != 'none']
            
            format_combobox['values'] = [f[0] for f in formats]
            format_combobox.format_map = dict(formats)
            format_combobox.current(0)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron obtener los formatos:\n{e}")

def download_video():
    url = url_entry.get().strip()
    format_id = format_combobox.format_map.get(format_combobox.get())
    if not url or not format_id:
        messagebox.showerror("Error", "Ingrese una URL válida y seleccione un formato")
        return
    
    ydl_opts = {
        'format': format_id,
        'progress_hooks': [progress_hook]
    }
    
    def run_download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Éxito", "Descarga completada")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en la descarga:\n{e}")
    
    root.after(100, run_download)

def progress_hook(d):
    if d['status'] == 'downloading':
        progress_label.config(text=f"Descargando: {d['_percent_str']} - {d['_eta_str']} restantes")
    elif d['status'] == 'finished':
        progress_label.config(text="Descarga completada")

# Crear ventana
root = tk.Tk()
root.title("Descargador de Videos")
root.geometry("500x300")

# Elementos UI
url_label = tk.Label(root, text="URL del video:")
url_label.pack()
url_entry = tk.Entry(root, width=50)
url_entry.pack()

format_button = tk.Button(root, text="Obtener formatos", command=get_formats)
format_button.pack()

format_combobox = ttk.Combobox(root, width=50)
format_combobox.pack()

download_button = tk.Button(root, text="Descargar", command=download_video)
download_button.pack()

progress_label = tk.Label(root, text="")
progress_label.pack()

# Ejecutar app
root.mainloop()
