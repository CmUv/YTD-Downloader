import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

# Configuración de Proxy (Reemplaza con tu proxy si es necesario)
DEFAULT_PROXY = "http://192.168.49.1:8000"

class YTDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader con Proxy")
        self.root.geometry("500x300")

        # URL del video
        ttk.Label(root, text="URL del video:").pack(pady=5)
        self.url_entry = ttk.Entry(root, width=50)
        self.url_entry.pack(pady=5)

        # Botón para obtener calidades
        self.get_quality_btn = ttk.Button(root, text="Obtener calidades", command=self.get_qualities)
        self.get_quality_btn.pack(pady=5)

        # Lista de calidades
        self.quality_combobox = ttk.Combobox(root, state="readonly")
        self.quality_combobox.pack(pady=5)

        # Botón para descargar
        self.download_btn = ttk.Button(root, text="Descargar", command=self.download_video)
        self.download_btn.pack(pady=10)

        # Barra de progreso
        self.progress = ttk.Progressbar(root, length=300, mode="determinate")
        self.progress.pack(pady=10)

    def get_qualities(self):
        """ Obtiene las calidades disponibles del video """
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Advertencia", "Ingrese una URL válida")
            return

        try:
            result = subprocess.run(
                ["yt-dlp", "--proxy", DEFAULT_PROXY, "-F", url],
                capture_output=True,
                text=True
            )
            output = result.stdout
            formats = []
            for line in output.split("\n"):
                if line.strip() and line[0].isdigit():
                    formats.append(line.split()[0])  # Extrae solo el ID del formato
            self.quality_combobox["values"] = formats
            if formats:
                self.quality_combobox.current(0)
                messagebox.showinfo("Éxito", "Calidades obtenidas correctamente.")
            else:
                messagebox.showwarning("Error", "No se encontraron formatos disponibles.")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema: {str(e)}")

    def download_video(self):
        """ Descarga el video con la calidad seleccionada """
        url = self.url_entry.get().strip()
        quality = self.quality_combobox.get()

        if not url or not quality:
            messagebox.showwarning("Advertencia", "Seleccione una calidad de descarga")
            return

        self.progress["value"] = 10
        self.root.update_idletasks()

        try:
            subprocess.run(
                ["yt-dlp", "--proxy", DEFAULT_PROXY, "-f", quality, url, "-o", "%(title)s.%(ext)s"],
                text=True
            )
            self.progress["value"] = 100
            messagebox.showinfo("Éxito", "Descarga completada correctamente.")

        except Exception as e:
            messagebox.showerror("Error", f"Error al descargar: {str(e)}")
            self.progress["value"] = 0

if __name__ == "__main__":
    root = tk.Tk()
    app = YTDownloaderApp(root)
    root.mainloop()
