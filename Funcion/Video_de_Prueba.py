import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import os
import imageio_ffmpeg

# --- 0. CONFIGURACIÓN ---
plt.rcParams['animation.ffmpeg_path'] = imageio_ffmpeg.get_ffmpeg_exe()
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['font.family'] = 'serif'

# --- 1. RUTAS ---
base_dir = os.getcwd()
archivo_salida = os.path.join(base_dir, 'Flujo', 'output', 'pringles_acumulativo_lento.mp4')
print(f"1. Preparando video (Acumulativo + Construcción Lenta).\n   Salida: {archivo_salida}")

# --- 2. DATOS MATEMÁTICOS ---
RADIO_MAX = 2.5
RES_RADIO = 60   # Más resolución para que se vea bonito al crecer lento
RES_ANGULO = 120 
theta = np.linspace(0, 2*np.pi, RES_ANGULO)

# --- 3. TIEMPOS (FRAMES a 60 FPS) ---
# Cronología Acumulativa
T_INTRO = 40        # 0.6s: Aparece "Esta es la función"
T_PAUSA_1 = 70      # Pausa breve
T_NOMBRE = 40       # 0.6s: Aparece "Paraboloide Hiperbólico"
T_PAUSA_2 = 20      # Pausa breve
T_CRECIMIENTO = 240 # 4.0s: ¡Construcción LENTA! (Antes era 2s)
T_FINAL = 240       # 4.0s: Rotación + Fórmula

# Hitos de tiempo acumulados
HITO_1 = T_INTRO + T_PAUSA_1
HITO_2 = HITO_1 + T_NOMBRE + T_PAUSA_2
HITO_3 = HITO_2 + T_CRECIMIENTO

TOTAL_FRAMES = HITO_3 + T_FINAL

# --- 4. ESCENA ---
fig = plt.figure(figsize=(9, 16), facecolor='#010409') 
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#010409')
ax.set_axis_off()

# Límites
lim = 3
ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(-lim, lim)

# --- 5. TEXTOS (POSICIONES FIJAS) ---

# A) TEXTO INTRO (Muy arriba)
txt_intro = fig.text(0.5, 0.82, "Esta es la función", 
                     ha='center', va='center', 
                     color='#36CCE1', fontsize=28, alpha=0)

# B) NOMBRE DE LA FUNCIÓN (Un poco más abajo, más grande)
txt_nombre = fig.text(0.5, 0.76, "Paraboloide Hiperbólico", 
                      ha='center', va='center', 
                      color='#36CCE1', fontsize=36, alpha=0)

# C) FÓRMULA (Abajo del todo)
txt_formula = fig.text(0.5, 0.25, r'$z = \dfrac{x^2}{a^2} - \dfrac{y^2}{b^2}$', 
                       ha='center', va='center', 
                       color='#36CCE1', fontsize=30, alpha=0)

# D) EJES 3D (Invisibles al inicio)
ejes_lineas = []
ejes_textos = []
# Líneas
l1, = ax.plot([-3, 3], [0, 0], [0, 0], color='white', lw=0.8, alpha=0)
l2, = ax.plot([0, 0], [-3, 3], [0, 0], color='white', lw=0.8, alpha=0)
l3, = ax.plot([0, 0], [0, 0], [-2, 2], color='white', lw=0.8, alpha=0)
ejes_lineas = [l1, l2, l3]
# Textos ejes
lbl_x = ax.text(3.2, 0, 0, "x", color='white', fontsize=14, alpha=0)
lbl_y = ax.text(0, 3.2, 0, "y", color='white', fontsize=14, alpha=0)
lbl_z = ax.text(0, 0, 2.2, "z", color='white', fontsize=14, alpha=0)
ejes_textos = [lbl_x, lbl_y, lbl_z]

surf = None

# --- 6. ANIMACIÓN ---
def animate(i):
    global surf
    if surf: surf.remove()
    
    # --- FASE 1: APARECE "ESTA ES LA FUNCIÓN" ---
    if i < T_INTRO:
        alpha = i / T_INTRO
        txt_intro.set_alpha(alpha)
        return []
    
    # PAUSA 1
    elif i < HITO_1:
        txt_intro.set_alpha(1)
        return []

    # --- FASE 2: APARECE "PARABOLOIDE HIPERBÓLICO" ---
    elif i < (HITO_1 + T_NOMBRE):
        txt_intro.set_alpha(1) # El anterior se queda
        
        frame_actual = i - HITO_1
        alpha = frame_actual / T_NOMBRE
        txt_nombre.set_alpha(alpha)
        return []

    # PAUSA 2 (Antes de la gráfica)
    elif i < HITO_2:
        txt_intro.set_alpha(1)
        txt_nombre.set_alpha(1)
        return []

    # --- FASE 3: CONSTRUCCIÓN LENTA DE LA GRÁFICA ---
    elif i < HITO_3:
        txt_intro.set_alpha(1)
        txt_nombre.set_alpha(1)
        
        # Mostrar ejes suavemente al inicio de esta fase
        for obj in ejes_lineas + ejes_textos: obj.set_alpha(0.5)

        # Progreso de crecimiento (0 a 1)
        progreso = (i - HITO_2) / T_CRECIMIENTO # Ahora dura 4 segundos
        
        # Efecto suavizado (ease out)
        radio_actual = RADIO_MAX * (1 - (1 - progreso)**3)
        if radio_actual < 0.1: radio_actual = 0.1
        
        # Malla parcial
        r_ = np.linspace(0, radio_actual, RES_RADIO)
        R, THETA = np.meshgrid(r_, theta)
        X = R * np.cos(THETA); Y = R * np.sin(THETA)
        Z = (X**2 - Y**2) / 3.5
        
        ax.view_init(elev=30, azim=45)
        surf = ax.plot_surface(X, Y, Z, cmap='cool', rstride=1, cstride=1, alpha=0.8, linewidth=0, shade=True)

    # --- FASE 4: ROTACIÓN + FÓRMULA ---
    else:
        # Asegurar todo visible
        txt_intro.set_alpha(1)
        txt_nombre.set_alpha(1)
        for obj in ejes_lineas + ejes_textos: obj.set_alpha(0.5)

        # Malla completa
        r_ = np.linspace(0, RADIO_MAX, RES_RADIO)
        R, THETA = np.meshgrid(r_, theta)
        X = R * np.cos(THETA); Y = R * np.sin(THETA)
        Z = (X**2 - Y**2) / 3.5
        
        # Rotación
        frames_rotando = i - HITO_3
        ax.view_init(elev=30, azim=45 + frames_rotando * 0.5)
        
        # Aparece fórmula
        alpha_f = frames_rotando / 60
        if alpha_f > 1: alpha_f = 1
        txt_formula.set_alpha(alpha_f)
        
        surf = ax.plot_surface(X, Y, Z, cmap='cool', rstride=1, cstride=1, alpha=0.8, linewidth=0, shade=True)

    return surf,

print(f"2. Renderizando... ({TOTAL_FRAMES} frames - Aprox {TOTAL_FRAMES/60:.1f} segundos)")
ani = animation.FuncAnimation(fig, animate, frames=TOTAL_FRAMES, interval=16, blit=False)

try:
    ani.save(archivo_salida, writer='ffmpeg', fps=60, bitrate=6000)
    print(f"✅ ¡Video listo! Revisa:\n{archivo_salida}")
except Exception as e:
    print(f"❌ Error: {e}")
plt.close()