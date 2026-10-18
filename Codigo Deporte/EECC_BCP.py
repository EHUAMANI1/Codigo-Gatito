# ESTADOS DE CUENTA BCP

from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
import pdfplumber
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


# =========================
# RUTAS DE ENTRADA Y SALIDA
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
ENTRADA_DATOS = BASE_DIR / "Flujo" / "Estados_de_cuenta" / "EECC_BCP"
SALIDA_DATOS = BASE_DIR / "Flujo" / "Output" / "Movimientos_EECC_BCP.xlsx"

# Para ejecutarlo sin crear proyecto, opcionalmente modifica solo BASE_DIR.

MESES = {
    "ENE": 1, "FEB": 2, "MAR": 3, "ABR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AGO": 8,
    "SET": 9, "SEP": 9, "OCT": 10, "NOV": 11, "DIC": 12,
}
PATRON_FECHA = re.compile(r"^(\d{1,2})([A-Z]{3})$")
PATRON_CUENTA = re.compile(r"\b\d{3}-\d{6,12}-\d-\d{2}\b")
PATRON_PERIODO = re.compile(
    r"\bDEL\s+(\d{2}/\d{2}/\d{2,4})\s+AL\s+(\d{2}/\d{2}/\d{2,4})\b",
    re.IGNORECASE,
)
PATRON_IMPORTE = re.compile(r"^(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}$")
COLUMNAS = ["Fecha", "Numero de cuenta", "Descripcion", "Movimiento"]


def sin_tildes(cadena: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", cadena.upper())
        if unicodedata.category(c) != "Mn"
    )

# Agrupa palabras por su posición vertical, conservando las columnas PDF.
def filas_visuales(pagina: pdfplumber.page.Page) -> list[list[dict]]:
    palabras = pagina.extract_words(x_tolerance=1.5, y_tolerance=2.5)
    palabras.sort(key=lambda p: (p["top"], p["x0"]))
    filas: list[list[dict]] = []
    for palabra in palabras:
        if not filas or abs(palabra["top"] - filas[-1][0]["top"]) > 2.4:
            filas.append([palabra])
        else:
            filas[-1].append(palabra)
    for fila in filas:
        fila.sort(key=lambda p: p["x0"])
    return filas


# Detecta columnas usando los títulos impresos; no usa palabras como YAPE/PLIN.
def obtener_columnas(filas: list[list[dict]]) -> tuple[float, float, float, float] | None:
    for fila in filas:
        palabras = {sin_tildes(p["text"]): p for p in fila}
        if not all(p in palabras for p in ("VALOR", "DESCRIPCION", "CARGOS", "ABONOS")):
            continue
        fechas = [p for p in fila if sin_tildes(p["text"]) == "FECHA"]
        if len(fechas) < 2:
            continue
        x_fecha_valor = fechas[1]["x0"]
        x_fecha_proc = fechas[0]["x0"]
        inicio_descripcion = x_fecha_valor + (x_fecha_valor - x_fecha_proc) - 5
        inicio_cargos = palabras["CARGOS"]["x0"] - 25
        centro_cargos = (palabras["CARGOS"]["x0"] + palabras["CARGOS"]["x1"]) / 2
        centro_abonos = (palabras["ABONOS"]["x0"] + palabras["ABONOS"]["x1"]) / 2
        limite_cargo_abono = (centro_cargos + centro_abonos) / 2
        return x_fecha_valor, inicio_descripcion, inicio_cargos, limite_cargo_abono
    return None

# Detecta las fechas del Estado de Cuenta
def leer_fecha_estado(texto: str) -> tuple[datetime, datetime]:
    resultado = PATRON_PERIODO.search(texto)
    if not resultado:
        raise ValueError("No encontré 'DEL dd/mm/aa AL dd/mm/aa' en el encabezado.")

    def convertir(cadena: str) -> datetime:
        formato = "%d/%m/%Y" if len(cadena.split("/")[-1]) == 4 else "%d/%m/%y"
        return datetime.strptime(cadena, formato)

    return convertir(resultado.group(1)), convertir(resultado.group(2))

# Convierte las fechas de PDF en formato de excel
def convertir_fecha_valor(cadena: str, inicio: datetime, fin: datetime) -> datetime:
    coincidencia = PATRON_FECHA.fullmatch(sin_tildes(cadena.strip()))
    if not coincidencia:
        raise ValueError(f"Fecha valor no reconocida: {cadena}")
    dia, nombre_mes = coincidencia.groups()
    mes = MESES.get(nombre_mes)
    if mes is None:
        raise ValueError(f"Mes no reconocido: {nombre_mes}")

    # Permite estados de cuenta que cruzan de diciembre a enero.
    opciones = []
    for anio in range(inicio.year - 1, fin.year + 2):
        try:
            fecha = datetime(anio, mes, int(dia))
        except ValueError:
            continue
        opciones.append(fecha)
    dentro = [f for f in opciones if inicio - timedelta(days=7) <= f <= fin + timedelta(days=7)]
    if dentro:
        return min(dentro, key=lambda f: abs((fin - f).days))
    if opciones:
        return min(opciones, key=lambda f: abs((fin - f).days))
    raise ValueError(f"Fecha valor inválida: {cadena}")

