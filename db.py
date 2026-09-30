import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

_engine = None


def _config(key: str) -> str:
    """Lee la config de st.secrets (Streamlit Cloud) o de variables de entorno/.env (local)."""
    try:
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ[key]


def get_engine():
    global _engine
    if _engine is None:
        url = (
            f"postgresql+psycopg2://{_config('DB_USER')}:{_config('DB_PASSWORD')}"
            f"@{_config('DB_HOST')}:{_config('DB_PORT')}/{_config('DB_NAME')}"
        )
        _engine = create_engine(url)
    return _engine


def get_usuario(login: str):
    query = text("SELECT login, password_hash, rol FROM usuario WHERE login = :login")
    with get_engine().connect() as conn:
        row = conn.execute(query, {"login": login}).mappings().fetchone()
    return dict(row) if row else None


def get_sectores() -> pd.DataFrame:
    return pd.read_sql("SELECT id, nombre FROM dim_sector ORDER BY nombre", get_engine())


def get_periodos() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT DISTINCT periodo AS fecha FROM objetivo ORDER BY fecha", get_engine()
    )


def get_semaforo(periodo) -> pd.DataFrame:
    """Venta real (calculada, fija) vs. meta para un periodo dado, por sector."""
    query = text(
        """
        SELECT
            s.id AS sector_id,
            s.nombre AS sector,
            COALESCE(v.monto_vendido, 0) AS venta_real,
            o.meta_venta,
            o.umbral_verde,
            o.umbral_amarillo,
            CASE WHEN o.meta_venta > 0
                 THEN ROUND(100.0 * COALESCE(v.monto_vendido, 0) / o.meta_venta, 1)
                 ELSE NULL
            END AS porcentaje
        FROM dim_sector s
        JOIN objetivo o ON o.fk_sector = s.id AND o.periodo = :periodo
        LEFT JOIN dim_tiempo t ON t.fecha = :periodo
        LEFT JOIN hecho_venta v ON v.fk_sector = s.id AND v.fk_tiempo = t.id
        ORDER BY s.nombre
        """
    )
    with get_engine().connect() as conn:
        df = pd.read_sql(query, conn, params={"periodo": periodo})

    def estado(row):
        if row["porcentaje"] is None:
            return "sin datos"
        if row["porcentaje"] >= row["umbral_verde"]:
            return "verde"
        if row["porcentaje"] >= row["umbral_amarillo"]:
            return "amarillo"
        return "rojo"

    df["estado"] = df.apply(estado, axis=1)
    return df


def upsert_objetivo(sector_id, periodo, meta_venta, umbral_verde, umbral_amarillo):
    query = text(
        """
        INSERT INTO objetivo (fk_sector, periodo, meta_venta, umbral_verde, umbral_amarillo)
        VALUES (:sector_id, :periodo, :meta_venta, :umbral_verde, :umbral_amarillo)
        ON CONFLICT (fk_sector, periodo)
        DO UPDATE SET
            meta_venta = EXCLUDED.meta_venta,
            umbral_verde = EXCLUDED.umbral_verde,
            umbral_amarillo = EXCLUDED.umbral_amarillo
        """
    )
    with get_engine().begin() as conn:
        conn.execute(
            query,
            {
                "sector_id": sector_id,
                "periodo": periodo,
                "meta_venta": meta_venta,
                "umbral_verde": umbral_verde,
                "umbral_amarillo": umbral_amarillo,
            },
        )


def get_objetivos() -> pd.DataFrame:
    query = """
        SELECT o.id, s.nombre AS sector, o.fk_sector, o.periodo,
               o.meta_venta, o.umbral_verde, o.umbral_amarillo
        FROM objetivo o
        JOIN dim_sector s ON s.id = o.fk_sector
        ORDER BY o.periodo DESC, s.nombre
    """
    return pd.read_sql(query, get_engine())
