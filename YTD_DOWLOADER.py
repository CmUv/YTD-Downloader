import yt_dlp
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

dest_folder = None


def select_folder():
    global dest_folder
    folder = filedialog.askdirectory(title="Seleccionar carpeta destino")
    if folder:
        dest_folder = folder
        folder_label.config(text=f"Carpeta destino: {dest_folder}")


import threading
import time

loading_popup = None
loading_label = None
loading_running = False


def show_loading_popup():
    global loading_popup, loading_label, loading_running
    loading_popup = tk.Toplevel(root)
    loading_popup.title("Por favor espere")
    loading_popup.geometry("200x80")
    loading_popup.resizable(False, False)
    loading_popup.transient(root)
    loading_popup.grab_set()  # Modal
    loading_popup.protocol("WM_DELETE_WINDOW", lambda: None)  # No cerrar con X
    # Agrega esta línea para quitar la barra de título (incluye botón cerrar)
    # loading_popup.overrideredirect(True)

    loading_label = ttk.Label(loading_popup, text="Cargando")
    loading_label.pack(expand=True, pady=20)

    loading_running = True
    animate_loading()


def animate_loading():
    if not loading_running:
        return
    current_text = loading_label.cget("text")
    if current_text.endswith("..."):
        new_text = "Cargando"
    else:
        new_text = current_text + "."
    loading_label.config(text=new_text)
    loading_label.after(500, animate_loading)


def hide_loading_popup():
    global loading_running, loading_popup
    loading_running = False
    if loading_popup is not None:
        loading_popup.destroy()
        loading_popup = None


def get_formats_thread():
    try:
        get_formats_core()
    finally:
        root.after(0, hide_loading_popup)


def get_formats():
    # Mostrar ventana modal y lanzar thread para no bloquear UI
    show_loading_popup()
    threading.Thread(target=get_formats_thread, daemon=True).start()


