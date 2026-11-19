# Spot-Sec 🎧
<div align="center">
<img src="logo.png" alt="SPOTSEC Logo" width="420"/>
**Interfaz gráfica estilo terminal para descargar playlists, álbumes y canciones usando [spotDL](https://github.com/spotDL/spotify-downloader).**

Pega enlaces de Spotify o escribe títulos, elige formato y calidad, y Spot-Sec se encarga del resto: valida la lista, descarga por lotes, reintenta lo que falle y te deja un registro de todo.

> Hecho con Python + [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter).

---
</div>
## Características

- **Validación inteligente de la lista**: reconoce playlists, álbumes, canciones, artistas, enlaces de YouTube y búsquedas por texto. Limpia los `?si=...`, elimina duplicados e ignora las líneas que empiezan con `#`.
- **Opciones en pantalla**: formato (`m4a`, `mp3`, `flac`, `opus`, `ogg`, `wav`), bitrate, hilos, reintentos y qué hacer con los archivos que ya existen.
- **Progreso real**: barra global, contadores por pistas (✔ descargadas · ↷ omitidas · ✖ fallidas) y tiempo transcurrido.
- **Cancelación limpia**: detiene spotDL y todos sus procesos hijos.
- **Reintentos automáticos** con espera creciente; los objetivos fallidos o pendientes vuelven a la caja de texto para reintentar.
- **Subcarpeta por playlist/álbum** (opcional).
- **Cargar listas desde `.txt`**, abrir la carpeta de destino y guardar el registro.
- **Mantenimiento integrado**: botones para actualizar spotDL y descargar ffmpeg.
- **Configuración persistente** entre sesiones.
- **Seguro**: los comandos se ejecutan como lista de argumentos, sin `shell=True`.

## Requisitos

- Python 3.9 o superior
- Tkinter (en Linux: `python3-tk`)
- [spotDL](https://github.com/spotDL/spotify-downloader) y [ffmpeg](https://ffmpeg.org/)

## Instalación

### Linux (Debian / Ubuntu / Kali)

Estas distribuciones protegen el Python del sistema (PEP 668), así que usa un entorno virtual:

```bash
git clone https://github.com/MRVYP3R/spot-sec.git
cd spot-sec

sudo apt install python3-full python3-tk
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
spotdl --download-ffmpeg        # o: sudo apt install ffmpeg
```

### Windows

```powershell
git clone https://github.com/MRVYP3R/spot-sec.git
cd spot-sec

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
spotdl --download-ffmpeg
```

### macOS

```bash
git clone https://github.com/TU_USUARIO/spot-sec.git
cd spot-sec

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
spotdl --download-ffmpeg
```

## Uso

Activa el entorno virtual y ejecuta el script:

```bash
source venv/bin/activate        # Windows: venv\Scripts\activate
python3 spotsec_v3.py
```

1. Elige la carpeta de destino.
2. Pega tus enlaces o títulos en la caja, **uno por línea**.
3. Ajusta formato, bitrate y demás opciones.
4. Pulsa **▶ INICIAR CACERÍA**.

### Ejemplo de lista

```text
# Mi lista de prueba
https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M
https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3
https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC?si=abc123
spotify:track:4uLU6hMCjMI75M1A2tKUQC
Artista - Nombre de la canción
https://open.spotify.com/track/ID|https://www.youtube.com/watch?v=ID_DE_YOUTUBE
```

La última línea usa el formato `spotify|youtube` de spotDL, que fuerza la fuente de audio.

### Opciones

| Opción | Descripción |
|---|---|
| Formato | `m4a`, `mp3`, `flac`, `opus`, `ogg`, `wav` |
| Bitrate | `auto`, `128k`, `192k`, `256k`, `320k` (se ignora en `flac` y `wav`) |
| Hilos | Descargas simultáneas (1–8) |
| Reintentos | Veces que se reintenta un objetivo fallido (0–3) |
| Existentes | Omitir, actualizar metadatos o sobrescribir archivos ya descargados |
| Subcarpeta | Crea una carpeta por playlist/álbum |
| Guardar registro | Guarda un `.txt` con el log en la carpeta de destino al terminar |

## Credenciales de Spotify (opcional, recomendado)

Sin credenciales propias, spotDL usa las compartidas y es fácil toparse con límites de peticiones. Para evitarlo:

1. Entra a <https://developer.spotify.com/dashboard> y crea una app gratuita.
2. Copia el **Client ID** y el **Client Secret**.
3. Pégalos en los campos «Spotify API» de la aplicación.

> ⚠️ Los ajustes se guardan en `~/.spotsec.json` (con permisos solo para tu usuario). El Client Secret queda en **texto plano** en ese archivo: no lo subas a ningún repositorio.

## Solución de problemas

| Problema | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'customtkinter'` | No activaste el entorno virtual: `source venv/bin/activate` |
| `externally-managed-environment` al usar pip | Usa un entorno virtual (ver instalación). Evita `--break-system-packages` |
| `No module named 'tkinter'` | Linux: `sudo apt install python3-tk` |
| spotDL no encuentra ffmpeg | Pulsa **⬇ ffmpeg** en la app o ejecuta `spotdl --download-ffmpeg` |
| Errores de límite de peticiones | Configura tu propio Client ID/Secret |
| Una canción no se encuentra | Pega junto al enlace de Spotify uno de YouTube con el formato `spotify\|youtube` |
| Dejó de funcionar de un día para otro | Pulsa **⟳ Actualizar spotdl**: YouTube cambia a menudo y spotDL necesita actualizarse |

## Cómo funciona

Spot-Sec es una capa de interfaz sobre spotDL: valida tu lista, construye el comando `spotdl download` con las opciones elegidas, lo ejecuta en un hilo aparte y analiza su salida para mostrar el progreso y los resultados.

## Aviso legal

Esta herramienta es un proyecto personal y **no está afiliada a Spotify ni a YouTube**. spotDL obtiene el audio desde fuentes de terceros, y descargar música protegida por derechos de autor puede infringir la ley o los términos de servicio de esas plataformas según tu país. Úsala solo con contenido que tengas derecho a descargar y bajo tu propia responsabilidad.

## Licencia

Elige una licencia para tu repositorio (por ejemplo [MIT](https://choosealicense.com/licenses/mit/)) y añade el archivo `LICENSE`.
