import streamlit as st

import db
from auth import verify_login

st.set_page_config(page_title="Tablero de Ventas Gamer", layout="wide")

ESTADO_EMOJI = {"verde": "🟢", "amarillo": "🟡", "rojo": "🔴"}
ESTADO_ORDEN = {"rojo": 0, "amarillo": 1, "verde": 2, "sin datos": 3}

COLOR_FILA = {
    "verde": "background-color: #d4edda; color: #155724",
    "amarillo": "background-color: #fff3cd; color: #856404",
    "rojo": "background-color: #f8d7da; color: #721c24",
}

if "user" not in st.session_state:
    st.session_state.user = None


HEADER_CSS = """
<style>
.st-key-header_zone {
    background-color: #1a1f3a;
    border-radius: 8px;
}
[role="tablist"] {
    background-color: #1a1f3a;
    border-radius: 8px;
    padding: 0.25rem 0.75rem;
}
</style>
"""


def header_view():
    st.markdown(HEADER_CSS, unsafe_allow_html=True)
    with st.container(border=True, key="header_zone"):
        col_titulo, col_usuario = st.columns([3, 1])
        with col_titulo:
            st.markdown("## 🎮 Tablero de Ventas Gamer")
        with col_usuario:
            st.write(f"👤 {st.session_state.user['login']} ({st.session_state.user['rol']})")
            if st.button("Cerrar sesión"):
                st.session_state.user = None
                st.rerun()


def login_view():
    st.title("Tablero de Ventas Gamer")
    st.subheader("Login")
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


def semaforo_view():
    periodos_df = db.get_periodos()
    periodo_sel = st.selectbox(
        "Período a evaluar",
        options=periodos_df["fecha"].sort_values(ascending=False),
        format_func=lambda d: d.strftime("%m/%Y"),
    )

    semaforo_df = db.get_semaforo(periodo_sel)
    semaforo_df["orden"] = semaforo_df["estado"].map(ESTADO_ORDEN)
    semaforo_df = semaforo_df.sort_values("orden")

    tabla = semaforo_df.copy()
    tabla["Estado"] = tabla["estado"].map(ESTADO_EMOJI).fillna("⚪") + " " + tabla["estado"].str.capitalize()
    tabla["Diferencia"] = tabla.apply(mensaje_estado, axis=1)
    tabla = tabla.rename(
        columns={
            "sector": "Sector",
            "porcentaje": "% Cumplimiento",
            "venta_real": "Venta real ($)",
            "meta_venta": "Meta ($)",
        }
    )[["Sector", "Estado", "% Cumplimiento", "Diferencia", "Venta real ($)", "Meta ($)"]]

    def pintar_fila(fila):
        estilo = COLOR_FILA.get(semaforo_df.loc[fila.name, "estado"], "")
        return [estilo] * len(fila)

    st.subheader("Semáforo de cumplimiento de metas")
    st.dataframe(
        tabla.style.apply(pintar_fila, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "% Cumplimiento": st.column_config.NumberColumn(format="%.1f%%"),
            "Venta real ($)": st.column_config.NumberColumn(format="$ %,.0f"),
            "Meta ($)": st.column_config.NumberColumn(format="$ %,.0f"),
        },
    )


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
        sector_id = int(sectores_df[sectores_df["nombre"] == sector_nombre]["id"].iloc[0])
        db.upsert_objetivo(sector_id, periodo, meta_venta, umbral_verde, umbral_amarillo)
        st.success("Objetivo guardado correctamente.")
        st.rerun()

    st.subheader("Objetivos existentes")
    st.dataframe(db.get_objetivos(), use_container_width=True)


def main_view():
    header_view()

    if st.session_state.user["rol"] == "admin":
        tab1, tab2 = st.tabs(["Semáforo", "Gestión de objetivos"])
        with tab1:
            semaforo_view()
        with tab2:
            gestion_objetivos_view()
    else:
        semaforo_view()


if st.session_state.user is None:
    login_view()
else:
    main_view()