# Lee los importes
def leer_importe(cadena: str) -> Decimal | None:
    limpio = cadena.replace(" ", "")
    if not PATRON_IMPORTE.fullmatch(limpio):
        return None
    try:
        return Decimal(limpio.replace(",", ""))
    except InvalidOperation:
        return None

# Lee los valores impresos en la fila justo encima de TOTAL MOVIMIENTO.
def totales_impresos(filas: list[list[dict]], corte: float) -> tuple[Decimal, Decimal] | None:
    for i, fila in enumerate(filas):
        texto = " ".join(sin_tildes(p["text"]) for p in fila)
        if "TOTAL MOVIMIENTO" not in texto:
            continue
        for anterior in reversed(filas[max(0, i - 3):i]):
            importes = [
                (p["x0"], v)
                for p in anterior
                if (v := leer_importe(p["text"])) is not None
                and p["x0"] > corte - 120
            ]
            cargos = [v for x, v in importes if x < corte]
            abonos = [v for x, v in importes if x >= corte]
            if len(cargos) == 1 and len(abonos) == 1:
                return cargos[0], abonos[0]
    return None

# Extrae los registros del PDF, respetando FECHA VALOR, cargos y abonos.
def extraer_pdf(ruta_pdf: Path) -> tuple[list[dict], tuple[Decimal, Decimal] | None]:
    registros = []
    resumen = None
    with pdfplumber.open(ruta_pdf) as pdf:
        textos = "\n".join(p.extract_text() or "" for p in pdf.pages)
        if not textos.strip():
            raise ValueError("PDF escaneado sin texto; necesita OCR previo.")
        cuenta = PATRON_CUENTA.search(textos)
        if not cuenta:
            raise ValueError("No pude encontrar el CODIGO DE CUENTA.")
        numero_cuenta = cuenta.group(0)
        inicio, fin = leer_fecha_estado(textos)
        columnas_actuales = None

        for numero_pagina, pagina in enumerate(pdf.pages, start=1):
            filas = filas_visuales(pagina)
            columnas = obtener_columnas(filas)
            if columnas is not None:
                columnas_actuales = columnas
            if columnas_actuales is None:
                print(f"   Aviso: página {numero_pagina} sin cabecera de movimientos.")
                continue

            x_fecha_valor, x_desc, x_cargos, corte = columnas_actuales
            if numero_pagina == len(pdf.pages):
                resumen = totales_impresos(filas, corte) or resumen
            en_tabla = False
            for fila in filas:
                textos_fila = [sin_tildes(p["text"]) for p in fila]
                if all(t in textos_fila for t in ("VALOR", "DESCRIPCION", "CARGOS", "ABONOS")):
                    en_tabla = True
                    continue
                if not en_tabla:
                    continue
                if "TOTAL" in textos_fila and "MOVIMIENTO" in textos_fila:
                    break
                # En BCP, la primera fecha es PROC. y la segunda es VALOR.
                fechas = [
                    p for p in fila
                    if p["x0"] < x_desc and PATRON_FECHA.fullmatch(sin_tildes(p["text"]))
                ]
                if len(fechas) < 2:
                    continue  # Ignora SALDO ANTERIOR, encabezados y pie.
                fechas.sort(key=lambda p: p["x0"])
                palabra_valor = min(fechas, key=lambda p: abs(p["x0"] - x_fecha_valor))
                fecha = convertir_fecha_valor(palabra_valor["text"], inicio, fin)

                descripcion_palabras = [
                    p["text"] for p in fila
                    if p["x0"] >= x_desc and p["x0"] < x_cargos
                    and p["text"] != "*"
                    and not (p["text"] == "1" and p["x0"] > x_cargos - 50)
                ]
                descripcion = " ".join(descripcion_palabras).strip()
                if not descripcion:
                    raise ValueError(f"Movimiento sin descripción (página {numero_pagina}, {fecha:%d/%m/%Y}).")

                importes = [
                    (p["x0"], importe)
                    for p in fila if p["x0"] >= x_cargos
                    if (importe := leer_importe(p["text"])) is not None
                ]
                cargos = [v for x, v in importes if x < corte]
                abonos = [v for x, v in importes if x >= corte]
                if len(cargos) + len(abonos) != 1:
                    raise ValueError(
                        f"Importe ambiguo: página {numero_pagina}, {fecha:%d/%m/%Y}, "
                        f"'{descripcion}'; cargos={cargos}, abonos={abonos}."
                    )
                movimiento = abonos[0] if abonos else -cargos[0]
                registros.append({
                    "Fecha": fecha,
                    "Numero de cuenta": numero_cuenta,
                    "Descripcion": descripcion,
                    "Movimiento": movimiento,
                })

    if not registros:
        raise ValueError("No se identificaron operaciones en la tabla del estado de cuenta.")
    return registros, resumen

