# Código de Python para obtener la rentabilidad en las apuestas
# Hecho por Eduardo Huamani

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize

# =====================================
# 1. RUTAS Y PARÁMETROS
# =====================================

base_dir = os.getcwd()

archivo_entrada = os.path.join(base_dir, 'Flujo', 'input', 'Datos_apuesta.xlsx')  # Datos de entrada 

archivo_salida = os.path.join(base_dir, 'Flujo', 'output', 'Resultados_portafolio_optimo.xlsx')
archivo_png = os.path.join(base_dir, 'Flujo', 'output', 'Frontera_Eficiente_Portafolio.png')

MONTO = 100   # monto total a invertir
N_RANDOM = 10000  # número de portafolios aleatorios para la nube


# =====================================
# 2. LECTURA DEL EXCEL
# =====================================

df = pd.read_excel(archivo_entrada)

if 'Descripcion' not in df.columns or 'Cuota' not in df.columns:
    raise ValueError("El Excel debe tener columnas: 'Descripcion' y 'Cuota'.")

nombres_apuestas = df['Descripcion'].astype(str)
odds = df['Cuota'].astype(float).to_numpy()

# Rentabilidad = Cuota - 1  (único escenario: si se acierta)
mu = odds - 1  # (n_apuestas,)

n_assets = len(mu)
if n_assets < 2:
    raise ValueError("Se requieren al menos 2 apuestas para formar un portafolio.")

# Matriz de riesgo artificial (diagonal) para poder construir portafolios
base_vol = np.maximum(0.10, 0.5 * np.abs(mu))  # vol mínima del 10%
Sigma = np.diag(base_vol**2)

# =====================================
# 3. FUNCIONES DE PORTAFOLIO Y OPTIMIZACIÓN
# =====================================

def portafolio_stats(weights, mu, Sigma):
    """Devuelve rendimiento esperado y desviación estándar (riesgo)."""
    w = np.array(weights)
    exp_ret = np.dot(w, mu)
    var = np.dot(w.T, np.dot(Sigma, w))
    std = np.sqrt(var)
    return exp_ret, std


def objetivo_min_var(weights, mu, Sigma, target_return):
    """Minimiza la varianza penalizando alejarse del retorno objetivo."""
    exp_ret, std = portafolio_stats(weights, mu, Sigma)
    penalty = 1000.0 * (exp_ret - target_return)**2
    return std**2 + penalty


def optimizar_para_retorno(target_return, mu, Sigma):
    """Portafolio de mínima varianza para un retorno objetivo."""
    n = len(mu)
    w0 = np.ones(n) / n

    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    bounds = tuple((0, 1) for _ in range(n))

    res = minimize(objetivo_min_var,
                   w0,
                   args=(mu, Sigma, target_return),
                   method='SLSQP',
                   bounds=bounds,
                   constraints=cons)
    return res


def portafolio_min_var(mu, Sigma):
    # Portafolio conservador
    n = len(mu)
    w0 = np.ones(n) / n
    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    bounds = tuple((0, 1) for _ in range(n))
    res = minimize(lambda w: portafolio_stats(w, mu, Sigma)[1]**2,
                   w0,
                   method='SLSQP',
                   bounds=bounds,
                   constraints=cons)
    return res