def get_formats_core():
    url = url_entry.get().strip()
    if not url:
        root.after(0, lambda: messagebox.showerror("Error", "Ingrese una URL válida"))
        return

    ydl_opts = {"quiet": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_formats = []
            audio_formats = []

            for f in info["formats"]:
                if f.get("vcodec") != "none":
                    video_formats.append(f)
                elif f.get("acodec") != "none":
                    audio_formats.append(f)

            # Limpiar treeviews en el hilo principal
            def update_ui():
                for tree in (video_tree, audio_tree):
                    for item in tree.get_children():
                        tree.delete(item)

                for f in video_formats:
                    if f.get("height"):
                        note = f"{f['height']}p"
                    elif f.get("resolution"):
                        note = f["resolution"]
                    else:
                        note = "Desconocida"

                    video_tree.insert(
                        "",
                        "end",
                        iid=f["format_id"],
                        values=(f["format_id"], note, f["ext"], note, f.get("fps", "")),
                    )

                for f in audio_formats:
                    abr = f.get("abr")
                    note = f"{int(abr)} kbps" if abr else "Desconocida"

                    audio_tree.insert(
                        "",
                        "end",
                        iid=f["format_id"],
                        values=(f["format_id"], note, f["ext"], abr or "", ""),
                    )

                if video_formats:
                    video_tree.selection_set(video_formats[0]["format_id"])
                if audio_formats:
                    audio_tree.selection_set(audio_formats[0]["format_id"])

            root.after(0, update_ui)

    except Exception as e:
        root.after(
            0,
            lambda e=e: messagebox.showerror(
                "Error", f"No se pudieron obtener los formatos:\n{e}"
            ),
        )


def download_video():
    global dest_folder
    url = url_entry.get().strip()
    selected_video = video_tree.selection()
    selected_audio = audio_tree.selection()

    if not url:
        messagebox.showerror("Error", "Ingrese una URL válida")
        return

    if not selected_video:
        messagebox.showerror("Error", "Seleccione un formato de video")
        return

    if not dest_folder:
        messagebox.showerror("Error", "Seleccione una carpeta destino")
        return

    format_id_video = selected_video[0]
    format_id_audio = selected_audio[0] if selected_audio else None

    if format_id_audio and format_id_audio != format_id_video:
        format_id = f"{format_id_video}+{format_id_audio}"
    else:
        format_id = format_id_video

    ydl_opts = {
        "format": format_id,
        "progress_hooks": [progress_hook],
        "noplaylist": True,
        "outtmpl": f"{dest_folder}/%(title)s.%(ext)s",
    }

    download_button.config(state="disabled")
    progress_label.config(text="Iniciando descarga...")
    progress_bar["value"] = 0

    def run_download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            messagebox.showinfo("Éxito", "Descarga completada")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo en la descarga:\n{e}")
        finally:
            download_button.config(state="normal")

    root.after(100, run_download)


def progress_hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        progress_label.config(text=f"Descargando... {percent} - Tiempo restante: {eta}")
        try:
            progress_bar["value"] = float(percent.strip("%"))
        except:
            pass
    elif d["status"] == "finished":
        progress_label.config(text="Descarga completada")
        progress_bar["value"] = 100


# Crear ventana principal
root = tk.Tk()
root.title("Descargador de Videos")
root.geometry("1200x800")
root.minsize(600, 400)
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

# Frame URL
frame_url = ttk.Frame(root, padding=10)
frame_url.grid(row=0, column=0, sticky="ew")

url_label = ttk.Label(frame_url, text="URL del video:")
url_label.pack(side="left")

url_entry = ttk.Entry(frame_url)
url_entry.pack(side="left", fill="x", expand=True, padx=5)

format_button = ttk.Button(frame_url, text="Obtener formatos", command=get_formats)
format_button.pack(side="left", padx=5)

# Frame formatos video y audio
frame_formats = ttk.Frame(root, padding=10)
frame_formats.grid(row=1, column=0, sticky="nsew")

frame_formats.columnconfigure(0, weight=1)
frame_formats.columnconfigure(1, weight=1)
frame_formats.rowconfigure(1, weight=1)

# Video formats
video_label = ttk.Label(frame_formats, text="Formatos de Video:")
video_label.grid(row=0, column=0, sticky="w")

video_tree = ttk.Treeview(
    frame_formats, columns=("ID", "Nota", "Ext", "Resolución", "FPS"), show="headings"
)
for col in ("ID", "Nota", "Ext", "Resolución", "FPS"):
    video_tree.heading(col, text=col)
    video_tree.column(col, width=80 if col != "Nota" else 150, anchor="center")
video_tree.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=5)

# Audio formats
audio_label = ttk.Label(frame_formats, text="Formatos de Audio:")
audio_label.grid(row=0, column=1, sticky="w")

audio_tree = ttk.Treeview(
    frame_formats, columns=("ID", "Nota", "Ext", "Bitrate (kbps)", ""), show="headings"
)
for col in ("ID", "Nota", "Ext", "Bitrate (kbps)", ""):
    audio_tree.heading(col, text=col)
    audio_tree.column(col, width=80 if col != "Nota" else 150, anchor="center")
audio_tree.grid(row=1, column=1, sticky="nsew", pady=5)

# Frame carpeta destino y descarga
frame_download = ttk.Frame(root, padding=10)
frame_download.grid(row=2, column=0, sticky="ew")

folder_button = ttk.Button(
    frame_download, text="Seleccionar carpeta destino", command=select_folder
)
folder_button.pack(side="left")

folder_label = ttk.Label(frame_download, text="Carpeta destino: No seleccionada")
folder_label.pack(side="left", padx=10)

download_button = ttk.Button(frame_download, text="Descargar", command=download_video)
download_button.pack(side="right")

progress_label = ttk.Label(frame_download, text="Esperando acción...")
progress_label.pack(side="left", padx=10)

progress_bar = ttk.Progressbar(frame_download, length=200)
progress_bar.pack(side="right", padx=10)


def center_window(win):
    win.update_idletasks()  # Actualiza info de tamaño
    width = win.winfo_width()
    height = win.winfo_height()
    screen_width = win.winfo_screenwidth()
    screen_height = win.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    win.geometry(f"{width}x{height}+{x}+{y}")


# Luego, antes de mainloop, llama a:
center_window(root)

root.mainloop()
