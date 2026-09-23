import streamlit as st
import plotly.express as px

import db
from auth import verify_login

st.set_page_config(page_title="Tablero de Ventas", layout="wide")

ESTADO_EMOJI = {"verde": "🟢", "amarillo": "🟡", "rojo": "🔴"}
ESTADO_ORDEN = {"rojo": 0, "amarillo": 1, "verde": 2, "sin datos": 3}

if "user" not in st.session_state:
    st.session_state.user = None


def login_view():
    st.title("Tablero de Ventas - Login")
    with st.form("login_form"):
        login = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")
    if submitted:
        user = verify_login(login, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")


def mensaje_estado(row) -> str:
    if row["porcentaje"] is None:
        return "Sin objetivo cargado para este período."
    diferencia = row["porcentaje"] - 100
    if diferencia >= 0:
        return f"{diferencia:.1f}% por encima de la meta"
    return f"{abs(diferencia):.1f}% por debajo de la meta"


def semaforo_view(fk_sectores):
    periodos_df = db.get_periodos()
    periodo_sel = st.selectbox(
        "Período a evaluar",
        options=periodos_df["fecha"].sort_values(ascending=False),
        format_func=lambda d: d.strftime("%m/%Y"),
    )

    semaforo_df = db.get_semaforo(periodo_sel)
    if fk_sectores:
        semaforo_df = semaforo_df[semaforo_df["fk_sector"].isin(fk_sectores)]
    semaforo_df["orden"] = semaforo_df["estado"].map(ESTADO_ORDEN)
    semaforo_df = semaforo_df.sort_values("orden")

    st.subheader("Semáforo de cumplimiento de metas")
    cols = st.columns(len(semaforo_df)) if len(semaforo_df) else []
    for col, (_, row) in zip(cols, semaforo_df.iterrows()):
        with col:
            with st.container(border=True):
                st.markdown(f"### {ESTADO_EMOJI.get(row['estado'], '⚪')} {row['sector']}")
                st.metric(
                    label="Cumplimiento de meta",
                    value=f"{row['porcentaje']}%" if row["porcentaje"] is not None else "s/d",
                )
                st.caption(mensaje_estado(row))
                st.caption(f"Real: ${row['venta_real']:,.0f}  ·  Meta: ${row['meta_venta']:,.0f}")

    if len(semaforo_df):
        fig = px.bar(
            semaforo_df,
            x="sector",
            y=["venta_real", "meta_venta"],
            barmode="group",
            title="Venta real vs. meta por sector",
            labels={"value": "Monto ($)", "variable": ""},
        )
        st.plotly_chart(fig, use_container_width=True)


def tablero_view():
    sectores_df = db.get_sectores()

    st.sidebar.subheader("Filtros")
    sectores_sel = st.sidebar.multiselect(
        "Sector", options=sectores_df["nombre"], default=list(sectores_df["nombre"])
    )
    fk_sectores = sectores_df[sectores_df["nombre"].isin(sectores_sel)]["id"].tolist()

    semaforo_view(fk_sectores)

    with st.expander("Ver evolución histórica de ventas"):
        periodos_df = db.get_periodos()
        fecha_min, fecha_max = periodos_df["fecha"].min(), periodos_df["fecha"].max()
        fecha_desde, fecha_hasta = st.slider(
            "Rango de fechas",
            min_value=fecha_min,
            max_value=fecha_max,
            value=(fecha_min, fecha_max),
            format="MM/YYYY",
        )
        ventas_df = db.get_ventas(fk_sectores=fk_sectores, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
        por_periodo = ventas_df.groupby(["fecha", "sector"], as_index=False)["monto_vendido"].sum()
        fig = px.line(
            por_periodo, x="fecha", y="monto_vendido", color="sector", title="Ventas por período"
        )
        st.plotly_chart(fig, use_container_width=True)


def gestion_objetivos_view():
    st.header("Gestión de objetivos (admin)")
    sectores_df = db.get_sectores()
    periodos_df = db.get_periodos()

    with st.form("objetivo_form"):
        sector_nombre = st.selectbox("Sector", options=sectores_df["nombre"])
        periodo = st.selectbox(
            "Período", options=periodos_df["fecha"].sort_values(ascending=False),
            format_func=lambda d: d.strftime("%m/%Y"),
        )
        meta_venta = st.number_input("Meta de venta ($)", min_value=0.0, step=10000.0)
        umbral_verde = st.number_input(
            "Umbral verde (%) - venta superó la meta", min_value=0.0, max_value=200.0, value=100.0
        )
        umbral_amarillo = st.number_input(
            "Umbral amarillo (%) - venta cerca de la meta", min_value=0.0, max_value=200.0, value=90.0
        )
        submitted = st.form_submit_button("Guardar objetivo")

    if submitted:
        fk_sector = int(sectores_df[sectores_df["nombre"] == sector_nombre]["id"].iloc[0])
        db.upsert_objetivo(fk_sector, periodo, meta_venta, umbral_verde, umbral_amarillo)
        st.success("Objetivo guardado correctamente.")
        st.rerun()

    st.subheader("Objetivos existentes")
    st.dataframe(db.get_objetivos(), use_container_width=True)


def main_view():
    st.sidebar.write(f"Usuario: **{st.session_state.user['login']}** ({st.session_state.user['rol']})")
    if st.sidebar.button("Cerrar sesión"):
        st.session_state.user = None
        st.rerun()

    st.title("Tablero de Ventas por Sector")

    if st.session_state.user["rol"] == "admin":
        tab1, tab2 = st.tabs(["Tablero", "Gestión de objetivos"])
        with tab1:
            tablero_view()
        with tab2:
            gestion_objetivos_view()
    else:
        tablero_view()


if st.session_state.user is None:
    login_view()
else:
    main_view()
