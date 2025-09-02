import os
import io
import pandas as pd
import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import requests

st.set_page_config(page_title="Análisis de Viento", layout="wide")
st.title("🌬️ Análisis Interactivo de Datos de Viento")

# =========================
# URL Google Sheets (CSV)
# =========================
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ650aaHgB69g6U_srEpAU_aibt0LomYaOqwxt-TfGAQjtU6LYd-K_RYmcAIZ0AnUhR4z8dI-GYaLs3/pub?gid=92001156&single=true&output=csv"

@st.cache_data(show_spinner=True, ttl=600)
def load_from_google_csv(url: str) -> pd.DataFrame:
    import io, requests, pandas as pd
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    # sep=None + engine='python' -> autodetecta delimitador (; o ,)
    df_csv = pd.read_csv(io.BytesIO(r.content), sep=None, engine="python")
    return _normalize_dataframe(df_csv)

def _normalize_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df.columns = df.columns.astype(str).str.strip()

    # Mapeo fijo a tu archivo
    mapping = {
        "Fecha": "FechaHora",
        "Wind Speed(km/h)": "Viento_kmh",
        "Wind Gust(km/h)": "Rafaga_kmh",
        "Wind Direction(º)": "Direccion_grados",
    }
    # Renombrar
    present = {k: v for k, v in mapping.items() if k in df.columns}
    df = df.rename(columns=present)

    requeridas = ["FechaHora", "Viento_kmh", "Rafaga_kmh", "Direccion_grados"]
    faltantes = [c for c in requeridas if c not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}. Columnas disponibles: {list(df.columns)}")

    # --- Parse de fecha
    df["FechaHora"] = pd.to_datetime(df["FechaHora"], errors="coerce")

    # --- Normalización numérica robusta para CSV con coma decimal ---
    def to_num_robusto(s):
        # convierte a string, reemplaza coma decimal por punto y elimina caracteres no numéricos comunes
        s = s.astype(str).str.replace("\u00a0", "", regex=False)  # NBSP
        s = s.str.replace(",", ".", regex=False)
        s = s.str.replace(r"[^0-9\.\-]", "", regex=True)
        return pd.to_numeric(s, errors="coerce")

    df["Viento_kmh"]  = to_num_robusto(df["Viento_kmh"])
    df["Rafaga_kmh"]  = to_num_robusto(df["Rafaga_kmh"])
    df["Direccion_grados"] = pd.to_numeric(df["Direccion_grados"], errors="coerce")

    # Ordenar y limpiar
    df = df.dropna(subset=["FechaHora"]).sort_values("FechaHora").reset_index(drop=True)
    return df

