import streamlit as st
import pandas as pd
import datetime
import joblib
import folium
from streamlit_folium import st_folium
import googlemaps
import polyline
from shapely.geometry import LineString, Point

# ------------------------
# CONFIGURACIÓN GOOGLE MAPS
# ------------------------
gmaps = googlemaps.Client(key="AIzaSyDhbzBCT19qhDcFRUJreD2vCunhhSkwiBw")

# ------------------------
# CONFIGURACIÓN BÁSICA
# ------------------------
st.set_page_config(
    page_title="⛽ Predicción Gasolineras",
    page_icon="⛽",
    layout="wide"
)

st.title("⛽ Predicción de Gasolineras Baratas en Ruta")
st.markdown("Encuentra la gasolinera más barata en tu trayecto con predicción de precios futuros.")

# ------------------------
# CARGA DE DATOS Y MODELO
# ------------------------
@st.cache_resource
def load_model():
    return joblib.load("./models/modelo_gasolineras.pkl")

@st.cache_data
def load_data():
    usecols = ["Rotulo","Latitud","Longitud","Horario","Nombre_Carburante","Fecha"]
    return pd.read_csv("https://media.githubusercontent.com/media/Ebracara/Desafio_Reto2/refs/heads/main/data/gasolineras_precios_limpio.csv", usecols=usecols)

model = load_model()
df = load_data()

# ------------------------
# FUNCIONES AUXILIARES
# ------------------------
def highlight_min(s):
    is_min = s == s.min()
    return ['background-color: green' if v else '' for v in is_min]

def obtener_ruta(origen, destino):
    directions = gmaps.directions(origen, destino, mode="driving")
    polyline_points = directions[0]["overview_polyline"]["points"]
    coords = polyline.decode(polyline_points)
    return coords

def gasolineras_cercanas(df_gas, ruta_coords, radio_km=10):
    ruta_linea = LineString([(lon, lat) for lat, lon in ruta_coords])
    buffer = ruta_linea.buffer(radio_km/111)  # 1° ≈ 111 km

    seleccionadas = []
    for _, row in df_gas.iterrows():
        p = Point(row["Longitud"], row["Latitud"])
        if buffer.contains(p):
            seleccionadas.append(row)
    return pd.DataFrame(seleccionadas)

def desviacion_ruta(origen, destino, parada):
    ruta_ori = gmaps.directions(origen, destino, mode="driving")
    dist_ori = sum(leg["distance"]["value"] for leg in ruta_ori[0]["legs"])

    ruta_mod = gmaps.directions(origen, destino, mode="driving", waypoints=[parada])
    dist_mod = sum(leg["distance"]["value"] for leg in ruta_mod[0]["legs"])

    return dist_mod - dist_ori

# ------------------------
# SIDEBAR DE CONFIGURACIÓN
# ------------------------
st.sidebar.header("⚙️ Configuración de búsqueda")

col1, col2 = st.sidebar.columns(2)
with col1:
    origen = st.text_input("📍 Dirección de **origen**", "Bilbao, España")
with col2:
    destino = st.text_input("🏁 Dirección de **destino**", "San Sebastián, España")

radio_km = st.sidebar.slider("📏 Radio de búsqueda alrededor de la ruta (km)", 1, 30, 10)

carburantes = df["Nombre_Carburante"].unique()
tipo_carburante = st.sidebar.selectbox("⛽ Tipo de carburante", sorted(carburantes))

fecha_pred = st.sidebar.date_input(
    "📅 Fecha de predicción",
    min_value=datetime.date.today() + datetime.timedelta(days=1),
    value=datetime.date.today() + datetime.timedelta(days=1)
)

predict_btn = st.sidebar.button("🔮 Predecir ruta")

