# Estadistica Descriptiva
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from scipy.stats import kurtosis, skew, norm
import numpy as np
from matplotlib.ticker import FuncFormatter # <-- Importante tener esta línea

# --- 1. CONFIGURACIÓN DE RUTAS, HOJA Y VARIABLE ---

# Obtener el directorio actual
base_dir = os.getcwd()

# Ruta al archivo de entrada
Entrada = os.path.join(base_dir, 'Flujo', 'input', 'Calculos WACC.xlsx')

# --- ¡MODIFICA AQUÍ! ---
nombre_de_la_hoja = 'Riesgo País' #Hoja del archivo
variable = 'Riesgo Pais' # Nombre de la variable
mostrar_histograma_en_porcentaje = True #Histograma en porcentaje

# --- 2. CARGA Y PREPARACIÓN DE DATOS ---

try:
    # Cargar los datos desde la HOJA ESPECIFICADA del archivo Excel
    df = pd.read_excel(Entrada, engine='openpyxl', sheet_name=nombre_de_la_hoja)

    # Verificar que la columna a analizar exista en la hoja seleccionada
    if variable not in df.columns:
        print(f"Error: La columna '{variable}' no se encuentra en la hoja '{nombre_de_la_hoja}'.")
    else:

        # --- CÁLCULOS ESTADÍSTICOS Y EXPORTACIÓN A EXCEL (Esta sección no cambia) ---
        variable_stats = df[variable].describe()
        moda = df[variable].mode()[0]
        varianza = df[variable].var()
        coeficiente_variacion = df[variable].std() / df[variable].mean()
        rango = variable_stats['max'] - variable_stats['min']
        asimetria = skew(df[variable].dropna())
        curtosis_val = kurtosis(df[variable].dropna())
        
        stats_dict = {
            'Medida': ['Media', 'Mediana', 'Moda', 'Desviación estándar', 'Varianza', 'Rango', 
                       'Coeficiente de variación', 'Asimetría', 'Curtosis', 'Mínimo', '1er Cuartil', 
                       'Mediana', '3er Cuartil', 'Máximo'],
            'Valor': [
                variable_stats['mean'], df[variable].median(), moda, variable_stats['std'], 
                varianza, rango, coeficiente_variacion, asimetria, curtosis_val, 
                variable_stats['min'], variable_stats['25%'], variable_stats['50%'], 
                variable_stats['75%'], variable_stats['max']
            ]
        }
        stats_df = pd.DataFrame(stats_dict)

        fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_excel = os.path.join(base_dir, 'Flujo', 'output', f'estadistica_descriptiva_{variable}_{fecha_hora}.xlsx')
        stats_df.to_excel(output_excel, index=False)
        print(f"Estadística descriptiva exportada a {output_excel}")

        # --- CREACIÓN DE GRÁFICOS ---
        output_dir = os.path.join(base_dir, 'Flujo', 'output', f'box_hist_plots_{variable}')
        os.makedirs(output_dir, exist_ok=True)
        plot_color = 'lightblue'

        # --- CÓDIGO DEL BOXPLOT (Esta sección no cambia) ---
        
        fig, ax = plt.subplots(figsize=(5, 6))
        sns.boxplot(y=df[variable], color=plot_color, ax=ax, width=0.5)
        
        media = df[variable].mean()
        q1 = df[variable].quantile(0.25)
        mediana = df[variable].quantile(0.50)
        q3 = df[variable].quantile(0.75)
        iqr = q3 - q1
        limite_inferior = q1 - 1.5 * iqr
        bigote_inferior = df[variable][df[variable] >= limite_inferior].min()
        limite_superior = q3 + 1.5 * iqr
        bigote_superior = df[variable][df[variable] <= limite_superior].max()

        ax.axhline(media, color='blue', linestyle='--', linewidth=1.5, label=f'Media ({media*100:.2f}%)')
        
        posicion_x_cuartiles = 0.41
        ax.text(posicion_x_cuartiles, mediana, f'Me: {mediana*100:.2f}', va='center', ha='right', size='medium', color='black')
        ax.text(posicion_x_cuartiles, q3, f'Q3: {q3*100:.2f}', va='center', ha='right', size='medium', color='black')
        ax.text(posicion_x_cuartiles, q1, f'Q1: {q1*100:.2f}', va='center', ha='right', size='medium', color='black')

        posicion_x_extremos = 0.14
        ax.text(posicion_x_extremos, bigote_superior, f'Max: {bigote_superior*100:.2f}', va='center', ha='left', size='medium', color='black')
        ax.text(posicion_x_extremos, bigote_inferior, f'Min: {bigote_inferior*100:.2f}', va='center', ha='left', size='medium', color='black')

        ax.set_title('Diagrama de Caja')

        # Formateador para el eje Y del boxplot
        def percent_formatter_axis(y, pos):
            return f'{100 * y:.2f}' 
        ax.yaxis.set_major_formatter(FuncFormatter(percent_formatter_axis))

        ax.set_ylabel(f'{variable} (%)') # <-- Se sugiere añadir (%) aquí para coherencia
        ax.set_xlabel('')
        ax.set_xticks([])
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05))
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'boxplot_final_con_valores_{variable}.png'))
        plt.close()
        
        # --- HISTOGRAMA CON FORMATO CONDICIONAL ---
        plt.figure(figsize=(8, 6))
        sns.histplot(df[variable].dropna(), color=plot_color, bins=20, stat="density", label='Histograma')
        
        # --- INICIO DE LA MODIFICACIÓN ---
        # Lógica condicional para formatear el eje X del histograma
        if mostrar_histograma_en_porcentaje:
            # Si es True, aplica el formato de porcentaje
            def percent_formatter(x, pos):
                return f'{100 * x:.1f}%'
            plt.gca().xaxis.set_major_formatter(FuncFormatter(percent_formatter))
            plt.xlabel(f'{variable} (%)')
        else:
            # Si es False, solo pone la etiqueta normal
            plt.xlabel(variable)
        # --- FIN DE LA MODIFICACIÓN ---

        plt.title('Histograma')
        plt.ylabel('Densidad')
        mu, std = norm.fit(df[variable].dropna())
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        p = norm.pdf(x, mu, std)
        plt.plot(x, p, 'k', linewidth=2, label='Campana de Gauss')
        plt.legend()
        plt.savefig(os.path.join(output_dir, f'histograma_{variable}.png'))
        plt.close()

        print(f"Gráficos guardados en la carpeta: {output_dir}")

except FileNotFoundError:
    print(f"Error: No se pudo encontrar el archivo de entrada en la ruta: {Entrada}")
except ValueError:
    # Este error ahora te avisará si la hoja no existe
    print(f"Error: No se pudo encontrar la hoja '{nombre_de_la_hoja}' en el archivo. Revisa el nombre.")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")