# Guarda la información en PDF
def guardar_excel(registros: list[dict], destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Mantenemos el orden original para operaciones de la misma fecha (ordenamiento estable).
    registros = sorted(registros, key=lambda item: item["Fecha"])
    df = pd.DataFrame(registros, columns=COLUMNAS)
    df["Movimiento"] = df["Movimiento"].map(float)
    df.to_excel(destino, sheet_name="Movimientos", index=False)

    libro = load_workbook(destino)
    hoja = libro["Movimientos"]
    hoja.freeze_panes = "A2"
    hoja.auto_filter.ref = hoja.dimensions
    azul_oscuro = PatternFill("solid", fgColor="17365D")
    azul_claro = PatternFill("solid", fgColor="F2F6FC")
    for celda in hoja[1]:
        celda.fill = azul_oscuro
        celda.font = Font(name="Aptos", size=11, bold=True, color="FFFFFF")
        celda.alignment = Alignment(horizontal="center", vertical="center")
    hoja.row_dimensions[1].height = 25

    anchuras = [16, 25, 48, 19]
    for num_columna, ancho in enumerate(anchuras, start=1):
        hoja.column_dimensions[get_column_letter(num_columna)].width = ancho
    for fila in range(2, hoja.max_row + 1):
        if fila % 2 == 0:
            for celda in hoja[fila]:
                celda.fill = azul_claro
        hoja.cell(fila, 1).number_format = "dd/mm/yyyy"
        hoja.cell(fila, 2).number_format = "@"  # Número de cuenta = texto.
        hoja.cell(fila, 4).number_format = '#,##0.00;[Red]-#,##0.00;0.00'
        hoja.cell(fila, 4).alignment = Alignment(horizontal="right")
    libro.save(destino)

# Busca la entrada y salida de la informacion y analiza si el codigo funciona correctamente
def main() -> None:
    if not ENTRADA_DATOS.is_dir():
        raise SystemExit(
            f"No existe la carpeta de entrada:\n{ENTRADA_DATOS}\n"
            "Verifica que el script esté dentro de una subcarpeta del proyecto."
        )
    archivos = sorted(
        p for p in ENTRADA_DATOS.rglob("*")
        if p.is_file() and p.suffix.lower() == ".pdf"
    )
    if not archivos:
        raise SystemExit(f"No encontré archivos PDF en {ENTRADA_DATOS}")

    todos = []
    problemas = []
    print(f"Se encontraron {len(archivos)} archivo(s) PDF.\n")
    for pdf in archivos:
        print(f"Procesando: {pdf.name}")
        try:
            movimientos, totales = extraer_pdf(pdf)
        except Exception as exc:
            problemas.append(f"{pdf.name}: {exc}")
            print(f"  ERROR: {exc}\n")
            continue

        cargos = sum((-r["Movimiento"] for r in movimientos if r["Movimiento"] < 0), Decimal("0"))
        abonos = sum((r["Movimiento"] for r in movimientos if r["Movimiento"] > 0), Decimal("0"))
        print(f"  Operaciones: {len(movimientos)} | Cargos: {cargos:,.2f} | Abonos: {abonos:,.2f}")
        if totales is not None:
            esperado_cargo, esperado_abono = totales
            coincide = cargos == esperado_cargo and abonos == esperado_abono
            print(f"  Control BCP: {'OK' if coincide else 'DIFERENCIA - REVISAR'} "
                  f"(PDF: cargos {esperado_cargo:,.2f}; abonos {esperado_abono:,.2f})")
            if not coincide:
                problemas.append(f"{pdf.name}: los movimientos no cuadran con TOTAL MOVIMIENTO")
        else:
            print("  Control BCP: no se encontró fila de totales para validar.")
        todos.extend(movimientos)
        print()

    if todos:
        guardar_excel(todos, SALIDA_DATOS)
        print(f"LISTO: {len(todos)} movimientos en total")
        print(f"Archivo Excel: {SALIDA_DATOS}")
    else:
        print("No se generó Excel: no se pudieron extraer movimientos.")
    if problemas:
        print("\nATENCIÓN - REVISAR:")
        for problema in problemas:
            print(f" - {problema}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
