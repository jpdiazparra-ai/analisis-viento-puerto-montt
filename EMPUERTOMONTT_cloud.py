import pandas as pd
import streamlit as st
import os
import matplotlib.dates as mdates
import plotly.express as px
import matplotlib.pyplot as plt
from windrose import WindroseAxes

st.set_page_config(page_title="Análisis de Viento", layout="wide")
st.title("🌬️ Análisis Interactivo de Datos de Viento")

# === Carga automática del archivo desde el repositorio ===
archivo = os.path.join(os.path.dirname(__file__), "PuertoMontt.xlsx")

if os.path.exists(archivo):
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

    # ======= NUEVOS KPIs SOLICITADOS =======
    v_util_min = 3    # km/h
    v_util_max = 25   # km/h

    velocidad_modal = df_filtrado["Viento_kmh"].mode()[0]
    direccion_dominante = df_filtrado["Direccion_grados"].mode()[0]
    porcentaje_tiempo_viento_util = df_filtrado[
        (df_filtrado["Viento_kmh"] >= v_util_min) & (df_filtrado["Viento_kmh"] <= v_util_max)
    ].shape[0] / len(df_filtrado) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Velocidad Modal", f"{velocidad_modal:.2f} km/h")
    col2.metric("Dirección Dominante", f"{direccion_dominante:.0f}°")
    col3.metric("Tiempo con Viento Útil (%)", f"{porcentaje_tiempo_viento_util:.2f} %")

    # ========= KPIs EXISTENTES =========
    col4, col5, col6 = st.columns(3)
    col4.metric("Velocidad Promedio", f"{df_filtrado['Viento_kmh'].mean():.2f} km/h")
    col5.metric("Ráfaga Máxima", f"{df_filtrado['Rafaga_kmh'].max():.2f} km/h")
    col6.metric("Registros", f"{len(df_filtrado)}")

    # ========= Gráfico interactivo de líneas con Plotly =========
    fig_line = px.line(df_filtrado, x="FechaHora", y=["Viento_kmh", "Rafaga_kmh"],
                       labels={"value": "Velocidad (km/h)", "FechaHora": "Fecha y Hora", "variable": "Tipo de Velocidad"},
                       title="Velocidad y Ráfagas de Viento")
    st.plotly_chart(fig_line, use_container_width=True)

    # ========= ROSAS DEL VIENTO con matplotlib =========
    st.subheader("🌪️ Rosa del Viento y Ráfagas")
    col7, col8 = st.columns(2)

    with col7:
        st.markdown("**🌪️ Velocidad promedio del Viento**")
        fig1 = plt.figure(figsize=(5, 5))
        ax1 = WindroseAxes.from_ax(fig=fig1)
        ax1.bar(df_filtrado["Direccion_grados"], df_filtrado["Viento_kmh"], normed=True, opening=0.8, edgecolor='white', cmap=plt.cm.viridis)
        ax1.set_legend(title="Viento (km/h)")
        st.pyplot(fig1)

    with col8:
        st.markdown("**💨 Ráfagas máximas del Viento**")
        fig2 = plt.figure(figsize=(5, 5))
        ax2 = WindroseAxes.from_ax(fig=fig2)
        ax2.bar(df_filtrado["Direccion_grados"], df_filtrado["Rafaga_kmh"], normed=True, opening=0.8, edgecolor='white', cmap=plt.cm.plasma)
        ax2.set_legend(title="Ráfaga (km/h)")
        st.pyplot(fig2)

else:
    st.error("❌ El archivo 'PuertoMontt.xlsx' no se encuentra en el directorio del script. Sube el archivo a tu repositorio o revisa la ruta.")
<<<<<<< HEAD
=======


>>>>>>> 2deb2595993be4e7fb2d8676c19b55299ddd66f7
