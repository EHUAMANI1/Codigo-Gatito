# Código de Python para obtener la rentabilidad en las apuestas
# Hecho por Eduardo Huamani

import os
from datetime import datetime

import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# PARAMETROS DE ENTRADA
base_dir = os.getcwd()
archivo_entrada = os.path.join(base_dir, 'Flujo', 'input', 'Datos_apuesta.xlsx')

# SALIDA DE INFORMACION
fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
resultado_variacion = os.path.join(base_dir, 'Flujo', 'output', f'Datos_{fecha_hora}.xlsx')
imagen_portafolio = os.path.join(base_dir, 'Flujo', 'output', f'Portafolio_{fecha_hora}.png')

# PARÁMETROS DEL MODELO
MONTO_APUESTA = 1000       # Monto de la Apuesta
RISK_AVERSION = 1.0     # λ de Markowitz para TU portafolio óptimo (ajústalo si quieres)


# =====================================================
# 2. FUNCIONES AUXILIARES
# =====================================================

def cargar_apuestas(path, sheet_name=0):
    
    # Lee el Excel de entrada.
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {path}")

    df = pd.read_excel(path, sheet_name=sheet_name)

    # Chequeo de columnas mínimas
    cols_min = {"Descripcion", "Cuota"}
    if not cols_min.issubset(df.columns):
        raise ValueError(
            f"Faltan columnas mínimas en el Excel. Debe tener al menos: {cols_min}"
        )

    # Crear/ajustar ProbReal
    if "ProbReal" not in df.columns:
        df["ProbReal"] = 1.0 / df["Cuota"]
    else:
        mask_nan = df["ProbReal"].isna()
        df.loc[mask_nan, "ProbReal"] = 1.0 / df.loc[mask_nan, "Cuota"]

    if (df["ProbReal"] < 0).any() or (df["ProbReal"] > 1).any():
        raise ValueError("ProbReal debe estar entre 0 y 1 (ej. 0.60, 0.45, etc.).")

    return df


def calcular_ev_y_var(df):
    # Calcula la ganancia neta, valor esperado y la varianza
    # GananciaNeta = Cuota - 1

    df = df.copy()
    df["GananciaNeta"] = df["Cuota"] - 1.0

    p = df["ProbReal"].values
    g = df["GananciaNeta"].values

    # EV = p*g - (1 - p)*1
    EV = p * g - (1 - p)
    df["EV"] = EV

    # Var = p (g - EV)^2 + (1-p) (-1 - EV)^2
    var = p * (g - EV) ** 2 + (1 - p) * ((-1 - EV) ** 2)
    df["Varianza"] = var

    return df


def construir_covarianza(df):
    # Se asume la independencia de las apuestas
    var = df["Varianza"].values
    cov = np.diag(var)
    return cov


def optimizar_portafolio(mu, cov, risk_aversion=1.0):
    # Se aplica el modelo de Markowitz
   
    n = len(mu)
    mu = np.array(mu, dtype=float)
    cov = np.array(cov, dtype=float)

    def objective(w):
        exp_ret = np.dot(mu, w)
        var = w @ cov @ w
        return -(exp_ret - risk_aversion * var)

    constraints = ({
        "type": "eq",
        "fun": lambda w: np.sum(w) - 1.0
    })
    bounds = tuple((0.0, 1.0) for _ in range(n))
    w0 = np.ones(n) / n

    result = minimize(objective, w0, method="SLSQP",
                      bounds=bounds, constraints=constraints)

    if not result.success:
        raise RuntimeError(f"Optimización no convergió: {result.message}")

    w_opt = result.x
    exp_ret_opt = float(np.dot(mu, w_opt))
    var_opt = float(w_opt @ cov @ w_opt)

    return w_opt, exp_ret_opt, var_opt


