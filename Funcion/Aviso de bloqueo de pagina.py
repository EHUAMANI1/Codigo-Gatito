import requests

url = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01271PM/csv/2003-01-01/2025-01-01/ing"

response = requests.get(url)

print("STATUS CODE:", response.status_code)
print("CONTENT-TYPE:", response.headers.get("Content-Type"))
print("PREVIEW (primeros 300 caracteres):")
print(response.text[:300])