import requests
import pandas as pd
import os
from io import StringIO


# Ruta de salida de informacion
base_dir = os.getcwd()
archivo_salida = os.path.join(base_dir, 'Flujo', 'output', 'Base de datos BCRP.csv')

# Código de las series económicas (mensuales)
series = [
    'PN01271PM', # Inflación: Variación del IPC.
    'PN01652XM', # Cotización del Cobre (LME).
    'PN01773AM', # PBI Desestacionalizado.
    'PN02347FM'  # Ingresos Tributarios reales.
    ] # Se recomienda que las series tengan el mismo periodo (Mensual, Trimestral o anual)

# Fecha inicial y final
periodo_inicial = '2003-01-01'
periodo_final = '2025-01-01'

# Idioma de las fechas
idioma = 'ing'  # Inglés: 'ing'  ---  Español: 'esp'

def construir_url(series, periodo_inicial, periodo_final, idioma, formato):
    url_base = 'https://estadisticas.bcrp.gob.pe/estadisticas/series/api/'
    partes = ['-'.join(series), formato]
    if periodo_inicial:
        partes.append(periodo_inicial)
    if periodo_final:
        partes.append(periodo_final)
    if idioma:
        partes.append(idioma)
    url = url_base + '/'.join(partes)
    return url

url_csv = construir_url(series, periodo_inicial, periodo_final, idioma, 'csv')
print(url_csv)

response_csv = requests.get(url_csv)

# Limpieza del HTML con formato csv
texto = response_csv.text.replace("<br>", "\n")  # convierte <br> en salto real
texto = texto.replace("&ntilde;", "ñ")  # arregla el texto
texto = texto.replace("n.d.", "") # Vacía los n.d.

df = pd.read_csv(StringIO(texto), sep=",", quotechar='"')
df = df.rename(columns={df.columns[0]: "Periodo"})
df.head()

# Si el idioma es español...
if (df['Periodo'].dtype == 'object') & (idioma == 'esp'):
    meses = {
        'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Ago': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12'
    }

    df['Periodo'] = df['Periodo'].str.split('.').apply(
        lambda x: pd.to_datetime(f'{x[1]}-{meses[x[0]]}')
        )

# Si el idioma es Inglés...
elif idioma == 'ing':
    df['Periodo'] = pd.to_datetime(df['Periodo'], format = '%b.%Y')

import requests

url = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01271PM/csv/2003-01-01/2025-01-01/ing"

response = requests.get(url)

print("STATUS CODE:", response.status_code)
print("CONTENT-TYPE:", response.headers.get("Content-Type"))
print("PREVIEW (primeros 300 caracteres):")
print(response.text[:300])

# =========================
# RENOMBRAR COLUMNAS
# =========================
df.columns = [
    'Periodo',
    'Inflación',
    'Cobre',
    'PBI Desestacionalizado',
    'Ingresos Tributarios'
]

# =========================
# EXPORTAR CSV (LO QUE FALTABA)
# =========================
os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')

print("✅ Archivo generado en:")
print(archivo_salida)



