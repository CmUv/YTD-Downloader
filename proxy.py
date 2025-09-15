import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading

# Clase para la interfaz de usuario
class YTDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("900x600")

        self.download_path = None
        self.process = None
        self.cancel_download_flag = False
        self.format_dict = {}

        # Etiqueta para la URL
        ttk.Label(root, text="URL del video:").pack(pady=5)
        self.url_entry = ttk.Entry(root, width=50)
        self.url_entry.pack(pady=5)

        # Botón para obtener calidades
        self.get_quality_btn = ttk.Button(root, text="Obtener calidades", command=self.start_get_qualities_thread)
        self.get_quality_btn.pack(pady=5)

        # Indicador de carga
        self.loading_label = ttk.Label(root, text="Obteniendo calidades...", state="disabled")
        self.loading_label.pack(pady=5)

        # Combobox para elegir calidades
        self.quality_combobox = ttk.Combobox(root, state="readonly", width=80)
        self.quality_combobox.pack(pady=5)

        # Botón para descargar
        self.download_btn = ttk.Button(root, text="Descargar", command=self.start_download_thread, state="disabled")
        self.download_btn.pack(pady=10)

        # Botón de cancelar
        self.cancel_btn = ttk.Button(root, text="Cancelar", command=self.cancel_download, state="disabled")
        self.cancel_btn.pack(pady=5)

        # Barra de progreso
        self.progress = ttk.Progressbar(root, length=300, mode="determinate")
        self.progress.pack(pady=10)

        # Etiqueta de progreso
        self.progress_label = ttk.Label(root, text="Progreso: 0%")
        self.progress_label.pack(pady=5)

    def start_get_qualities_thread(self):
        """ Inicia el hilo para obtener las calidades sin bloquear la interfaz """
        threading.Thread(target=self.get_qualities).start()

    def get_qualities(self):
        """ Obtiene las calidades del video y las muestra en un formato amigable """
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showwarning("Advertencia", "Por favor ingrese una URL válida")
            return

        # Mostrar el indicador de carga
        self.loading_label.config(state="normal")
        self.get_quality_btn.config(state="disabled")
        self.root.update_idletasks()

        try:
            result = subprocess.run(
                ["yt-dlp", "-F", url],
                capture_output=True,
                text=True
            )
            output = result.stdout
            formats = []
            self.format_dict.clear()

            # Buscar los formatos disponibles en la salida de yt-dlp
            for line in output.split("\n"):
                if line.startswith("format code"):
                    continue  # Saltamos la línea de encabezado
                if len(line.split()) > 0 and line.split()[0].isdigit():
                    parts = line.split()
                    format_id = parts[0]
                    resolution = parts[2] if "x" in parts[2] else "Desconocido"
                    ext = parts[1]
                    filesize = parts[4] if len(parts) > 4 else "N/A"
                    codec = parts[7] if len(parts) > 7 else "N/A"
                    description = f"{format_id:<6} {resolution:<12} {ext:<6} {filesize:<12} {codec:<15}"
                    formats.append(description)
                    self.format_dict[description] = format_id

            if formats:
                self.quality_combobox["values"] = formats
                self.quality_combobox.current(0)
                self.download_btn.config(state="normal")
                messagebox.showinfo("Éxito", "Calidades obtenidas correctamente.")
            else:
                messagebox.showwarning("Error", "No se encontraron formatos para este video.")
        
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error: {str(e)}")

        # Ocultar el indicador de carga
        self.loading_label.config(state="disabled")
        self.get_quality_btn.config(state="normal")
        self.root.update_idletasks()

    def start_download_thread(self):
        """ Inicia el hilo para la descarga sin bloquear la interfaz """
        self.download_path = filedialog.askdirectory(title="Seleccionar carpeta de descarga")
        if not self.download_path:
            messagebox.showwarning("Advertencia", "Debe seleccionar una carpeta para la descarga.")
            return

        self.cancel_download_flag = False
        self.cancel_btn.config(state="normal")
        threading.Thread(target=self.download_video).start()

    def download_video(self):
        """ Realiza la descarga del video con la calidad seleccionada """
        url = self.url_entry.get().strip()
        selected_quality = self.quality_combobox.get()
        format_id = self.format_dict.get(selected_quality, "")

        if not url or not format_id:
            messagebox.showwarning("Advertencia", "Seleccione un formato de descarga válido.")
            return

        try:
            self.process = subprocess.Popen(
                ["yt-dlp", "-f", format_id, url, "-o", f"{self.download_path}/%(title)s.%(ext)s"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Leer la salida del proceso y actualizar la barra de progreso
            for line in self.process.stdout:
                if self.cancel_download_flag:
                    self.process.kill()
                    messagebox.showinfo("Cancelado", "La descarga ha sido cancelada.")
                    break
                if "%" in line:
                    self.update_progress(line)

            self.process.wait()
            if not self.cancel_download_flag:
                messagebox.showinfo("Completado", "Descarga finalizada correctamente.")
            else:
                self.progress["value"] = 0
                self.progress_label.config(text="Progreso: 0%")

        except Exception as e:
            messagebox.showerror("Error", f"Hubo un error al intentar descargar el video: {str(e)}")

        self.cancel_btn.config(state="disabled")

    def update_progress(self, line):
        """ Actualiza la barra de progreso y el texto del progreso """
        try:
            # Extraemos el porcentaje de progreso
            if "%" in line:
                progress = int(re.search(r'(\d+)%', line).group(1))
                self.progress["value"] = progress
                self.progress_label.config(text=f"Progreso: {progress}%")

            # Extraemos el ETA
            if "ETA" in line:
                eta = line.split("ETA")[-1].strip()
                self.progress_label.config(text=f"Progreso: {self.progress['value']}% | ETA: {eta}")

            self.root.update_idletasks()

        except Exception as e:
            print(f"Error al actualizar progreso: {e}")

    def cancel_download(self):
        """ Cancela la descarga """
        self.cancel_download_flag = True
        if self.process:
            self.process.kill()

if __name__ == "__main__":
    root = tk.Tk()
    app = YTDownloaderApp(root)
    root.mainloop()
