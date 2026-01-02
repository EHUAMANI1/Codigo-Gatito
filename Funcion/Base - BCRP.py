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
]

# Fecha inicial y final
periodo_inicial = '2003-01-01'
periodo_final = '2025-01-01'

# Idioma de las fechas
idioma = 'esp'  # 'ing' o 'esp'

def construir_url(series, periodo_inicial, periodo_final, idioma, formato):
    url_base = 'https://estadisticas.bcrp.gob.pe/estadisticas/series/api/'
    partes = ['-'.join(series), formato]
    if periodo_inicial:
        partes.append(periodo_inicial)
    if periodo_final:
        partes.append(periodo_final)
    if idioma:
        partes.append(idioma)
    return url_base + '/'.join(partes)

# =========================
# DESCARGA
# =========================
url_csv = construir_url(series, periodo_inicial, periodo_final, idioma, 'csv')
print("URL generada:")
print(url_csv)

response_csv = requests.get(url_csv)

# =========================
# DIAGNÓSTICO Y SALIDA LIMPIA
# =========================
if response_csv.status_code != 200:
    print("\n⛔ El servidor no permitió la descarga.")
    print("⚠️  Código HTTP:", response_csv.status_code)

    if response_csv.status_code == 403:
        print("➡️  HTTP 403: Acceso bloqueado por el servidor del BCRP.")
    elif response_csv.status_code == 429:
        print("➡️  HTTP 429: Demasiadas solicitudes.")
    else:
        print("➡️  Error HTTP:", response_csv.status_code)

    print("\n⛔ No se exporto los datos.\n")
    exit()

# =========================
# PROCESAMIENTO (solo si hay CSV)
# =========================
texto = response_csv.text.replace("<br>", "\n")
texto = texto.replace("&ntilde;", "ñ")
texto = texto.replace("n.d.", "")

df = pd.read_csv(StringIO(texto), sep=",", quotechar='"')
df = df.rename(columns={df.columns[0]: "Periodo"})

# Fechas
if (df['Periodo'].dtype == 'object') and (idioma == 'esp'):
    meses = {
        'Ene': '01', 'Feb': '02', 'Mar': '03', 'Abr': '04',
        'May': '05', 'Jun': '06', 'Jul': '07', 'Ago': '08',
        'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dic': '12'
    }
    df['Periodo'] = df['Periodo'].str.split('.').apply(
        lambda x: pd.to_datetime(f'{x[1]}-{meses[x[0]]}')
    )

elif idioma == 'ing':
    df['Periodo'] = pd.to_datetime(df['Periodo'], format='%b.%Y')

# Renombrar columnas
df.columns = [
    'Periodo',
    'Inflación',
    'Cobre',
    'PBI Desestacionalizado',
    'Ingresos Tributarios'
]

# Exportar
os.makedirs(os.path.dirname(archivo_salida), exist_ok=True)
df.to_csv(archivo_salida, index=False, encoding='utf-8-sig')

print("\n✅ Archivo generado correctamente:")
print(archivo_salida)

