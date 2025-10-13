# Linea temporal de las variables

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from datetime import datetime

# --- 1. CONFIGURACIÓN DE RUTAS, HOJA Y VARIABLES ---

base_dir = os.getcwd()
Entrada = os.path.join(base_dir, 'Flujo', 'input', 'Calculos wacc.xlsx')
output_dir = os.path.join(base_dir, 'Flujo', 'output')
os.makedirs(output_dir, exist_ok=True)

# --- ¡MODIFICA AQUÍ! ---
# 1. Define el nombre de la hoja que quieres leer.
nombre_de_la_hoja = 'Mercado'

# 2. Define las variables a graficar en una lista.
variables_a_graficar = ['Rendimiento S&P500', 'Rendimiento USGG10YR'] #['WACC', 'KE', 'TMAR']

# 3. Define los colores para CADA variable en el MISMO ORDEN.
colores_para_variables = ['blue', 'red'] #['blue', 'red', 'green'] 

# --- VALIDACIÓN INICIAL DE COLORES ---
if len(variables_a_graficar) != len(colores_para_variables):
    raise ValueError("El número de variables a graficar no coincide con el número de colores definidos.")

# --- 2. CARGA Y PREPARACIÓN DE DATOS ---

try:
    df = pd.read_excel(Entrada, engine='openpyxl', sheet_name=nombre_de_la_hoja)

    columnas_necesarias = ['Fecha'] + variables_a_graficar
    columnas_faltantes = [col for col in columnas_necesarias if col not in df.columns]

    if columnas_faltantes:
        print(f"Error: No se encontraron las siguientes columnas en la hoja '{nombre_de_la_hoja}': {columnas_faltantes}")
    else:
        # --- 3. PROCESAMIENTO Y GRÁFICO ---
        
        df_serie = df[columnas_necesarias].copy()
        df_serie['Fecha'] = pd.to_datetime(df_serie['Fecha'], errors='coerce')
        df_serie.dropna(inplace=True)
        df_serie = df_serie.sort_values(by='Fecha')

        print(f"Generando gráfico para: {variables_a_graficar}...")

        fig, ax = plt.subplots(figsize=(12, 6))

        # Bucle para graficar una o varias series con colores específicos
        for i, variable in enumerate(variables_a_graficar):
            ax.plot(df_serie['Fecha'], df_serie[variable], 
                    marker='o', linestyle='-', 
                    color=colores_para_variables[i],
                    label=variable,
                    markersize=3)

        # Formato de ejes y títulos
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        
        def percent_formatter(y, pos):
            return f'{100 * y:.1f}%'
        ax.yaxis.set_major_formatter(FuncFormatter(percent_formatter))

        ax.set_title('Bono con Vencimiento a 10 años (2022-2024)')
        ax.set_ylabel('Rendimiento (%)')

        ax.set_xlabel('Años')
        ax.grid(True)

        # Leyenda
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=len(variables_a_graficar))
        
        # Ajustar el diseño DESPUÉS de definir la leyenda para que haya espacio
        plt.tight_layout()

        # --- 4. EXPORTACIÓN DEL GRÁFICO (SOLO PNG) ---
        
        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        nombre_variables = '-'.join(variables_a_graficar)
        nombre_base = f'serie_temporal_{nombre_variables}_{fecha_hora}'

        ruta_salida_imagen = os.path.join(output_dir, f'{nombre_base}.png')
        # Usar bbox_inches='tight' para asegurar que la leyenda no se corte al guardar
        plt.savefig(ruta_salida_imagen, bbox_inches='tight') 
        plt.close()
        print(f"Gráfico PNG guardado en: {ruta_salida_imagen}")

except FileNotFoundError:
    print(f"Error: No se pudo encontrar el archivo de entrada en la ruta: {Entrada}")
except ValueError as ve:
    print(f"Error de configuración: {ve}")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")