def portafolio_max_return(mu, Sigma):
    # Portafolio agresivo
    n = len(mu)
    w0 = np.ones(n) / n
    cons = ({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    bounds = tuple((0, 1) for _ in range(n))
    res = minimize(lambda w: -np.dot(w, mu),
                   w0,
                   method='SLSQP',
                   bounds=bounds,
                   constraints=cons)
    return res


# =====================================
# 4. PORTAFOLIOS ALEATORIOS (NUBE)
# =====================================

rand_returns = []
rand_risks = []
rand_sharpes = []

for _ in range(N_RANDOM):
    w = np.random.rand(n_assets)
    w /= w.sum()
    r, s = portafolio_stats(w, mu, Sigma)
    rand_returns.append(r)
    rand_risks.append(s)
    rand_sharpes.append(r / s)

rand_returns = np.array(rand_returns)
rand_risks = np.array(rand_risks)
rand_sharpes = np.array(rand_sharpes)


# =====================================
# 5. FRONTERA EFICIENTE (LÍNEA)
# =====================================

min_ret = float(mu.min())
max_ret = float(mu.max())

if np.isclose(min_ret, max_ret):
    raise ValueError("Todas las rentabilidades son iguales. "
                     "No se puede construir una frontera eficiente.")

target_returns = np.linspace(min_ret, max_ret, 50)

frontier_returns = []
frontier_risks = []
frontier_weights = []

for r_target in target_returns:
    r = optimizar_para_retorno(r_target, mu, Sigma)
    if r.success:
        w = r.x
        exp_ret, std = portafolio_stats(w, mu, Sigma)
        frontier_returns.append(exp_ret)
        frontier_risks.append(std)
        frontier_weights.append(w)

frontier_returns = np.array(frontier_returns)
frontier_risks = np.array(frontier_risks)
frontier_weights = np.array(frontier_weights)

if len(frontier_returns) == 0:
    raise RuntimeError("No se pudo trazar la frontera eficiente.")


# =====================================
# 6. TRES TIPOS DE INVERSIONISTA
# =====================================

# 6.1 Conservador: mínima varianza
res_cons = portafolio_min_var(mu, Sigma)
w_cons = res_cons.x
ret_cons, risk_cons = portafolio_stats(w_cons, mu, Sigma)
montos_cons = w_cons * MONTO

# 6.2 Moderado: máximo Sharpe sobre la frontera
sharpe_frontier = frontier_returns / frontier_risks
idx_best = np.argmax(sharpe_frontier)
w_mod = frontier_weights[idx_best]
ret_mod = frontier_returns[idx_best]
risk_mod = frontier_risks[idx_best]
montos_mod = w_mod * MONTO

# 6.3 Agresivo: máximo rendimiento esperado
res_agr = portafolio_max_return(mu, Sigma)
w_agr = res_agr.x
ret_agr, risk_agr = portafolio_stats(w_agr, mu, Sigma)
montos_agr = w_agr * MONTO


# =====================================
# 7. PRINT DE RESULTADOS
# =====================================

def imprimir_portafolio(nombre_tipo, w, montos, ret, risk):
    print(f"\n===== PORTAFOLIO {nombre_tipo} =====")
    for n, wi, mi in zip(nombres_apuestas, w, montos):
        print(f"Apuesta: {n:25s}  Peso: {wi:6.3f}  Monto: {mi:8.2f}")
    print(f"Rendimiento esperado: {ret*100:6.2f}%")
    ganancia = MONTO * ret
    print(f"Ganancia esperada: {ganancia:.2f}")

imprimir_portafolio("CONSERVADOR", w_cons, montos_cons, ret_cons, risk_cons)
imprimir_portafolio("MODERADO", w_mod, montos_mod, ret_mod, risk_mod)
imprimir_portafolio("AGRESIVO", w_agr, montos_agr, ret_agr, risk_agr)

print(f"\nMONTO total utilizado: {MONTO:.2f}")


# =====================================
# 8. EXPORTAR A EXCEL
# =====================================

df_tipos = pd.DataFrame({
    'Apuesta': nombres_apuestas,
    'Cuota': odds,
    'RentabilidadEstimada': mu,
    'Peso_Conservador': w_cons,
    'Monto_Conservador': montos_cons,
    'Peso_Moderado': w_mod,
    'Monto_Moderado': montos_mod,
    'Peso_Agresivo': w_agr,
    'Monto_Agresivo': montos_agr
})

df_resumen_tipos = pd.DataFrame({
    'Tipo': ['Conservador', 'Moderado_Sharpe', 'Agresivo'],
    'Rendimiento': [ret_cons, ret_mod, ret_agr],
    'Riesgo': [risk_cons, risk_mod, risk_agr],
    'Sharpe': [ret_cons/risk_cons, ret_mod/risk_mod, ret_agr/risk_agr],
    'MONTO': [MONTO, MONTO, MONTO]
})

with pd.ExcelWriter(archivo_salida, engine='openpyxl') as writer:
    df_tipos.to_excel(writer, index=False, sheet_name='Portafolios_Tipos')
    df_resumen_tipos.to_excel(writer, index=False, sheet_name='Resumen_Tipos')

print(f"\nArchivo Excel exportado en:\n{archivo_salida}")


# =====================================
# 9. GRÁFICA PNG (NUBE + TIPOS)
# =====================================

plt.figure(figsize=(8, 6))

# Nube de portafolios aleatorios
sc = plt.scatter(rand_risks, rand_returns, c=rand_sharpes,
                 cmap='viridis', alpha=0.8, label='Portafolios aleatorios')

# Tres portafolios tipo (estrellas)
plt.scatter(risk_cons, ret_cons, marker='*', s=200, label='Conservador')
plt.scatter(risk_mod, ret_mod, marker='*', s=200, label='Moderado')
plt.scatter(risk_agr, ret_agr, marker='*', s=200, label='Agresivo')

plt.xlabel('Volatilidad')
plt.ylabel('Rendimiento esperado (%)')
plt.title('Frontera Eficiente de las Apuestas')
plt.grid(True)
plt.colorbar(sc, label='Ratio de Sharpe')
plt.legend()

plt.savefig(archivo_png, dpi=300, bbox_inches='tight')
plt.close()

print(f"Imagen PNG guardada en:\n{archivo_png}")
