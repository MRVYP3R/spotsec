import customtkinter as ctk
import subprocess
import threading
import shutil
import sys
import os
from tkinter import filedialog
from datetime import datetime

# Opcional: credenciales propias de Spotify (recomendado para evitar rate limits)
# Créalas gratis en https://developer.spotify.com/dashboard
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""

# Configuración del entorno visual (Estilo Terminal)
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class SpotSonda(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spot-Sec // Cazador de Playlists")
        self.geometry("850x700")

        # Ruta de volcado por defecto
        self.dump_dir = os.path.abspath("./spotify_volcado")
        os.makedirs(self.dump_dir, exist_ok=True)

        self.construir_interfaz()

    def construir_interfaz(self):
        # Título
        self.lbl_titulo = ctk.CTkLabel(
            self, text="TERMINAL DE CACERÍA MUSICAL (SPOTIFY / TEXTO)",
            font=("Consolas", 18, "bold"), text_color="#00FF00"
        )
        self.lbl_titulo.pack(pady=10)

        # --- Panel Superior: Selector de Carpeta ---
        self.frame_folder = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_folder.pack(pady=5, fill="x", padx=20)

        self.lbl_folder = ctk.CTkLabel(self.frame_folder, text="Ruta Destino:", font=("Consolas", 12))
        self.lbl_folder.pack(side="left", padx=5)

        self.entry_carpeta = ctk.CTkEntry(self.frame_folder, font=("Consolas", 12))
        self.entry_carpeta.insert(0, self.dump_dir)
        self.entry_carpeta.configure(state="disabled")
        self.entry_carpeta.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_examinar = ctk.CTkButton(
            self.frame_folder, text="Examinar...",
            command=self.seleccionar_carpeta, font=("Consolas", 12),
            fg_color="#1f538d", hover_color="#14375e"
        )
        self.btn_examinar.pack(side="left", padx=10)

        # --- Panel Central: Entrada de Datos (Lista) ---
        self.lbl_instrucciones = ctk.CTkLabel(
            self,
            text="Pega URLs de Spotify (Playlists/Álbumes/Canciones) o escribe títulos manualmente (Uno por línea):",
            font=("Consolas", 11)
        )
        self.lbl_instrucciones.pack(pady=(10, 0), padx=20, anchor="w")

        self.caja_entrada = ctk.CTkTextbox(
            self, width=810, height=150, font=("Consolas", 12),
            fg_color="#1A1A1A", text_color="#FFFFFF"
        )
        self.caja_entrada.pack(pady=5, padx=20)

        # --- Botón de Ejecución ---
        self.btn_cazar = ctk.CTkButton(
            self, text="INICIAR CACERÍA Y EXTRACCIÓN",
            command=self.iniciar_caceria, font=("Consolas", 14, "bold"),
            fg_color="#8B0000", hover_color="#A52A2A", height=40
        )
        self.btn_cazar.pack(pady=10)

        # --- Panel Inferior: Consola de Salida ---
        self.consola = ctk.CTkTextbox(
            self, width=810, height=280, font=("Consolas", 12),
            fg_color="#0A0A0A", text_color="#00FF00"
        )
        self.consola.pack(pady=5, padx=20)
        self.consola.insert("0.0", "[*] Módulo Spot-Sec cargado. Esperando objetivos...\n")

    # ------------------------------------------------------------------
    # Utilidades de interfaz (seguras para llamar desde hilos)
    # ------------------------------------------------------------------
    def log_consola(self, texto):
        # self.after programa la escritura en el hilo principal de la GUI
        self.after(0, self._log_ui, texto)

    def _log_ui(self, texto):
        hora = datetime.now().strftime("%H:%M:%S")
        self.consola.insert("end", f"[{hora}] {texto}\n")
        self.consola.see("end")

    def _reactivar(self, fallidos):
        self.btn_cazar.configure(state="normal")
        self.caja_entrada.configure(state="normal")
        self.caja_entrada.delete("0.0", "end")
        if fallidos:
            # Dejamos en la caja solo los objetivos que fallaron para reintentar
            self.caja_entrada.insert("0.0", "\n".join(fallidos))

    def seleccionar_carpeta(self):
        carpeta_seleccionada = filedialog.askdirectory(initialdir=self.dump_dir, title="Seleccionar Destino")
        if carpeta_seleccionada:
            self.dump_dir = os.path.abspath(carpeta_seleccionada)
            self.entry_carpeta.configure(state="normal")
            self.entry_carpeta.delete(0, "end")
            self.entry_carpeta.insert(0, self.dump_dir)
            self.entry_carpeta.configure(state="disabled")
            self.log_consola(f"[+] Directorio de volcado reconfigurado -> {self.dump_dir}")

    # ------------------------------------------------------------------
    # Lógica principal
    # ------------------------------------------------------------------
    def iniciar_caceria(self):
        texto_bruto = self.caja_entrada.get("0.0", "end").strip()
        if not texto_bruto:
            self.log_consola("[-] Error: El panel de inyección está vacío.")
            return

        if shutil.which("spotdl") is None:
            self.log_consola("[-] No se encontró 'spotdl' en el PATH.")
            self.log_consola("    Instálalo con: pip install -U spotdl")
            self.log_consola("    Y luego:       spotdl --download-ffmpeg")
            return

        lineas = [linea.strip() for linea in texto_bruto.split("\n") if linea.strip()]

        self.btn_cazar.configure(state="disabled")
        self.caja_entrada.configure(state="disabled")

        # daemon=True para que la ventana pueda cerrarse aunque haya una descarga activa
        hilo_caceria = threading.Thread(target=self.proceso_extraccion, args=(lineas,), daemon=True)
        hilo_caceria.start()

    def proceso_extraccion(self, lineas):
        self.log_consola(f"[!] Se detectaron {len(lineas)} objetivo(s) en la lista.")
        self.log_consola("[*] Inicializando motor puente SpotDL/YT-DLP...")
        self.log_consola("-" * 50)

        fallidos = []

        # {list-name} crea una subcarpeta por playlist/álbum.
        # OJO: la extensión en spotdl es {output-ext}, no {ext}.
        plantilla_salida = os.path.join(self.dump_dir, "{list-name}", "{artists} - {title}.{output-ext}")

        # Evita que se abra una ventana de consola por cada proceso en Windows
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        for i, objetivo in enumerate(lineas, 1):
            self.log_consola(f"\n[*] Analizando Objetivo [{i}/{len(lineas)}]: {objetivo}")

            comando = [
                "spotdl",
                "download",
                objetivo,
                "--format", "m4a",
                "--threads", "4",
                "--output", plantilla_salida,
            ]
            if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
                comando += ["--client-id", SPOTIFY_CLIENT_ID, "--client-secret", SPOTIFY_CLIENT_SECRET]

            try:
                proceso = subprocess.Popen(
                    comando,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",        # evita UnicodeDecodeError en Windows
                    errors="replace",
                    bufsize=1,
                    creationflags=flags,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                )

                for salida in proceso.stdout:
                    linea_limpia = salida.strip()
                    if not linea_limpia:
                        continue
                    # Filtramos barras de progreso para mantener la consola limpia
                    if "ETA" in linea_limpia or "%" in linea_limpia:
                        continue
                    self.log_consola(f"    -> {linea_limpia}")

                proceso.stdout.close()
                proceso.wait()

                if proceso.returncode != 0:
                    self.log_consola(f"[X] Falla al procesar el objetivo {i}.")
                    fallidos.append(objetivo)
                else:
                    self.log_consola(f"[+] Objetivo {i} procesado exitosamente.")

            except Exception as e:
                self.log_consola(f"[-] Falla crítica en subproceso: {e}")
                fallidos.append(objetivo)

        self.log_consola("-" * 50)
        if fallidos:
            self.log_consola(f"[!] Completado con {len(fallidos)} fallo(s). Se dejaron en la lista para reintentar.")
        else:
            self.log_consola("[!] Completado sin errores.")
        self.log_consola(f"[*] Archivos en: {self.dump_dir}")

        # Reactivamos controles desde el hilo principal
        self.after(0, self._reactivar, fallidos)


if __name__ == "__main__":
    app = SpotSonda()
    app.mainloop()