@st.cache_data(show_spinner=True, ttl=600)
def load_from_google_csv(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    df_csv = pd.read_csv(io.BytesIO(r.content))
    return _normalize_dataframe(df_csv)

@st.cache_data(show_spinner=True, ttl=600)
def load_from_local_excel(path: str) -> pd.DataFrame:
    df_xlsx = pd.read_excel(path)
    return _normalize_dataframe(df_xlsx)
# =========================
# Controles (sidebar)
# =========================
st.sidebar.header("⚙️ Controles")
if st.sidebar.button("🔄 Actualizar datos (limpiar caché)", use_container_width=True):
    # borra caché de @st.cache_data
    st.cache_data.clear()
    # marca de recarga para mostrar hora en UI
    import pandas as pd
    st.session_state["_refresh_ts"] = pd.Timestamp.now().isoformat()
    st.sidebar.success("Caché borrada. Recargando…")
    # re-ejecuta la app
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# =========================
# Fuente de datos (solo URL fija)
# =========================
try:
    df = load_from_google_csv(URL_CSV)
except Exception as e:
    st.error(f"❌ Error cargando datos desde Google Sheets:\n\n{e}")
    st.stop()


# =========================
# Filtros de fecha
# =========================
st.sidebar.header("📅 Filtro de Fechas")
opcion_filtro = st.sidebar.radio(
    "Selecciona el tipo de filtro",
    ["Rango de fechas", "Día específico", "Mes completo", "Año completo"]
)

fecha_min = df['FechaHora'].min().date()
fecha_max = df['FechaHora'].max().date()

if opcion_filtro == "Rango de fechas":
    fecha_inicio, fecha_fin = st.sidebar.date_input(
        "Selecciona el rango", [fecha_min, fecha_max],
        min_value=fecha_min, max_value=fecha_max
    )
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
else:  # Año completo
    años = sorted(df['FechaHora'].dt.year.unique())
    año_sel = st.sidebar.selectbox("Selecciona el año", años)
    df_filtrado = df[df['FechaHora'].dt.year == año_sel]

if df_filtrado.empty:
    st.warning("⚠️ No hay datos para el filtro seleccionado.")
    st.stop()
else:
    st.success(f"✅ {len(df_filtrado)} registros encontrados.")

# =========================
# Limpieza específica por métrica
# =========================
df_speed   = df_filtrado.dropna(subset=["Viento_kmh"])
df_gust    = df_filtrado.dropna(subset=["Rafaga_kmh"])
df_dir     = df_filtrado.dropna(subset=["Direccion_grados"])
df_rose_v  = df_filtrado.dropna(subset=["Direccion_grados", "Viento_kmh"])
df_rose_g  = df_filtrado.dropna(subset=["Direccion_grados", "Rafaga_kmh"])

# =========================
# KPIs seguros
# =========================
v_util_min = 3    # km/h
v_util_max = 25   # km/h

def safe_mode(series):
    m = series.dropna().mode()
    return m.iloc[0] if len(m) else float("nan")

def safe_mean(series):
    s = series.dropna()
    return float(s.mean()) if len(s) else float("nan")

velocidad_modal = safe_mode(df_speed["Viento_kmh"]) if not df_speed.empty else float("nan")
direccion_dominante = safe_mode(df_dir["Direccion_grados"]) if not df_dir.empty else float("nan")

den = df_speed.shape[0] if df_speed.shape[0] > 0 else 1
porcentaje_tiempo_viento_util = (
    df_speed[(df_speed["Viento_kmh"] >= v_util_min) & (df_speed["Viento_kmh"] <= v_util_max)].shape[0] / den * 100
)

col1, col2, col3 = st.columns(3)
col1.metric("Velocidad Modal", f"{velocidad_modal:.2f} km/h" if pd.notna(velocidad_modal) else "—")
col2.metric("Dirección Dominante", f"{direccion_dominante:.0f}°" if pd.notna(direccion_dominante) else "—")
col3.metric("Tiempo con Viento Útil (%)", f"{porcentaje_tiempo_viento_util:.2f} %")

col4, col5, col6 = st.columns(3)
mean_speed = safe_mean(df_speed["Viento_kmh"])
max_gust   = float(df_gust["Rafaga_kmh"].max()) if not df_gust.empty else float("nan")
col4.metric("Velocidad Promedio", f"{mean_speed:.2f} km/h" if pd.notna(mean_speed) else "—")
col5.metric("Ráfaga Máxima", f"{max_gust:.2f} km/h" if pd.notna(max_gust) else "—")
col6.metric("Registros", f"{len(df_filtrado)}")

# =========================
# Serie de tiempo (Plotly)
# =========================
fig_line = px.line(
    df_filtrado, x="FechaHora", y=["Viento_kmh", "Rafaga_kmh"],
    labels={"value": "Velocidad (km/h)", "FechaHora": "Fecha y Hora", "variable": "Tipo de Velocidad"},
    title="Velocidad y Ráfagas de Viento"
)
st.plotly_chart(fig_line, use_container_width=True)

# =========================
# Rosas del Viento
# =========================
st.subheader("🌪️ Rosa del Viento y Ráfagas")
col7, col8 = st.columns(2)

with col7:
    st.markdown("**🌪️ Velocidad promedio del Viento**")
    if len(df_rose_v) >= 5:  # pide datos suficientes y sin NaN
        fig1 = plt.figure(figsize=(5, 5))
        ax1 = WindroseAxes.from_ax(fig=fig1)
        ax1.bar(
            df_rose_v["Direccion_grados"].to_numpy(),
            df_rose_v["Viento_kmh"].to_numpy(),
            normed=True, opening=0.8, edgecolor='white', cmap=plt.cm.viridis
        )
        ax1.set_legend(title="Viento (km/h)")
        st.pyplot(fig1)
    else:
        st.info("No hay suficientes datos válidos (sin NaN) para la rosa de **velocidad**.")

with col8:
    st.markdown("**💨 Ráfagas máximas del Viento**")
    if len(df_rose_g) >= 5:
        fig2 = plt.figure(figsize=(5, 5))
        ax2 = WindroseAxes.from_ax(fig=fig2)
        ax2.bar(
            df_rose_g["Direccion_grados"].to_numpy(),
            df_rose_g["Rafaga_kmh"].to_numpy(),
            normed=True, opening=0.8, edgecolor='white', cmap=plt.cm.plasma
        )
        ax2.set_legend(title="Ráfaga (km/h)")
        st.pyplot(fig2)
    else:
        st.info("No hay suficientes datos válidos (sin NaN) para la rosa de **ráfagas**.")
