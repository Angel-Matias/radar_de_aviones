from flask import Flask, render_template_string
import requests
import math
import folium
from threading import Thread
import time
import os

app = Flask(__name__)
mapa_html = ""

# 📍 Tu ubicación real
mi_lat = 20.511011381992425
mi_lon = -100.8166114928057
mi_alt = 1757  # metros sobre el nivel del mar

# 📡 Zona de búsqueda
zona = {
    "lamin": 20.3,
    "lamax": 20.7,
    "lomin": -101.1,
    "lomax": -100.5
}

# 📐 Cálculo del ángulo de elevación
def elevacion(lat1, lon1, alt1, lat2, lon2, alt2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distancia_horizontal = R * c
    delta_alt = alt2 - alt1
    angulo = math.degrees(math.atan2(delta_alt, distancia_horizontal))
    return angulo

# 🔍 Consulta vuelos cercanos desde OpenSky
def consultar_vuelos():
    url = f"https://opensky-network.org/api/states/all?lamin={zona['lamin']}&lamax={zona['lamax']}&lomin={zona['lomin']}&lomax={zona['lomax']}"
    try:
        response = requests.get(url)
        data = response.json()
        if 'states' in data and isinstance(data['states'], list):
            return data['states']
    except:
        pass
    return []

# 🗺️ Genera mapa interactivo en memoria
def generar_mapa(aviones_visibles):
    mapa = folium.Map(location=[mi_lat, mi_lon], zoom_start=10)
    folium.Marker([mi_lat, mi_lon], tooltip="Tu ubicación", icon=folium.Icon(color='blue')).add_to(mapa)

    for lat, lon, callsign, angulo in aviones_visibles:
        folium.Marker(
            [lat, lon],
            tooltip=f"{callsign} ({round(angulo)}°)",
            icon=folium.Icon(color='red')
        ).add_to(mapa)

    return mapa._repr_html_()

# 🔁 Actualiza el radar cada 30 segundos
def actualizar_radar():
    global mapa_html
    while True:
        vuelos = consultar_vuelos()
        visibles = []
        for vuelo in vuelos:
            callsign = vuelo[1]
            lat = vuelo[6]
            lon = vuelo[5]
            alt = vuelo[7]
            if None in [lat, lon, alt]:
                continue
            angulo = elevacion(mi_lat, mi_lon, mi_alt, lat, lon, alt)
            if angulo >= 45:
                visibles.append((lat, lon, callsign.strip(), angulo))
        mapa_html = generar_mapa(visibles)
        time.sleep(30)

# 🌐 Página web
@app.route("/")
def mostrar_mapa():
    return render_template_string("""
        <html>
        <head><title>Radar Virtual</title></head>
        <body>
            <h2>✈️ Radar Virtual - Actualizado cada 30 segundos</h2>
            {{ mapa|safe }}
        </body>
        </html>
    """, mapa=mapa_html)

# 🚀 Inicia radar y servidor web
if __name__ == "__main__":
    Thread(target=actualizar_radar, daemon=True).start()
    port = int(os.environ.get("PORT", 20000))  # Compatible con Render y local
    app.run(host="0.0.0.0", port=port)
