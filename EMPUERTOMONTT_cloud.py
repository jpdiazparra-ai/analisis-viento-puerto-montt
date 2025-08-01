import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import streamlit as st
import os
import matplotlib.dates as mdates

# Configurar la app
st.set_page_config(page_title="Análisis de Viento", layout="wide")
st.title("🌬️ Análisis Interactivo de Datos de Viento")

# Cargar archivo
archivo = os.path.join(os.getcwd(), "PuertoMontt.xlsx")
df = pd.read_excel(archivo)

# Normalizar columnas
df.columns = df.columns.astype(str).str.strip()
df = df.convert_dtypes()

# Detectar columnas relevantes
col_fecha = df.columns[0]
col_viento = [col for col in df.columns if "Wind Speed" in col or col.strip() == "Y"][0]
col_rafaga = [col for col in df.columns if "Wind Gust" in col or col.strip() == "Z"][0]
col_direccion = [col for col in df.columns if "Wind Direction" in col or col.strip() == "AA"][0]

df = df.rename(columns={
    col_fecha: "FechaHora",
    col_viento: "Viento_kmh",
    col_rafaga: "Rafaga_kmh",
    col_direccion: "Direccion_grados"
})
df["FechaHora"] = pd.to_datetime(df["FechaHora"])

# ========= FILTRO FLEXIBLE DE FECHAS =========
st.sidebar.header("📅 Filtro de Fechas")
opcion_filtro = st.sidebar.radio(
    "Selecciona el tipo de filtro",
    ["Rango de fechas", "Día específico", "Mes completo", "Año completo"]
)

fecha_min = df['FechaHora'].min().date()
fecha_max = df['FechaHora'].max().date()

if opcion_filtro == "Rango de fechas":
    fecha_inicio, fecha_fin = st.sidebar.date_input("Selecciona el rango", [fecha_min, fecha_max], min_value=fecha_min, max_value=fecha_max)
    df_filtrado = df[(df['FechaHora'].dt.date >= fecha_inicio) & (df['FechaHora'].dt.date <= fecha_fin)]
elif opcion_filtro == "Día específico":
    dia = st.sidebar.date_input("Selecciona un día", fecha_min, min_value=fecha_min, max_value=fecha_max)
    df_filtrado = df[df['FechaHora'].dt.date == dia]
elif opcion_filtro == "Mes completo":
    años = sorted(df['FechaHora'].dt.year.unique())
    año_sel = st.sidebar.selectbox("Selecciona el año", años)
    meses = sorted(df[df['FechaHora'].dt.year == año_sel]['FechaHora'].dt.month.unique())
    mes_sel = st.sidebar.selectbox("Selecciona el mes", meses)
    df_filtrado = df[(df['FechaHora'].dt.year == año_sel) & (df['FechaHora'].dt.month == mes_sel)]
elif opcion_filtro == "Año completo":
    años = sorted(df['FechaHora'].dt.year.unique())
    año_sel = st.sidebar.selectbox("Selecciona el año", años)
    df_filtrado = df[df['FechaHora'].dt.year == año_sel]

# ========= VALIDACIÓN =========
if df_filtrado.empty:
    st.warning("⚠️ No hay datos para el filtro seleccionado.")
    st.stop()
else:
    st.success(f"✅ {len(df_filtrado)} registros encontrados.")

# ========= LIMPIEZA DE COLUMNAS OBJETO/ERROR =========
for col in df_filtrado.columns:
    if df_filtrado[col].apply(lambda x: isinstance(x, bytes)).any():
        df_filtrado = df_filtrado.drop(columns=[col])

# ========= TABLA =========
st.subheader("📋 Datos Filtrados")
st.write(df_filtrado)  # Más seguro que st.dataframe

# ========= GRÁFICO DE LÍNEA =========
st.subheader("📈 Velocidad y Ráfagas de Viento")
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(df_filtrado["FechaHora"], df_filtrado["Viento_kmh"], label="Viento (km/h)")
ax.plot(df_filtrado["FechaHora"], df_filtrado["Rafaga_kmh"], label="Ráfaga (km/h)", alpha=0.7)
ax.set_xlabel("Fecha y Hora")
ax.set_ylabel("Velocidad (km/h)")
ax.legend()
ax.grid(True)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
plt.xticks(rotation=45)
st.pyplot(fig)

# ========= ROSAS DEL VIENTO =========
st.subheader("🌪️ Rosa del Viento y Ráfagas")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**🌪️ Velocidad promedio del Viento**")
    fig1 = plt.figure(figsize=(5, 5))
    ax1 = WindroseAxes.from_ax(fig=fig1)
    ax1.bar(df_filtrado["Direccion_grados"], df_filtrado["Viento_kmh"], normed=True, opening=0.8, edgecolor='white', cmap=plt.cm.viridis)
    ax1.set_legend(title="Viento (km/h)")
    st.pyplot(fig1)

with col2:
    st.markdown("**💨 Ráfagas máximas del Viento**")
    fig2 = plt.figure(figsize=(5, 5))
    ax2 = WindroseAxes.from_ax(fig=fig2)
    ax2.bar(df_filtrado["Direccion_grados"], df_filtrado["Rafaga_kmh"], normed=True, opening=0.8, edgecolor='white', cmap=plt.cm.plasma)
    ax2.set_legend(title="Ráfaga (km/h)")
    st.pyplot(fig2)