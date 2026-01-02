import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# =========================
# FFMPEG (forzado)
# =========================
try:
    import imageio_ffmpeg
    plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
except Exception as e:
    raise RuntimeError(
        "FFmpeg no está disponible en ESTE Python.\n"
        "Ejecuta:\n"
        "  python -m pip install -U imageio imageio-ffmpeg\n"
        f"Detalle: {e}"
    )

# =========================
# CONFIGURACIÓN GENERAL
# =========================
COLOR_FONDO = "#000000"
COLOR_TEXTO = "#36CCE1"
COLOR_DORADO = "#D4AF37"

FPS = 30
INTERVAL_MS = int(1000 / FPS)

FRAMES_POR_CHUNK = 8
PAUSA_PROBLEMA_FRAMES = int(1.5 * FPS)

FADE_IN_FRAMES = 10
HOLD_FRAMES = 28
FADE_OUT_FRAMES = 10
FINAL_HOLD_FRAMES = 75

# ✅ NUEVO: esperar 1 segundo antes del fuego
DELAY_FUEGOS_FRAMES = int(1.0 * FPS)

# ✅ NUEVO: duración del fuego (más lento en apagarse)
FUEGOS_FADE_FRAMES = int(2.5 * FPS)  # 2.5 segundos

plt.rcParams["mathtext.fontset"] = "cm"
plt.rcParams["font.family"] = "serif"
plt.rcParams["figure.facecolor"] = COLOR_FONDO
plt.rcParams["axes.facecolor"] = COLOR_FONDO
plt.rcParams["savefig.facecolor"] = COLOR_FONDO

# =========================
# SALIDA (anti caché)
# =========================
base_dir = os.getcwd()
output_folder = os.path.join(base_dir, "Flujo", "output")
os.makedirs(output_folder, exist_ok=True)
archivo_salida = os.path.join(
    output_folder, f"integral_new_year_2026_{np.random.randint(1000,9999)}.mp4"
)

# =========================
# CONTENIDO
# =========================
problema_chunks = [
    r"$P = $",
    r"$\int_{1}^{11}$",
    r"$\left( 2^x \ln 2 - 2 \right)$",
    r"$\,dx$",
]

titulo_text = r"$\mathit{Happy\ New\ Year}$"
TITULO_SIZE = 50
TITULO_Y = 0.68

resolucion = [
    {"text": r"$P = \left[ 2^x - 2x \right]_{1}^{11}$", "size": 45},
    {"text": r"$P =\left( 2^{11} - 2(11)\right)-\left(2^{1}-2(1)\right)$", "size": 35},
    {"text": r"$P =(2048-22)-(2-2)$", "size": 40},
]

resultado_final = {"text": r"$\mathbf{2026}$", "size": 75}

# =========================
# FRAMES
# =========================
frames_data = []

def add_frame(text, size, alpha, show_title):
    frames_data.append({
        "text": text,
        "size": size,
        "alpha": alpha,
        "show_title": show_title
    })

# Problema con escritura
current = ""
for chunk in problema_chunks:
    current += chunk
    for _ in range(FRAMES_POR_CHUNK):
        add_frame(current, 40, 1.0, False)

# Pausa 1.5s
for _ in range(PAUSA_PROBLEMA_FRAMES):
    add_frame(current, 40, 1.0, False)

# Fade out problema
for k in range(FADE_OUT_FRAMES):
    add_frame(current, 40, 1 - (k + 1) / FADE_OUT_FRAMES, False)

# Resoluciones con fade
for paso in resolucion:
    for k in range(FADE_IN_FRAMES):
        add_frame(paso["text"], paso["size"], (k + 1) / FADE_IN_FRAMES, True)
    for _ in range(HOLD_FRAMES):
        add_frame(paso["text"], paso["size"], 1.0, True)
    for k in range(FADE_OUT_FRAMES):
        add_frame(paso["text"], paso["size"], 1 - (k + 1) / FADE_OUT_FRAMES, True)

# Resultado final
for k in range(FADE_IN_FRAMES):
    add_frame(resultado_final["text"], resultado_final["size"], (k + 1) / FADE_IN_FRAMES, True)
for _ in range(FINAL_HOLD_FRAMES):
    add_frame(resultado_final["text"], resultado_final["size"], 1.0, True)

FINAL_START_INDEX = next(i for i, f in enumerate(frames_data) if f["text"] == resultado_final["text"])

# =========================
# FIGURA
# =========================
fig, ax = plt.subplots(figsize=(9, 16))
ax.axis("off")

# Fijar límites y desactivar autoscale (robusto con partículas)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_autoscale_on(False)

texto = ax.text(
    0.5, 0.5, "",
    ha="center", va="center",
    color=COLOR_TEXTO,
    fontsize=40
)

titulo = ax.text(
    0.5, TITULO_Y, titulo_text,
    ha="center", va="center",
    color=COLOR_TEXTO,
    fontsize=TITULO_SIZE,
    alpha=0.0
)

# =========================
# FUEGOS ARTIFICIALES (LENTOS)
# =========================
rng = np.random.default_rng(2026)

N = 420
angles = rng.uniform(0, 2*np.pi, N)

# ✅ MÁS LENTO: bajar velocidades
speeds = rng.uniform(0.0015, 0.008, N)

vx = speeds * np.cos(angles)
vy = speeds * np.sin(angles)

x0 = np.full(N, 0.5)
y0 = np.full(N, 0.5)

particles = ax.scatter(
    np.empty((0,)), np.empty((0,)),
    s=14, c=COLOR_DORADO, alpha=0.0,
    transform=ax.transAxes
)

# =========================
# DIBUJO FRAME (robusto)
# =========================
def draw_frame(i):
    d = frames_data[i]

    texto.set_text(d["text"])
    texto.set_fontsize(d["size"])
    texto.set_alpha(d["alpha"])

    if d["show_title"]:
        titulo.set_alpha(1.0)
        titulo.set_color(COLOR_DORADO)
    else:
        titulo.set_alpha(0.0)
        titulo.set_color(COLOR_TEXTO)

    # ✅ esperar 1s después de salir 2026 y recién disparar fuegos
    start_fire = FINAL_START_INDEX + DELAY_FUEGOS_FRAMES

    if i >= start_fire:
        t = i - start_fire

        xs = x0 + vx * t
        ys = y0 + vy * t

        particles.set_offsets(np.c_[xs, ys])

        # ✅ fade más lento (2.5s)
        particles.set_alpha(max(0.0, 1.0 - t / float(FUEGOS_FADE_FRAMES)))

        texto.set_color(COLOR_DORADO)
    else:
        particles.set_offsets(np.empty((0, 2)))
        particles.set_alpha(0.0)
        texto.set_color(COLOR_TEXTO)

# =========================
# EXPORT (frame-by-frame)
# =========================
writer = animation.FFMpegWriter(fps=FPS, bitrate=5000)

with writer.saving(fig, archivo_salida, dpi=200):
    for i in range(len(frames_data)):
        draw_frame(i)
        fig.canvas.draw()
        writer.grab_frame()

plt.close(fig)
print("✅ Video generado con animaciones + fuegos (delay 1s, explosión lenta):", archivo_salida)
print("FFmpeg:", plt.rcParams.get("animation.ffmpeg_path"))
