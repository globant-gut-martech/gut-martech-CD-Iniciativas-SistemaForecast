import json
import os

# Ruta al archivo JSON de la cuenta de servicio ponerla de acuerdo a donde se tenga guardada la informacion de la cuenta
ruta_json = "C:/Users/diegofabian.sanchez/Downloads/ProyectoForecast/secrets/mi-clave-gcp.json"

# Leer el contenido del archivo JSON
with open(ruta_json, "r") as f:
    data = f.read()

# Escapar comillas, backslashes y saltos de línea
data_escaped = data.replace("\\", "\\\\").replace('"', '\\"').replace('\n', '\\n')

# Crear la carpeta .streamlit si no existe
os.makedirs(".streamlit", exist_ok=True)

# Ruta final del archivo secrets.toml
ruta_toml = os.path.join(".streamlit", "secrets.toml")

# Escribir el archivo secrets.toml
with open(ruta_toml, "w", encoding="utf-8") as f:
    f.write(f'GCP_SERVICE_ACCOUNT = """\n{data_escaped}\n"""')

print(f"✅ Archivo secrets.toml creado exitosamente en: {ruta_toml}")