def generar_nube_portafolios(mu, cov, n_port=3000, seed=42):
    
    #Genera el portafolio
    rng = np.random.default_rng(seed)
    n_assets = len(mu)
    mu = np.array(mu, dtype=float)
    cov = np.array(cov, dtype=float)

    sigmas = []
    rets = []
    sharpes = []

    for _ in range(n_port):
        w = rng.random(n_assets)
        w /= w.sum()

        port_ret = float(mu @ w)
        port_var = float(w @ cov @ w)
        port_sigma = np.sqrt(port_var)

        sigmas.append(port_sigma)
        rets.append(port_ret)
        if port_sigma > 0:
            sharpes.append(port_ret / port_sigma)
        else:
            sharpes.append(0.0)

    return np.array(sigmas), np.array(rets), np.array(sharpes)


def graficar_portafolio(mu, cov, ev_opt, var_opt, image_path):
    # Grafica el portafolio

    sigmas, rets, sharpes = generar_nube_portafolios(mu, cov)

    sigma_opt = np.sqrt(var_opt)

    plt.figure(figsize=(8, 6))

    # Nube de portafolios
    sc = plt.scatter(sigmas, rets, c=sharpes, s=10, alpha=0.7)
    plt.colorbar(sc, label="Índice retorno/riesgo")

    # Punto del portafolio óptimo
    plt.scatter(sigma_opt, ev_opt, marker='*', s=250,
                edgecolor='black', linewidths=1.2)

    plt.xlabel("Riesgo (desviación estándar)")
    plt.ylabel("Rentabilidad esperada (EV)")
    plt.title("Portafolio de apuestas - Modelo de Markowitz")

    plt.grid(True, linestyle='--', alpha=0.3)

    # Guardar y cerrar
    plt.tight_layout()
    plt.savefig(image_path, dpi=300)
    plt.close()


# =====================================================
# 3. PIPELINE PRINCIPAL
# =====================================================

def main():
    # Crear carpeta de salida si no existe
    out_dir = os.path.dirname(resultado_variacion)
    os.makedirs(out_dir, exist_ok=True)

    # 1) Cargar apuestas
    df = cargar_apuestas(archivo_entrada)

    # 2) Calcular EV y varianza
    df_calc = calcular_ev_y_var(df)

    # 3) Filtrar solo EV > 0 (si las tienes); si no hay, usar todas
    df_valor = df_calc[df_calc["EV"] > 0].reset_index(drop=True)
    if df_valor.empty:
        print("No hay apuestas con EV > 0; se usa todo el conjunto para mínima varianza.")
        df_valor = df_calc.reset_index(drop=True)

    # 4) Matriz de covarianza y vector de EV
    cov = construir_covarianza(df_valor)
    mu = df_valor["EV"].values

    # 5) Optimizar portafolio (Markowitz)
    w_opt, ev_opt, var_opt = optimizar_portafolio(mu, cov, RISK_AVERSION)

    # 6) Convertir a montos
    stakes = w_opt * MONTO_APUESTA
    df_valor["PesoOptimo"] = w_opt
    df_valor["MontoSugerido"] = stakes

    # 7) Guardar Excel
    with pd.ExcelWriter(resultado_variacion, engine="openpyxl") as writer:
        df_calc.to_excel(writer, sheet_name="Apuestas_EV_Var", index=False)
        df_valor.to_excel(writer, sheet_name="Portafolio_Optimo", index=False)

    # 8) Graficar y guardar PNG
    graficar_portafolio(mu, cov, ev_opt, var_opt, imagen_portafolio)

    # 9) Print de resumen en consola
    print("=== ARCHIVO DE RESULTADOS ===")
    print(resultado_variacion)
    print("\n=== IMAGEN DEL PORTAFOLIO ===")
    print(imagen_portafolio)

    print("\n=== PORTAFOLIO ÓPTIMO (MARKOWITZ) ===")
    print(df_valor[["Descripcion", "Cuota", "ProbReal", "EV",
                    "PesoOptimo", "MontoSugerido"]])

    print(f"\nRentabilidad esperada del portafolio (EV): {ev_opt:.4f}")
    print(f"Varianza del portafolio: {var_opt:.4f}")
    print(f"Desviación estándar (riesgo): {np.sqrt(var_opt):.4f}")
    print(f"Suma de pesos: {df_valor['PesoOptimo'].sum():.4f}")


if __name__ == "__main__":
    main()