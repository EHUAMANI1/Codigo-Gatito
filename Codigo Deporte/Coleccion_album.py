# ALbum Mundial y Eurocopa
# Creado por Eduardo Huamani     22/03/26

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# 1. PARÁMETROS Y CONFIGURACIÓN 
# =====================================================================
TOTAL_FIGUS = 674       # Total de figuras diferentes en el album
FIGUS_POR_SOBRE = 7     # Cantidad de figuras por sobre
FIGURITAS_PEGADAS = 86  # Figuras diferentes pegadas en el album

LIMITE_REPETIDAS = 3    # Límite de tolerancia 

NUM_SIMULACIONES = 10000  # Iteraciones

NIVEL_CONFIANZA = 90   # Nivel de confianza

# =====================================================================
# 2. RUTAS DE ENTRADA Y SALIDA
# =====================================================================
base_dir = os.getcwd()

# Entrada
archivo_entrada = os.path.join(base_dir, 'Flujo', 'input', 'datos_album.xlsx') 

#Salida
salida_modelo = os.path.join(base_dir, 'Flujo', 'output', 'Resultados_modelo_album.png')
salida_simulacion = os.path.join(base_dir, 'Flujo', 'output', 'Resultado_simulacion_album.png')

# =====================================================================
# 3. PROCEDIMIENTO DEL MODELO PROBABILISTICO
# =====================================================================
def generar_imagen_modelo():
    print("⏳ Generando gráfico del Modelo Analítico...")
    sobres_abiertos_estimados = int(FIGURITAS_PEGADAS / FIGUS_POR_SOBRE)
    
    pegadas_simuladas = 0
    numero_sobre = 0
    eje_x_sobres = []
    eje_y_repetidas = []
    sobre_limite = None
    
    while pegadas_simuladas < TOTAL_FIGUS - 5:
        numero_sobre += 1
        prob_repetida = pegadas_simuladas / TOTAL_FIGUS
        repetidas_en_sobre = FIGUS_POR_SOBRE * prob_repetida
        nuevas_en_sobre = FIGUS_POR_SOBRE - repetidas_en_sobre
        
        eje_x_sobres.append(numero_sobre)
        eje_y_repetidas.append(repetidas_en_sobre)
        pegadas_simuladas += nuevas_en_sobre
        
        if sobre_limite is None and repetidas_en_sobre >= LIMITE_REPETIDAS:
            sobre_limite = numero_sobre

    plt.figure(figsize=(10, 6))
    plt.plot(eje_x_sobres, eje_y_repetidas, color='#d62728', linewidth=2.5, label='Repetidas esperadas por sobre')
    plt.axhline(y=LIMITE_REPETIDAS, color='orange', linestyle='-', linewidth=2, label=f'Límite ({LIMITE_REPETIDAS} repetidas)')
    plt.axvline(x=sobre_limite, color='black', linestyle='--', label=f'Limite de sobres ({sobre_limite})')
    
    prob_actual = FIGURITAS_PEGADAS / TOTAL_FIGUS
    repetidas_actuales_esperadas = FIGUS_POR_SOBRE * prob_actual
    plt.plot(sobres_abiertos_estimados, repetidas_actuales_esperadas, marker='o', markersize=10, color='blue', label='Tu estado actual')
    
    plt.title('Modelo Teórico', fontsize=14, fontweight='bold')
    plt.xlabel('Número de sobres Comprado', fontsize=12)
    plt.ylabel('Cantidad de repetidas por sobre', fontsize=12)
    plt.fill_between(eje_x_sobres, LIMITE_REPETIDAS, eje_y_repetidas, where=[s >= sobre_limite for s in eje_x_sobres], color='red', alpha=0.15)
    plt.grid(True, linestyle=':', alpha=0.7)
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(salida_modelo, dpi=300)
    plt.close()
    print(f"✅ Listo")

# =====================================================================
# 4. SIMULACION DE MONTECARLO
# =====================================================================
def generar_imagen_montecarlo():
    print(f"⏳ Corriendo Simulación de Montecarlo ({NUM_SIMULACIONES} iteraciones)...")
    
    resultados_sobres_limite = []
    limite_real_entero = int(np.ceil(LIMITE_REPETIDAS)) 
    
    for _ in range(NUM_SIMULACIONES):
        album = np.zeros(TOTAL_FIGUS) 
        sobres_comprados = 0
        
        while True:
            sobres_comprados += 1
            sobre_actual = np.random.choice(TOTAL_FIGUS, FIGUS_POR_SOBRE, replace=False)
            repetidas_en_sobre = np.sum(album[sobre_actual])
            
            if repetidas_en_sobre >= limite_real_entero:
                resultados_sobres_limite.append(sobres_comprados)
                break
                
            album[sobre_actual] = 1

    # --- CÁLCULO DEL NIVEL DE CONFIANZA ---
    # Si la confianza es 95%, cortamos el 2.5% inferior y el 2.5% superior.
    margen_error = (100 - NIVEL_CONFIANZA) / 2
    limite_inferior_porcentaje = margen_error
    limite_superior_porcentaje = 100 - margen_error

    promedio = np.mean(resultados_sobres_limite)
    percentil_inf = np.percentile(resultados_sobres_limite, limite_inferior_porcentaje) 
    percentil_sup = np.percentile(resultados_sobres_limite, limite_superior_porcentaje)

    # Gráfica
    plt.figure(figsize=(10, 6))
    plt.hist(resultados_sobres_limite, bins=range(min(resultados_sobres_limite), max(resultados_sobres_limite) + 1), 
             color='#1f77b4', edgecolor='black', alpha=0.7)
    
    plt.axvline(x=promedio, color='red', linestyle='-', linewidth=2, label=f'Promedio (Sobre {int(promedio)})')
    plt.axvline(x=percentil_inf, color='orange', linestyle='--', linewidth=2, label=f'Límite Inferior (Sobre {int(percentil_inf)})')
    plt.axvline(x=percentil_sup, color='green', linestyle='--', linewidth=2, label=f'Límite Superior (Sobre {int(percentil_sup)})')
    
    # Resaltar el RANGO seguro según el nivel de confianza
    plt.axvspan(percentil_inf, percentil_sup, color='yellow', alpha=0.2, 
                label=f'Intervalo de Confianza {NIVEL_CONFIANZA}%')

    plt.title(f'Simulación Montecarlo', fontsize=14, fontweight='bold')
    plt.xlabel('Número de sobres', fontsize=12)
    plt.ylabel('Casos simulados', fontsize=12)
    plt.grid(True, linestyle=':', alpha=0.4, axis='y')
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(salida_simulacion, dpi=300)
    plt.close()
    print(f"✅ Listo")


# =====================================================================
# 5. EJECUCIÓN
# =====================================================================
print("="*50)
print("🚀 Iniciando analisis")
print("="*50)

generar_imagen_modelo()
generar_imagen_montecarlo()

print("="*50)
print("🎉 Proceso terminado.")