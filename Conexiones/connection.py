import os
from dotenv import load_dotenv
import psycopg2
from datetime import datetime

base_dir = os.getcwd()
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

#MODELO DE FINANZAS
# Parámetros a modificar

finanzas_anlo_modelo = '2025'  
finanzas_mes_modelo = '08'  

FINANZAS_ALBAMAR_CAPITAL = f'https://www.dropbox.com/scl/fo/tpurhryy8hyh1yqwctb3u/h/Albamar%20Capital/Comit%C3%A9%20{finanzas_anlo_modelo}%20-%20{finanzas_mes_modelo}%20-%20{{dia}}/Colonial?rlkey=deqi3gc4bk0jh54m65oeiwg4l&dl=1'
FINANZAS_FARO = f'https://www.dropbox.com/scl/fo/tpurhryy8hyh1yqwctb3u/h/Faro%20Capital/Comit%C3%A9%20{finanzas_anlo_modelo}%20-%20{finanzas_mes_modelo}%20-%20{{dia}}?rlkey=deqi3gc4bk0jh54m65oeiwg4l&dl=1'
FINANZAS_FIBRA = f'https://www.dropbox.com/scl/fo/tpurhryy8hyh1yqwctb3u/h/FIBRA/Comit%C3%A9%20{finanzas_anlo_modelo}%20-%20{finanzas_mes_modelo}%20-%20{{dia}}?rlkey=deqi3gc4bk0jh54m65oeiwg4l&dl=1'
FINANZAS_CUKIC = f'https://www.dropbox.com/scl/fo/tpurhryy8hyh1yqwctb3u/h/Cukic/Patriotas/Comit%C3%A9%20{finanzas_anlo_modelo}%20-%20{finanzas_mes_modelo}%20-%20{{dia}}?rlkey=deqi3gc4bk0jh54m65oeiwg4l&dl=1'
FINANZAS_BENAVIDES = f'https://www.dropbox.com/scl/fo/tpurhryy8hyh1yqwctb3u/h/Benavides/Comit%C3%A9%20{finanzas_anlo_modelo}%20-%20{finanzas_mes_modelo}%20-%20{{dia}}?rlkey=deqi3gc4bk0jh54m65oeiwg4l&dl=1'


