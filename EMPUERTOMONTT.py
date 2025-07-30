import pandas as pd
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import streamlit as st
import os

# Configurar la app
st.set_page_config(page_title="Análisis de Viento", layout="wide")
st.title("🌬️ Análisis Interactivo de Datos de Viento")

# Cargar archivo
archivo = os.path.join(os.getcwd(), "Puertomont.xlsx")
df = pd.read_excel(archivo)

# Normalizar nombres de columnas
df.columns = df.columns.astype(str).str.strip()

# Mostrar nombres originales por inspección (para debug)
# st.write(df.columns.tolist())

# Renombrar las columnas que necesitas
col_fecha = df.columns[0]  # La primera columna es la fecha
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

# Sidebar: Filtro de fechas
st.sidebar.header("📅 Filtro de Fechas")
fecha_min = df["FechaHora"].min().date()
fecha_max = df["FechaHora"].max().date()
fecha_inicio, fecha_fin = st.sidebar.date_input("Selecciona el rango", [fecha_min, fecha_max])

# Filtro de datos por fechas
df_filtrado = df[(df["FechaHora"].dt.date >= fecha_inicio) & (df["FechaHora"].dt.date <= fecha_fin)]

# Mostrar tabla
st.info("📂 Archivo 'Puertomont.xlsx' cargado desde el directorio local.")
st.subheader("📋 Datos Filtrados")
st.dataframe(df_filtrado)

# Gráfico de líneas: Viento vs Ráfaga
st.subheader("📈 Velocidad y Ráfagas de Viento")
fig_lineas, ax1 = plt.subplots(figsize=(12, 4))
ax1.plot(df_filtrado["FechaHora"], df_filtrado["Viento_kmh"], label="Viento (km/h)", linewidth=1.5)
ax1.plot(df_filtrado["FechaHora"], df_filtrado["Rafaga_kmh"], label="Ráfaga (km/h)", alpha=0.7)
ax1.set_xlabel("Fecha y Hora")
ax1.set_ylabel("Velocidad (km/h)")
ax1.legend()
ax1.grid(True)
st.pyplot(fig_lineas)

# Rosas de Viento: lado a lado
st.subheader("🌪️ Rosa del Viento y Ráfagas")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🌪️ Velocidad promedio del Viento**")
    fig_rosa = plt.figure(figsize=(5, 5))
    ax2 = WindroseAxes.from_ax(fig=fig_rosa)
    ax2.bar(
        df_filtrado["Direccion_grados"],
        df_filtrado["Viento_kmh"],
        normed=True,
        opening=0.8,
        edgecolor='white',
        cmap=plt.cm.viridis
    )
    ax2.set_legend(title="Viento (km/h)")
    st.pyplot(fig_rosa)

with col2:
    st.markdown("**💨 Ráfagas máximas del Viento**")
    fig_rafaga = plt.figure(figsize=(5, 5))
    ax3 = WindroseAxes.from_ax(fig=fig_rafaga)
    ax3.bar(
        df_filtrado["Direccion_grados"],
        df_filtrado["Rafaga_kmh"],
        normed=True,
        opening=0.8,
        edgecolor='white',
        cmap=plt.cm.plasma
    )
    ax3.set_legend(title="Ráfaga (km/h)")
    st.pyplot(fig_rafaga)


