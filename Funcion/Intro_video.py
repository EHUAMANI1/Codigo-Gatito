import matplotlib.pyplot as plt
import matplotlib.animation as animation
import os
import imageio_ffmpeg

# --- 0. CONFIGURACIÓN ---
plt.rcParams['animation.ffmpeg_path'] = imageio_ffmpeg.get_ffmpeg_exe()
plt.rcParams['mathtext.fontset'] = 'cm' # Fuente matemática
plt.rcParams['font.family'] = 'serif'

# --- 1. CONFIGURACIÓN DE ALTURAS ---
Y_TEXTO_ARRIBA = 0.75
Y_IMAGEN_BASE = 0.30 
Y_IMAGEN_TOPE = 0.60 
Y_TEXTO_PRINGLES = 0.23

# --- 2. TIEMPOS Y VELOCIDAD ---
VELOCIDAD_LETRAS = 4   # Frames por letra (ajusta si quieres más rápido/lento)
TIEMPO_PAUSA_1 = 90    # 1.5 SEGUNDOS (1.5 * 60 fps)
TIEMPO_FADE_IMG = 40   # Aparición imagen
TIEMPO_PAUSA_2 = 15    # Breve pausa
TIEMPO_FADE_TXT = 30   # Aparición "Pringles"

# --- 3. RUTAS ---
base_dir = os.getcwd()
archivo_salida = os.path.join(base_dir, 'Flujo', 'output', 'video_intro.mp4')
ruta_imagen = os.path.join(base_dir, 'Flujo', 'input', 'Pringles.png')

print(f"1. Preparando intro (Letra por letra + Pausa 1.5s).\n   Salida: {archivo_salida}")

# --- 4. ESCENA ---
COLOR_FONDO = '#010409'
COLOR_TEXTO = '#36CCE1'

fig, ax = plt.subplots(figsize=(9, 16), facecolor=COLOR_FONDO)
ax.set_facecolor(COLOR_FONDO)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis('off')

# --- 5. CREAR ELEMENTOS ---

# A) TEXTO PREGUNTA (Empieza vacío para escribirse)
texto_pregunta = "¿Sabías que este\nsnacks sigue una\nfunción matemática?"
txt_pregunta_obj = ax.text(0.5, Y_TEXTO_ARRIBA, "", 
                           ha='center', va='center', 
                           color=COLOR_TEXTO, fontsize=30, linespacing=1.5,
                           zorder=10)

# B) IMAGEN
try:
    img_data = plt.imread(ruta_imagen)
    img_obj = ax.imshow(img_data, extent=[0.2, 0.8, Y_IMAGEN_BASE, Y_IMAGEN_TOPE], 
                        aspect='auto', zorder=5)
    img_obj.set_alpha(0) 
except FileNotFoundError:
    print(f"❌ ERROR: Imagen no encontrada en {ruta_imagen}")
    exit()

# C) TEXTO PRINGLES
texto_pringles = "Pringles"
txt_pringles_obj = ax.text(0.5, Y_TEXTO_PRINGLES, texto_pringles, 
                           ha='center', va='center', 
                           color=COLOR_TEXTO, fontsize=40, weight='bold',
                           alpha=0, zorder=10)

# --- 6. CÁLCULO DE TIEMPOS ---
frames_escribir = len(texto_pregunta) * VELOCIDAD_LETRAS
frames_pausa_larga = TIEMPO_PAUSA_1 # 90 frames (1.5s)
frames_fade_img = TIEMPO_FADE_IMG
frames_pausa_media = TIEMPO_PAUSA_2
frames_fade_txt = TIEMPO_FADE_TXT
frames_final = 60

total_frames = (frames_escribir + frames_pausa_larga + frames_fade_img + 
                frames_pausa_media + frames_fade_txt + frames_final)

# --- 7. ANIMACIÓN ---
def animate(i):
    
    # --- FASE 1: ESCRIBIENDO (Letra por Letra) ---
    if i < frames_escribir:
        caracteres = int(i / VELOCIDAD_LETRAS) + 1
        txt_pregunta_obj.set_text(texto_pregunta[:caracteres])
        
    # --- FASE 2: PAUSA DE 1.5 SEGUNDOS (Texto completo) ---
    elif i < (frames_escribir + frames_pausa_larga):
        txt_pregunta_obj.set_text(texto_pregunta)

    # --- FASE 3: APARECE IMAGEN (Fade In) ---
    elif i < (frames_escribir + frames_pausa_larga + frames_fade_img):
        txt_pregunta_obj.set_text(texto_pregunta)
        
        frame_actual = i - (frames_escribir + frames_pausa_larga)
        alpha = frame_actual / frames_fade_img
        if alpha > 1: alpha = 1
        img_obj.set_alpha(alpha)

    # --- FASE 4: PAUSA BREVE ---
    elif i < (frames_escribir + frames_pausa_larga + frames_fade_img + frames_pausa_media):
        txt_pregunta_obj.set_text(texto_pregunta)
        img_obj.set_alpha(1)

    # --- FASE 5: APARECE "PRINGLES" (Fade In) ---
    elif i < (frames_escribir + frames_pausa_larga + frames_fade_img + frames_pausa_media + frames_fade_txt):
        txt_pregunta_obj.set_text(texto_pregunta)
        img_obj.set_alpha(1)
        
        frame_actual = i - (frames_escribir + frames_pausa_larga + frames_fade_img + frames_pausa_media)
        alpha = frame_actual / frames_fade_txt
        if alpha > 1: alpha = 1
        txt_pringles_obj.set_alpha(alpha)

    # --- FINAL ---
    else:
        txt_pregunta_obj.set_text(texto_pregunta)
        img_obj.set_alpha(1)
        txt_pringles_obj.set_alpha(1)

    return txt_pregunta_obj, img_obj, txt_pringles_obj

print(f"2. Renderizando... ({total_frames} frames)")

ani = animation.FuncAnimation(fig, animate, frames=total_frames, interval=16, blit=False)
try:
    ani.save(archivo_salida, writer='ffmpeg', fps=60, bitrate=5000)
    print(f"✅ ¡Video listo! Revisa: {archivo_salida}")
except Exception as e:
    print(f"❌ Error: {e}")
plt.close()