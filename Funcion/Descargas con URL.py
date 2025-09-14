# Programa para descargar el modelo de finanzas
# Hecho por Eduardo M. Huamani Acosta               24/07/25

import os
import sys
import requests
import urllib.parse
import zipfile
import io

# Ruta completa donde estás ejecutando el script
base_dir = os.getcwd() 

# Agregar la carpeta padre al path para poder importar módulos desde allí
base_scr = sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from concurrent.futures import ThreadPoolExecutor
from Conexiones.connection import (
    FINANZAS_ALBAMAR_CAPITAL,
    FINANZAS_FARO,
    FINANZAS_FIBRA,
    FINANZAS_CUKIC,
    FINANZAS_BENAVIDES,
    finanzas_anlo_modelo,
    finanzas_mes_modelo
)


# Ruta en donde se guarda la descarga
carpeta_descargas = os.path.join(base_dir, "Flujo", "output", f'{finanzas_anlo_modelo}_{finanzas_mes_modelo}')
zip_final_nombre = os.path.join(carpeta_descargas, f'{finanzas_mes_modelo}_modelo_finanzas.zip')

# Diccionario de proyectos para renombrar carpetas
PROYECTO_FINANZAS = {
    "Cuba & Zela": "Cuba Zela", "Arenales": "Arenales", "Guardia Civil": "Miralba",
    "Independencia": "Independencia", "Ejercito": "Ejercito", "Bolivia": "Bolivia",
    "Villar": "Albamar Bea", "Habich": "Parque Habich", "Chorrillos Freund": "Albamar Brisana",
    "Patriotas": "Patriotas", "Marsano": "Albamar Aura", "Oasis": "Oasis",
    "View 411": "View411", "Scala": "Edificio Scala", "Altuars": "Altuars",
    "Park Town": "Casimiro", "Colonial": "Colonial"
}

def url_existe(url):
    try:
        r = requests.head(url, allow_redirects=True, timeout=1)
        return r.status_code == 200
    except requests.RequestException:
        return False

def encontrar_url_valida(url_template):
    for dia_num in range(31, 0, -1):
        dia = f"{dia_num:02d}"
        url = url_template.format(dia=dia)
        if url_existe(url):
            print(f"✅ Se encontró URL válida: {url}")
            return url
    print("❌ No se encontró URL válida en rango de días para esta URL.")
    return None


def encontrar_urls_validas_para_todos():
    urls = {
        "Albamar_Capital": FINANZAS_ALBAMAR_CAPITAL,
        "Faro": FINANZAS_FARO,
        "Fibra": FINANZAS_FIBRA,
        "Cukic": FINANZAS_CUKIC,
        "Benavides": FINANZAS_BENAVIDES,
    }
    
    resultados = {}
    for grupo, url_template in urls.items():
        print(f"\n🔍 Buscando URL para {grupo}...")
        url_valida = encontrar_url_valida(url_template)
        resultados[grupo] = url_valida
    return resultados


if not os.path.exists(carpeta_descargas):
    os.makedirs(carpeta_descargas)

# Inicia la descarga de los archivos
def descargar_contenido(url, nombre_carpeta):
    nombre_archivo_codificado = url.split('/')[-1].split('?')[0]
    nombre_archivo = urllib.parse.unquote(nombre_archivo_codificado)
    nombre_en_zip = f"{nombre_carpeta}.zip"  # Solo para logs

    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        if response.status_code == 404:
            print(f"❌ No se encontró la carpeta: {nombre_carpeta} (HTTP 404)")
            return None
        response.raise_for_status()
        print(f'✅ Descargado contenido para: {nombre_en_zip}')
        return (nombre_carpeta, nombre_en_zip, response.content)
    except requests.exceptions.Timeout:
        print(f"❌ No se encontró la carpeta: {nombre_carpeta} (Timeout)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error descargando carpeta: {nombre_carpeta} (error: {e})")
    return None

def descargar_y_extraer_xlsx(urls):
    archivos = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = [executor.submit(descargar_contenido, url, carpeta) for url, carpeta in urls]
        for futuro in futuros:
            resultado = futuro.result()
            if resultado:
                archivos.append(resultado)

    if not archivos:
        print("⚠️  No se descargó ningún archivo.")
        return

    # Crea el zip final solo con archivos que elegí
    with zipfile.ZipFile(zip_final_nombre, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for nombre_carpeta, nombre_zip, contenido_zip in archivos:
            try:
                with zipfile.ZipFile(io.BytesIO(contenido_zip)) as zip_interno:
                    for archivo in zip_interno.namelist():
                        archivo_lower = archivo.lower()
                        if archivo_lower.endswith(('.xlsx', '.xlsm')) \
                            and "ficha" not in archivo_lower \
                            and "kpis" not in archivo_lower \
                            and "usos" not in archivo_lower:

                            with zip_interno.open(archivo) as file_xlsx:
                                contenido_xlsx = file_xlsx.read()

                                # Mantener la ruta original de la descarga con renombrado de carpetas
                                if '/' not in archivo:
                                    if nombre_carpeta == "Cukic":
                                        nombre_en_zip_final = os.path.join(nombre_carpeta, "Patriotas", archivo)
                                    elif nombre_carpeta == "Benavides":
                                        nombre_en_zip_final = os.path.join(nombre_carpeta, "Casimiro", archivo)
                                    elif nombre_carpeta == "Albamar_Capital":
                                        nombre_en_zip_final = os.path.join(nombre_carpeta, "Colonial", archivo)
                                    else:
                                        nombre_en_zip_final = os.path.join(nombre_carpeta, archivo) 
                                else:
                                    partes_archivo = archivo.split('/') 
                                    # Cambio de nombre de las carpetas de los proyectos
                                    if partes_archivo:
                                        proyecto_original = partes_archivo[0]
                                        proyecto_renombrado = PROYECTO_FINANZAS.get(proyecto_original, proyecto_original)
                                        partes_archivo[0] = proyecto_renombrado

                                    nombre_en_zip_final = os.path.join(nombre_carpeta, *partes_archivo)

                                zipf.writestr(nombre_en_zip_final, contenido_xlsx)
                                print(f"📁 Archivo listo: {nombre_en_zip_final}")
            except zipfile.BadZipFile:
                print(f"❌ El contenido de {nombre_carpeta} no es un zip válido")

    print(f"\n✅ ZIP final creado en: {zip_final_nombre}")

if __name__ == "__main__":
    resultados = encontrar_urls_validas_para_todos()
    print("\n🔍 Resultados de búsqueda de URLs:")
    for grupo, url in resultados.items():
        simbolo = "✅" if url else "❌"
        print(f"{simbolo} {grupo}: ")

    # Filtrar solo las URLs válidas para descargar
    urls_a_descargar = [(url, grupo) for grupo, url in resultados.items() if url]

    if urls_a_descargar:
        descargar_y_extraer_xlsx(urls_a_descargar)
    else:
        print("No hay URLs válidas para descargar.")