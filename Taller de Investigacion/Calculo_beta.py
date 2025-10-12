import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np

# Obtener el directorio actual donde está el script de Python
base_dir = os.getcwd()

# --- CONFIGURACIÓN DE RUTAS ---
# Ruta completa al archivo Excel de entrada
archivo_entrada = os.path.join(base_dir, 'Flujo', 'output', 'variacion_porcentual_wacc_2025-10-12_10-25-39.xlsx')

# Directorio de salida para las imágenes
output_dir_plots = os.path.join(base_dir, 'Flujo', 'output', 'scatter_plots_positivos')
os.makedirs(output_dir_plots, exist_ok=True) # Crea el directorio si no existe

# Nombre del archivo Excel de salida para los resultados
archivo_salida_excel = os.path.join(base_dir, 'Flujo', 'output', 'pendientes_beta_positivas.xlsx')

# --- CARGA DE DATOS ---
df_variacion = pd.read_excel(archivo_entrada, engine='openpyxl')

# --- PROCESAMIENTO Y GRÁFICOS ---

# Lista para almacenar los resultados (empresa y su pendiente)
resultados_pendientes = []

# Definir las variables para el eje Y
variables_y = [col for col in df_variacion.columns if col not in ['Fecha', 'SP500']]

# Función para formatear los ejes como porcentaje
def percent(x, pos):
    return f'{100*x:.1f}%'

# Generar un gráfico por cada variable en Y
for variable in variables_y:
    
    # Crea un DataFrame temporal y elimina las filas con NaN
    df_temp = df_variacion[['SP500', variable]].dropna()

    if df_temp.empty:
        continue # Si no hay datos, salta a la siguiente variable

    # Asigna los datos limpios a 'x' e 'y'
    x = df_temp['SP500']
    y = df_temp[variable]
    
    # Calcula los coeficientes de la línea de tendencia
    m, b = np.polyfit(x, y, 1)

    # --- NUEVA CONDICIÓN: SOLO PROCESAR SI LA PENDIENTE ES POSITIVA ---
    if m > 0:
        print(f"Procesando '{variable}': Pendiente positiva ({m:.4f}). Generando gráfico...")

        # Almacenar el resultado en la lista
        resultados_pendientes.append({'Empresa': variable, 'Pendiente_Beta': m})

        # --- Creación del Gráfico ---
        plt.figure(figsize=(8, 6))
        plt.scatter(x, y, alpha=0.5, c='black')
        plt.plot(x, m*x + b, color='black', linewidth=1.5, label='Línea de Tendencia')

        # Configuración del gráfico
        plt.title('Diagrama de Dispersión')
        plt.xlabel('Rendimiento de S&P500 en %')
        plt.ylabel(f'Rendimiento de {variable} por acción en %')
        plt.grid(True)
        plt.legend()
        plt.gca().xaxis.set_major_formatter(FuncFormatter(percent))
        plt.gca().yaxis.set_major_formatter(FuncFormatter(percent))
        
        # Guarda la imagen
        output_image = os.path.join(output_dir_plots, f'beta_{variable}_vs_SP500.png')
        plt.savefig(output_image)
        plt.close()
    else:
        # Mensaje opcional para saber cuáles se omitieron
        print(f"Omitiendo '{variable}': Pendiente no positiva ({m:.4f}).")


# --- EXPORTACIÓN DE RESULTADOS A EXCEL ---
if resultados_pendientes:
    # Crear un DataFrame de pandas a partir de la lista de resultados
    df_resultados = pd.DataFrame(resultados_pendientes)

    # Exportar el DataFrame a un archivo Excel
    df_resultados.to_excel(archivo_salida_excel, index=False, engine='openpyxl')
    print(f"\nResultados de pendientes positivas exportados a: {archivo_salida_excel}")
else:
    print("\nNo se encontraron variables con pendiente positiva. No se generó el archivo Excel.")

print("\nProceso completado.")