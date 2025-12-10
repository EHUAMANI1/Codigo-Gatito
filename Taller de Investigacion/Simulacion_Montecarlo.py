import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from datetime import datetime

# ==============================================================================
# 1. FUNCIÓN AUXILIAR: NORMAL TRUNCADA 
# ==============================================================================
def generar_normal_positiva(media, desviacion, n_iteraciones):
    """
    Genera una distribución normal pero rechaza los negativos.
    Simula la opción 'Min: 0' de Crystal Ball.
    """
    datos = np.random.normal(media, desviacion, n_iteraciones)
    
    # Mientras existan números negativos, los volvemos a generar
    while (datos < 0).any():
        mask = datos < 0
        datos[mask] = np.random.normal(media, desviacion, mask.sum())
        
    return datos

# ==============================================================================
# 2. SECCIÓN DE VARIABLES (INPUTS)
# ==============================================================================
# --- Parámetros de la Simulación ---
n_iteraciones = 5000       
certeza_deseada = 95.0     

# --- Datos Financieros ---
rf_base     = 0.0375    # Tasa Libre de Riesgo
beta_base   = 0.493     # Beta
rm_base     = 0.0831    # Rendimiento de Mercado
riesgo_pais = 0.0193    # Riesgo País 

# --- Incertidumbre (Volatilidad) ---
# NOTA: Si la volatilidad es muy grande comparada con la media, 
# la gráfica se verá cortada a la izquierda (como una rampa).
volatilidad_rf   = 0.0054  
volatilidad_beta = 0.2055   
volatilidad_rm   = 0.0200  # Ajusté un poco esto (antes tenias 0.20 que es 20%, muy alto)
volatilidad_rp   = 0.0025  

# ==============================================================================
# 3. CONFIGURACIÓN DE RUTAS
# ==============================================================================
base_dir = os.getcwd()
input_folder = os.path.join(base_dir, 'Flujo', 'input')
output_folder = os.path.join(base_dir, 'Flujo', 'output')

os.makedirs(input_folder, exist_ok=True)
os.makedirs(output_folder, exist_ok=True)

fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
archivo_excel = os.path.join(output_folder, f'estadistica_WACC_{fecha_hora}.xlsx')
archivo_png   = os.path.join(output_folder, f'grafico_WACC_{fecha_hora}.png')

print(f"--- Iniciando Simulación (Solo Positivos - Truncada) ---")

# ==============================================================================
# 4. CÁLCULOS (MONTECARLO)
# ==============================================================================
np.random.seed(42)

# Usamos la nueva función en lugar de np.random.normal directo
rf_simulada   = generar_normal_positiva(rf_base, volatilidad_rf, n_iteraciones)
beta_simulada = generar_normal_positiva(beta_base, volatilidad_beta, n_iteraciones)
rm_simulada   = generar_normal_positiva(rm_base, volatilidad_rm, n_iteraciones)
rp_simulada   = generar_normal_positiva(riesgo_pais, volatilidad_rp, n_iteraciones)

# Fórmula WACC
wacc_simulado = (rf_simulada + beta_simulada*(1+(1-0.295)*(0.0818/0.78967)) * (rm_simulada - rf_simulada + rp_simulada))*0.78967 + (1-0.295)*0.2104*0.0818 

print(f"Promedio WACC simulado: {np.mean(wacc_simulado):.2%}")

# ==============================================================================
# 5. GUARDAR DATOS EN EXCEL
# ==============================================================================
df_resultados = pd.DataFrame({
    'Tasa_Libre_Riesgo': rf_simulada,
    'Beta': beta_simulada,
    'Rendimiento_Mercado': rm_simulada,
    'Riesgo_Pais': rp_simulada,
    'WACC_Simulado': wacc_simulado
})

with pd.ExcelWriter(archivo_excel) as writer:
    df_resultados.to_excel(writer, sheet_name='Datos', index=False)
    df_resultados.describe().to_excel(writer, sheet_name='Estadisticas')

print(f"Excel guardado en: {archivo_excel}")

# ==============================================================================
# 6. GENERAR Y GUARDAR GRÁFICO (PNG)
# ==============================================================================
print("Generando gráfico...")
fig, ax = plt.subplots(figsize=(10, 7))

# Límites
lim_inf = np.percentile(wacc_simulado, (100 - certeza_deseada) / 2)
lim_sup = np.percentile(wacc_simulado, 100 - (100 - certeza_deseada) / 2)
media_val = np.mean(wacc_simulado)

# Histograma
counts, bins, bars = ax.hist(wacc_simulado, bins=50, edgecolor='black', linewidth=0.5)

# Colorear
for bar in bars:
    centro = bar.get_x() + bar.get_width() / 2
    if lim_inf <= centro <= lim_sup:
        bar.set_facecolor('#1f49fa')
        bar.set_alpha(0.9)
    else:
        bar.set_facecolor('#fa8072')
        bar.set_alpha(0.8)

# Etiquetas
ax.set_title(f'Simulación WACC ({n_iteraciones} iteraciones)', fontsize=14, fontweight='bold')
ax.set_xlabel('Costo de Capital (%)', fontsize=12)
ax.set_ylabel('Frecuencia', fontsize=12)
ax.xaxis.set_major_formatter(mtick.PercentFormatter(xmax=1, decimals=2))
ax.grid(axis='y', alpha=0.3)

# Textos inferiores
ymax = max(counts)
pos_y = -ymax * 0.22 
estilo_caja = dict(boxstyle="round,pad=0.3", fc="white", ec="black")
estilo_azul = dict(boxstyle="round,pad=0.3", fc="white", ec="blue")

ax.text(lim_inf, pos_y, f'{lim_inf:.2%}', ha='center', va='top', bbox=estilo_caja, fontweight='bold')
ax.text(lim_sup, pos_y, f'{lim_sup:.2%}', ha='center', va='top', bbox=estilo_caja, fontweight='bold')
ax.text(media_val, pos_y, f'Certeza: {certeza_deseada:.0f}%', ha='center', va='top', bbox=estilo_azul, color='blue', fontweight='bold')

# Líneas y ajustes
ax.axvline(lim_inf, color='black', linestyle='--', alpha=0.5)
ax.axvline(lim_sup, color='black', linestyle='--', alpha=0.5)
plt.subplots_adjust(bottom=0.3)

plt.savefig(archivo_png, dpi=300, bbox_inches='tight')
plt.close()

print(f"Gráfico PNG guardado en: {archivo_png}")