# ------------------------
# PROCESAMIENTO
# ------------------------
if predict_btn:
    st.subheader("🚀 Resultados de la predicción")
    st.info(f"Calculando ruta y gasolineras cercanas entre **{origen} → {destino}**")

    df_future = (
        df[df["Nombre_Carburante"] == tipo_carburante]
        .drop_duplicates(subset=["Rotulo","Latitud","Longitud","Nombre_Carburante","Horario"])
        .copy()
    )

    fecha_dt = pd.to_datetime(fecha_pred)
    df_future["Año"] = fecha_dt.year
    df_future["Mes"] = fecha_dt.month
    df_future["Dia"] = fecha_dt.day
    df_future["DiaSemana"] = fecha_dt.dayofweek

    X_pred = df_future[['Latitud','Longitud','Nombre_Carburante','Año','Mes','Dia','DiaSemana']]
    df_future["Precio_Predicho"] = model.predict(X_pred)

    coords = obtener_ruta(origen, destino)
    df_ruta = gasolineras_cercanas(df_future, coords, radio_km)

    if df_ruta.empty:
        st.warning("⚠️ No se encontraron gasolineras en ese rango de la ruta.")
    else:
        precio_min = df_ruta["Precio_Predicho"].min()
        candidatas = df_ruta[df_ruta["Precio_Predicho"] == precio_min].copy()

        candidatas["Desviacion_m"] = candidatas.apply(
            lambda r: desviacion_ruta(origen, destino, f"{r['Latitud']},{r['Longitud']}"),
            axis=1
        )

        mejor_gasolinera = candidatas.sort_values("Desviacion_m").iloc[0]

        st.session_state["df_resultados"] = df_ruta.sort_values("Precio_Predicho")
        st.session_state["mejor_gasolinera"] = mejor_gasolinera
        st.session_state["coords"] = coords

# ------------------------
# RESULTADOS
# ------------------------
if "df_resultados" in st.session_state:
    df_resultados = st.session_state["df_resultados"]
    mejor_gasolinera = st.session_state["mejor_gasolinera"]
    coords = st.session_state["coords"]

    st.subheader("📊 Gasolineras y precios predichos")
    st.dataframe(
        df_resultados[["Rotulo","Latitud","Longitud","Horario","Precio_Predicho"]]
        .style.apply(highlight_min, subset=["Precio_Predicho"])
    )

    if st.checkbox("🗺️ Mostrar mapa con gasolineras y ruta"):
        m = folium.Map(location=coords[0], zoom_start=9)

        # Ruta original en azul
        folium.PolyLine(coords, color="blue", weight=5, opacity=0.6).add_to(m)

        # 🔹 Gasolineras candidatas como puntitos pequeños
        for _, row in df_resultados.iterrows():
            folium.CircleMarker(
                location=[row["Latitud"], row["Longitud"]],
                radius=2,  # marcador muy pequeño
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.7,
                popup=f"{row['Rotulo']}<br>{row['Horario']}<br>{row['Precio_Predicho']:.2f} €",
                tooltip=row['Rotulo']
            ).add_to(m)

        # 🔹 Gasolinera elegida en rojo con estrella
        folium.Marker(
            location=[mejor_gasolinera["Latitud"], mejor_gasolinera["Longitud"]],
            popup=f"⛽ GASOLINERA ELEGIDA<br>{mejor_gasolinera['Rotulo']}<br>{mejor_gasolinera['Precio_Predicho']:.2f} €",
            tooltip="Gasolinera más barata y cercana",
            icon=folium.Icon(color="red", icon="star", prefix="fa")
        ).add_to(m)

        # Ruta modificada en rojo
        parada = f"{mejor_gasolinera['Latitud']},{mejor_gasolinera['Longitud']}"
        ruta_mod = gmaps.directions(origen, destino, mode="driving", waypoints=[parada])
        coords_mod = polyline.decode(ruta_mod[0]["overview_polyline"]["points"])

        folium.PolyLine(coords_mod, color="red", weight=4, opacity=0.7).add_to(m)

        st_folium(m, width=800, height=600)
else:
    st.markdown("👉 Selecciona los parámetros en la barra lateral y pulsa **Predecir ruta** para empezar.")
