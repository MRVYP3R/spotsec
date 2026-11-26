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

# ----------------------------------------------------------------------
# Tema
# ----------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

FUENTE = "Consolas"
BG = "#0D1117"
PANEL = "#161B22"
CAMPO = "#0A0E14"
BORDE = "#30363D"
TEXTO = "#E6EDF3"
TENUE = "#8B949E"
VERDE = "#3FB950"
VERDE_OSC = "#238636"
ROJO = "#F85149"
ROJO_OSC = "#8B1A1A"
AMBAR = "#D29922"
AZUL = "#58A6FF"

FORMATOS = ["m4a", "mp3", "flac", "opus", "ogg", "wav"]


class SpotSonda(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Spot-Sec // Cazador de Playlists")
        self.geometry("900x780")
        self.minsize(780, 660)
        self.configure(fg_color=BG)

        # Ruta de volcado por defecto
        self.dump_dir = os.path.abspath("./spotify_volcado")
        os.makedirs(self.dump_dir, exist_ok=True)

        # Estado de ejecución
        self.proceso = None
        self.cancelado = False
        self.trabajando = False
        self.total = 0
        self.stats = {"actual": 0, "canciones": 0, "fallos": 0}

        self.var_carpeta = ctk.StringVar(value=self.dump_dir)
        self.var_formato = ctk.StringVar(value="m4a")
        self.var_hilos = ctk.StringVar(value="4")

        self.construir_interfaz()
        self._actualizar_contador()
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    # ------------------------------------------------------------------
    # Construcción de la interfaz
    # ------------------------------------------------------------------
    def _tarjeta(self, padre, **grid):
        marco = ctk.CTkFrame(
            padre, fg_color=PANEL, border_width=1, border_color=BORDE, corner_radius=8
        )
        marco.grid(sticky="ew", padx=20, pady=(0, 10), **grid)
        return marco

    def construir_interfaz(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)  # la consola absorbe el espacio sobrante

        self._crear_encabezado()
        self._crear_destino()
        self._crear_entrada()
        self._crear_acciones()
        self._crear_consola()

        self.log_consola("[*] Módulo Spot-Sec cargado. Esperando objetivos...")

    def _crear_encabezado(self):
        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 12))
        cab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cab, text="Spot-Sec", font=(FUENTE, 24, "bold"), text_color=VERDE, anchor="w"
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            cab,
            text="Descarga playlists, álbumes y canciones de Spotify",
            font=(FUENTE, 12), text_color=TENUE, anchor="w",
        ).grid(row=1, column=0, sticky="w")

        self.lbl_estado = ctk.CTkLabel(
            cab, text="  Listo  ", font=(FUENTE, 12, "bold"),
            fg_color=VERDE_OSC, text_color="#FFFFFF", corner_radius=10,
        )
        self.lbl_estado.grid(row=0, column=1, rowspan=2, sticky="e")

    def _crear_destino(self):
        tarjeta = self._tarjeta(self, row=1, column=0)
        tarjeta.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(tarjeta, text="Carpeta de destino", font=(FUENTE, 12), text_color=TENUE).grid(
            row=0, column=0, padx=(14, 8), pady=12
        )
        self.entry_carpeta = ctk.CTkEntry(
            tarjeta, textvariable=self.var_carpeta, font=(FUENTE, 12),
            fg_color=CAMPO, border_color=BORDE, state="readonly",
        )
        self.entry_carpeta.grid(row=0, column=1, sticky="ew", pady=12)

        self.btn_examinar = ctk.CTkButton(
            tarjeta, text="Cambiar", width=90, font=(FUENTE, 12),
            fg_color="#1F538D", hover_color="#14375E", command=self.seleccionar_carpeta,
        )
        self.btn_examinar.grid(row=0, column=2, padx=(8, 4), pady=12)

        self.btn_abrir = ctk.CTkButton(
            tarjeta, text="Abrir carpeta", width=110, font=(FUENTE, 12),
            fg_color="transparent", border_width=1, border_color=BORDE,
            hover_color="#21262D", text_color=TEXTO, command=self.abrir_carpeta,
        )
        self.btn_abrir.grid(row=0, column=3, padx=(4, 14), pady=12)

    def _crear_entrada(self):
        tarjeta = self._tarjeta(self, row=2, column=0)
        tarjeta.grid_columnconfigure(0, weight=1)

        # Fila de título + herramientas de la lista
        fila = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 4))
        fila.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            fila,
            text="Enlaces de Spotify o títulos de canciones (uno por línea)",
            font=(FUENTE, 12), text_color=TEXTO, anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.btn_pegar = ctk.CTkButton(
            fila, text="Pegar", width=70, height=26, font=(FUENTE, 11),
            fg_color="transparent", border_width=1, border_color=BORDE,
            hover_color="#21262D", text_color=TEXTO, command=self.pegar_portapapeles,
        )
        self.btn_pegar.grid(row=0, column=1, padx=(8, 4))

        self.btn_limpiar_lista = ctk.CTkButton(
            fila, text="Vaciar", width=70, height=26, font=(FUENTE, 11),
            fg_color="transparent", border_width=1, border_color=BORDE,
            hover_color="#21262D", text_color=TEXTO, command=self.vaciar_lista,
        )
        self.btn_limpiar_lista.grid(row=0, column=2)

        self.caja_entrada = ctk.CTkTextbox(
            tarjeta, height=130, font=(FUENTE, 12), fg_color=CAMPO,
            text_color=TEXTO, border_width=1, border_color=BORDE, wrap="none",
        )
        self.caja_entrada.grid(row=1, column=0, sticky="ew", padx=14, pady=4)
        self.caja_entrada.bind("<KeyRelease>", self._actualizar_contador)
        self.caja_entrada.bind("<Control-Return>", self._atajo_iniciar)

        # Pie de la tarjeta: contador + opciones de descarga
        pie = ctk.CTkFrame(tarjeta, fg_color="transparent")
        pie.grid(row=2, column=0, sticky="ew", padx=14, pady=(4, 12))
        pie.grid_columnconfigure(0, weight=1)

        self.lbl_contador = ctk.CTkLabel(
            pie, text="", font=(FUENTE, 11), text_color=TENUE, anchor="w"
        )
        self.lbl_contador.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(pie, text="Formato", font=(FUENTE, 11), text_color=TENUE).grid(
            row=0, column=1, padx=(8, 4)
        )
        self.menu_formato = ctk.CTkOptionMenu(
            pie, values=FORMATOS, variable=self.var_formato, width=84, height=26,
            font=(FUENTE, 11), dropdown_font=(FUENTE, 11),
            fg_color="#21262D", button_color="#30363D", button_hover_color="#3B434C",
        )
        self.menu_formato.grid(row=0, column=2)

        ctk.CTkLabel(pie, text="Hilos", font=(FUENTE, 11), text_color=TENUE).grid(
            row=0, column=3, padx=(14, 4)
        )
        self.seg_hilos = ctk.CTkSegmentedButton(
            pie, values=["1", "2", "4", "8"], variable=self.var_hilos,
            font=(FUENTE, 11), height=26,
        )
        self.seg_hilos.grid(row=0, column=4)

    def _crear_acciones(self):
        # Botones principales
        barra_botones = ctk.CTkFrame(self, fg_color="transparent")
        barra_botones.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
        barra_botones.grid_columnconfigure(0, weight=1)

        self.btn_cazar = ctk.CTkButton(
            barra_botones, text="Iniciar descarga  (Ctrl+Enter)",
            font=(FUENTE, 14, "bold"), height=42,
            fg_color=VERDE_OSC, hover_color="#2EA043", command=self.iniciar_caceria,
        )
        self.btn_cazar.grid(row=0, column=0, sticky="ew")

        self.btn_cancelar = ctk.CTkButton(
            barra_botones, text="Cancelar", width=120, height=42,
            font=(FUENTE, 13, "bold"), fg_color=ROJO_OSC, hover_color="#A52A2A",
            state="disabled", command=self.cancelar_caceria,
        )
        self.btn_cancelar.grid(row=0, column=1, padx=(10, 0))

        # Progreso
        progreso = ctk.CTkFrame(self, fg_color="transparent")
        progreso.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 10))
        progreso.grid_columnconfigure(0, weight=1)

        self.barra = ctk.CTkProgressBar(
            progreso, height=10, progress_color=VERDE, fg_color="#21262D"
        )
        self.barra.set(0)
        self.barra.grid(row=0, column=0, sticky="ew")

        self.lbl_stats = ctk.CTkLabel(
            progreso, text="", font=(FUENTE, 11), text_color=TENUE, anchor="e"
        )
        self.lbl_stats.grid(row=0, column=1, padx=(12, 0))
        self._refrescar_stats()

    def _crear_consola(self):
        marco = ctk.CTkFrame(
            self, fg_color=PANEL, border_width=1, border_color=BORDE, corner_radius=8
        )
        marco.grid(row=5, column=0, sticky="nsew", padx=20, pady=(0, 16))
        marco.grid_columnconfigure(0, weight=1)
        marco.grid_rowconfigure(1, weight=1)

        cab = ctk.CTkFrame(marco, fg_color="transparent")
        cab.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        cab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(cab, text="Registro", font=(FUENTE, 12), text_color=TEXTO, anchor="w").grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkButton(
            cab, text="Guardar", width=70, height=26, font=(FUENTE, 11),
            fg_color="transparent", border_width=1, border_color=BORDE,
            hover_color="#21262D", text_color=TEXTO, command=self.guardar_registro,
        ).grid(row=0, column=1, padx=(8, 4))
        ctk.CTkButton(
            cab, text="Limpiar", width=70, height=26, font=(FUENTE, 11),
            fg_color="transparent", border_width=1, border_color=BORDE,
            hover_color="#21262D", text_color=TEXTO, command=self.limpiar_consola,
        ).grid(row=0, column=2)

        self.consola = ctk.CTkTextbox(
            marco, font=(FUENTE, 12), fg_color=CAMPO, text_color=TEXTO,
            border_width=1, border_color=BORDE, wrap="word", state="disabled",
        )
        self.consola.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        # Colores por tipo de mensaje
        self.consola.tag_config("hora", foreground="#565F6B")
        self.consola.tag_config("ok", foreground=VERDE)
        self.consola.tag_config("err", foreground=ROJO)
        self.consola.tag_config("warn", foreground=AMBAR)
        self.consola.tag_config("info", foreground=AZUL)
        self.consola.tag_config("dim", foreground=TENUE)
        self.consola.tag_config("normal", foreground=TEXTO)

    # ------------------------------------------------------------------
    # Utilidades de interfaz (seguras para llamar desde hilos)
    # ------------------------------------------------------------------
    @staticmethod
    def _nivel(texto):
        t = texto.lstrip()
        if t.startswith("[+]"):
            return "ok"
        if t.startswith("[-]") or t.startswith("[X]"):
            return "err"
        if t.startswith("[!]"):
            return "warn"
        if t.startswith("[*]"):
            return "info"
        if t.startswith("->") or set(t) <= {"-"}:
            return "dim"
        return "normal"

    def log_consola(self, texto):
        # self.after programa la escritura en el hilo principal de la GUI
        self.after(0, self._log_ui, texto)

    def _log_ui(self, texto):
        hora = datetime.now().strftime("%H:%M:%S")
        self.consola.configure(state="normal")
        self.consola.insert("end", f"{hora}  ", "hora")
        self.consola.insert("end", f"{texto}\n", self._nivel(texto))
        self.consola.see("end")
        self.consola.configure(state="disabled")

    def limpiar_consola(self):
        self.consola.configure(state="normal")
        self.consola.delete("0.0", "end")
        self.consola.configure(state="disabled")

    def guardar_registro(self):
        ruta = filedialog.asksaveasfilename(
            title="Guardar registro",
            defaultextension=".txt",
            initialfile=f"spotsec_{datetime.now():%Y%m%d_%H%M%S}.txt",
            filetypes=[("Texto", "*.txt")],
        )
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(self.consola.get("0.0", "end"))
            self.log_consola(f"[+] Registro guardado en {ruta}")

    def _estado(self, texto, color):
        self.lbl_estado.configure(text=f"  {texto}  ", fg_color=color)

    def _refrescar_stats(self):
        s = self.stats
        self.lbl_stats.configure(
            text=f"Objetivo {s['actual']}/{self.total}   Canciones {s['canciones']}   Fallos {s['fallos']}"
        )

    def _actualizar_contador(self, _evento=None):
        lineas = self._leer_lineas()
        enlaces = sum(1 for l in lineas if l.lower().startswith("http"))
        if not lineas:
            texto = "Lista vacía"
        else:
            titulos = len(lineas) - enlaces
            texto = f"{len(lineas)} objetivo(s): {enlaces} enlace(s), {titulos} título(s)"
        self.lbl_contador.configure(text=texto)

    def _leer_lineas(self):
        bruto = self.caja_entrada.get("0.0", "end")
        return [l.strip() for l in bruto.split("\n") if l.strip()]

    def pegar_portapapeles(self):
        try:
            texto = self.clipboard_get()
        except Exception:
            self.log_consola("[-] El portapapeles está vacío o no contiene texto.")
            return
        actual = self.caja_entrada.get("0.0", "end").strip()
        if actual:
            self.caja_entrada.insert("end", "\n")
        self.caja_entrada.insert("end", texto.strip())
        self._actualizar_contador()

    def vaciar_lista(self):
        self.caja_entrada.delete("0.0", "end")
        self._actualizar_contador()

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory(initialdir=self.dump_dir, title="Seleccionar destino")
        if carpeta:
            self.dump_dir = os.path.abspath(carpeta)
            self.var_carpeta.set(self.dump_dir)
            self.log_consola(f"[+] Directorio de volcado reconfigurado -> {self.dump_dir}")

    def abrir_carpeta(self):
        os.makedirs(self.dump_dir, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(self.dump_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.dump_dir])
            else:
                subprocess.Popen(["xdg-open", self.dump_dir])
        except Exception as e:
            self.log_consola(f"[-] No se pudo abrir la carpeta: {e}")

    def _bloquear_controles(self, bloquear):
        estado = "disabled" if bloquear else "normal"
        for w in (
            self.caja_entrada, self.btn_examinar, self.btn_pegar,
            self.btn_limpiar_lista, self.menu_formato, self.seg_hilos,
        ):
            w.configure(state=estado)
        self.btn_cazar.configure(state=estado)
        self.btn_cancelar.configure(state="normal" if bloquear else "disabled")

    def _atajo_iniciar(self, _evento=None):
        self.iniciar_caceria()
        return "break"  # evita que Ctrl+Enter agregue una línea nueva

    # ------------------------------------------------------------------
    # Lógica principal
    # ------------------------------------------------------------------
    def iniciar_caceria(self):
        if self.trabajando:
            return

        lineas = self._leer_lineas()
        if not lineas:
            self.log_consola("[-] Error: la lista está vacía. Pega un enlace o escribe un título.")
            return

        if shutil.which("spotdl") is None:
            self.log_consola("[-] No se encontró 'spotdl' en el PATH.")
            self.log_consola("    Instálalo con: pip install -U spotdl")
            self.log_consola("    Y luego:       spotdl --download-ffmpeg")
            return

        self.trabajando = True
        self.cancelado = False
        self.total = len(lineas)
        self.stats = {"actual": 0, "canciones": 0, "fallos": 0}
        self._refrescar_stats()

        # Un solo objetivo: no hay progreso medible, así que animamos la barra
        if self.total == 1:
            self.barra.configure(mode="indeterminate")
            self.barra.start()
        else:
            self.barra.configure(mode="determinate")
            self.barra.set(0)

        self._bloquear_controles(True)
        self._estado("Descargando", AMBAR)

        formato = self.var_formato.get()
        hilos = self.var_hilos.get()

        # daemon=True para que la ventana pueda cerrarse aunque haya una descarga activa
        hilo = threading.Thread(
            target=self.proceso_extraccion, args=(lineas, formato, hilos), daemon=True
        )
        hilo.start()

    def cancelar_caceria(self):
        if not self.trabajando:
            return
        self.cancelado = True
        self.log_consola("[!] Cancelando... se detendrá la descarga en curso.")
        self.btn_cancelar.configure(state="disabled")
        proc = self.proceso
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass

    def proceso_extraccion(self, lineas, formato, hilos):
        n = len(lineas)
        self.log_consola(f"[!] Se detectaron {n} objetivo(s) en la lista.")
        self.log_consola(f"[*] Motor SpotDL/YT-DLP | formato: {formato} | hilos: {hilos}")
        self.log_consola("-" * 50)

        fallidos = []

        # {list-name} crea una subcarpeta por playlist/álbum.
        # OJO: la extensión en spotdl es {output-ext}, no {ext}.
        plantilla_salida = os.path.join(self.dump_dir, "{list-name}", "{artists} - {title}.{output-ext}")

        # Evita que se abra una ventana de consola por cada proceso en Windows
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

        for i, objetivo in enumerate(lineas, 1):
            if self.cancelado:
                # Lo que no se alcanzó a procesar queda en la lista
                fallidos.extend(lineas[i - 1:])
                break

            self.stats["actual"] = i
            self.after(0, self._refrescar_stats)
            if n > 1:
                self.after(0, self.barra.set, (i - 1) / n)

            self.log_consola(f"[*] Objetivo [{i}/{n}]: {objetivo}")

            comando = [
                "spotdl", "download", objetivo,
                "--format", formato,
                "--threads", hilos,
                "--output", plantilla_salida,
            ]
            if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
                comando += ["--client-id", SPOTIFY_CLIENT_ID, "--client-secret", SPOTIFY_CLIENT_SECRET]

            try:
                self.proceso = subprocess.Popen(
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

                for salida in self.proceso.stdout:
                    linea_limpia = salida.strip()
                    if not linea_limpia:
                        continue
                    # Filtramos barras de progreso para mantener la consola limpia
                    if "ETA" in linea_limpia or "%" in linea_limpia:
                        continue
                    if linea_limpia.startswith("Downloaded"):
                        self.stats["canciones"] += 1
                        self.after(0, self._refrescar_stats)
                    self.log_consola(f"    -> {linea_limpia}")

                self.proceso.stdout.close()
                self.proceso.wait()

                if self.cancelado:
                    fallidos.append(objetivo)
                    fallidos.extend(lineas[i:])
                    break

                if self.proceso.returncode != 0:
                    self.log_consola(f"[X] Falla al procesar el objetivo {i}.")
                    fallidos.append(objetivo)
                    self.stats["fallos"] += 1
                else:
                    self.log_consola(f"[+] Objetivo {i} procesado exitosamente.")

            except Exception as e:
                self.log_consola(f"[-] Falla crítica en subproceso: {e}")
                fallidos.append(objetivo)
                self.stats["fallos"] += 1
            finally:
                self.proceso = None
                self.after(0, self._refrescar_stats)

        self.log_consola("-" * 50)
        if self.cancelado:
            self.log_consola(f"[!] Cancelado. {len(fallidos)} objetivo(s) quedaron en la lista.")
        elif fallidos:
            self.log_consola(f"[!] Completado con {len(fallidos)} fallo(s). Se dejaron en la lista para reintentar.")
        else:
            self.log_consola("[+] Completado sin errores.")
        self.log_consola(f"[*] Archivos en: {self.dump_dir}")

        # Reactivamos controles desde el hilo principal
        self.after(0, self._finalizar, fallidos)

    def _finalizar(self, fallidos):
        self.barra.stop()
        self.barra.configure(mode="determinate")
        hechos = self.total - len(fallidos)
        self.barra.set(hechos / self.total if self.total else 0)

        if self.cancelado:
            self._estado("Cancelado", ROJO_OSC)
        elif fallidos:
            self._estado("Con fallos", ROJO_OSC)
        else:
            self._estado("Completado", VERDE_OSC)

        self.trabajando = False
        self._bloquear_controles(False)

        # Dejamos en la caja solo los objetivos pendientes o fallidos para reintentar
        self.caja_entrada.delete("0.0", "end")
        if fallidos:
            self.caja_entrada.insert("0.0", "\n".join(fallidos))
        self._actualizar_contador()

    def _cerrar(self):
        self.cancelado = True
        proc = self.proceso
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    app = SpotSonda()
    app.mainloop()