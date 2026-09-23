-- Esquema del Tablero de Ventas (BDA) - Grupo 3
-- Ejecutar una sola vez contra la base "tablero_ventas"

CREATE TABLE dim_tiempo (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL UNIQUE,
    mes SMALLINT NOT NULL,
    trimestre SMALLINT NOT NULL,
    anio SMALLINT NOT NULL
);

CREATE TABLE dim_sector (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE hecho_venta (
    id SERIAL PRIMARY KEY,
    fk_tiempo INTEGER NOT NULL REFERENCES dim_tiempo(id),
    fk_sector INTEGER NOT NULL REFERENCES dim_sector(id),
    monto_vendido NUMERIC(14,2) NOT NULL
);

CREATE TABLE objetivo (
    id SERIAL PRIMARY KEY,
    fk_sector INTEGER NOT NULL REFERENCES dim_sector(id),
    periodo DATE NOT NULL,
    meta_venta NUMERIC(14,2) NOT NULL,
    umbral_verde NUMERIC(5,2) NOT NULL DEFAULT 100.00,
    umbral_amarillo NUMERIC(5,2) NOT NULL DEFAULT 90.00,
    UNIQUE (fk_sector, periodo)
);

CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    login VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('admin', 'lector'))
);

CREATE INDEX idx_hecho_venta_tiempo ON hecho_venta(fk_tiempo);
CREATE INDEX idx_hecho_venta_sector ON hecho_venta(fk_sector);
CREATE INDEX idx_objetivo_sector_periodo ON objetivo(fk_sector, periodo);
