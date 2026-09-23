# Guía para explicar la base de datos del TP

## 0. En una frase

Es un tablero que compara **cuánto se vendió realmente** (dato fijo, histórico) contra **cuánto se quería vender** (dato editable por el admin) y muestra un semáforo por sector y mes.

## 1. El modelo de datos (5 tablas)

Es un **modelo estrella** (típico de bases analíticas): una tabla de hechos en el centro, rodeada de tablas de dimensión.

```
              dim_tiempo                    dim_sector
          (id, fecha, mes,               (id, nombre)
           trimestre, anio)
                 │                              │
                 └──────────┐        ┌───────────┘
                            ▼        ▼
                        hecho_venta
                (fk_tiempo, fk_sector, monto_vendido)


              dim_sector
                 │
                 ▼
              objetivo
     (fk_sector, periodo, meta_venta,
      umbral_verde, umbral_amarillo)


              usuario
     (login, password_hash, rol)
```

| Tabla | Qué guarda | Quién la modifica |
|---|---|---|
| `dim_tiempo` | Un renglón por mes: fecha, mes, trimestre, año | Nadie desde la app — se carga una sola vez con `seed.sql` |
| `dim_sector` | Los 6 rubros de la cadena (Electrónica, Celulares, etc.) | Nadie desde la app — fijo |
| `hecho_venta` | **El hecho**: cuánto se vendió, por mes y por sector | **Solo lectura** desde la app, nadie la edita |
| `objetivo` | Meta de venta y umbrales del semáforo, por sector y mes | **Solo el rol admin**, desde "Gestión de objetivos" |
| `usuario` | Login, contraseña hasheada y rol de cada usuario | Nadie desde la app (se carga con el seed) |

### Por qué son tablas separadas (la pregunta que más te van a hacer)

`hecho_venta` (lo que pasó) y `objetivo` (lo que se espera) son dos tablas distintas a propósito. Si estuvieran mezcladas en una sola tabla, cada vez que el admin cargara o cambiara una meta futura correría el riesgo de tocar datos históricos de venta ya cerrados. Separarlas también refleja que tienen **ciclos de vida distintos**: `hecho_venta` se carga una vez (por seed) y nunca cambia; `objetivo` se edita todo el tiempo, sector por sector, mes a mes.

`dim_tiempo` y `dim_sector` son tablas de dimensión: evitan repetir texto (el nombre del sector, la fecha completa) en cada fila de `hecho_venta`, y son la base del modelo estrella típico de un data warehouse simple.

## 2. Las relaciones (claves foráneas)

- `hecho_venta.fk_tiempo` → `dim_tiempo.id`
- `hecho_venta.fk_sector` → `dim_sector.id`
- `objetivo.fk_sector` → `dim_sector.id`

Importante: **`hecho_venta` y `objetivo` no tienen una FK directa entre sí.** Se relacionan indirectamente por `fk_sector` (mismo sector) y por fecha (`dim_tiempo.fecha = objetivo.periodo`, mismo mes). Eso es lo que permite comparar "lo real" contra "la meta" de un mismo sector y mes sin duplicar información.

## 3. La consulta clave: el semáforo

Esta es la consulta que hace todo el trabajo pesado (está en `db.py`, función `get_semaforo`):

```sql
SELECT
    s.nombre AS sector,
    COALESCE(v.monto_vendido, 0) AS venta_real,
    o.meta_venta,
    o.umbral_verde,
    o.umbral_amarillo,
    ROUND(100.0 * COALESCE(v.monto_vendido, 0) / o.meta_venta, 1) AS porcentaje
FROM dim_sector s
JOIN objetivo o       ON o.fk_sector = s.id AND o.periodo = :periodo
LEFT JOIN dim_tiempo t ON t.fecha = :periodo
LEFT JOIN hecho_venta v ON v.fk_sector = s.id AND v.fk_tiempo = t.id
ORDER BY s.nombre
```

Explicada en criollo:
1. **Arranca desde `dim_sector`**: quiero un resultado por cada sector, exista o no venta cargada.
2. **`JOIN objetivo`**: le pego la meta de ese sector para el período pedido. Si un sector no tiene objetivo cargado para ese mes, no aparece en el resultado (por eso es `JOIN` normal, no `LEFT JOIN`).
3. **`LEFT JOIN dim_tiempo` + `LEFT JOIN hecho_venta`**: uso `LEFT JOIN` (no `JOIN`) a propósito, para que si todavía no se cargó la venta de ese mes, el sector igual aparezca con `venta_real = 0` en vez de desaparecer del resultado.
4. **`COALESCE(v.monto_vendido, 0)`**: si no hay venta cargada (venta_real es NULL por el LEFT JOIN), lo trato como 0.
5. **El cálculo del porcentaje se hace en SQL**, no en Python — es la "consulta SQL fija" que pide el enunciado, no depende de que el usuario la pueda modificar.

Después, en Python, solo clasifico el color según el porcentaje calculado:

```
🟢 verde:    porcentaje >= umbral_verde       (por defecto 100 → superó la meta)
🟡 amarillo: umbral_amarillo <= porcentaje < umbral_verde   (por defecto 90-99 → cerca)
🔴 rojo:     porcentaje < umbral_amarillo     (por defecto <90 → lejos)
```

Los umbrales **no están fijos en el código**: son columnas de `objetivo`, así que cada sector y cada mes puede tener su propio criterio de verde/amarillo/rojo (por ejemplo, Climatización puede tener una meta y umbrales distintos en verano que en invierno).

## 4. La consulta de "Gestión de objetivos"

```sql
INSERT INTO objetivo (fk_sector, periodo, meta_venta, umbral_verde, umbral_amarillo)
VALUES (:fk_sector, :periodo, :meta_venta, :umbral_verde, :umbral_amarillo)
ON CONFLICT (fk_sector, periodo)
DO UPDATE SET meta_venta = EXCLUDED.meta_venta, ...
```

Es un **"upsert"**: si no existía un objetivo para ese sector+período lo crea (`INSERT`), y si ya existía lo actualiza (`UPDATE`) en la misma instrucción, gracias a la restricción `UNIQUE (fk_sector, periodo)` que tiene la tabla `objetivo`. Esta es la única operación de escritura de toda la app, y nunca toca `hecho_venta`.

## 5. Roles y seguridad

- `usuario.password_hash` guarda la contraseña **hasheada con bcrypt**, nunca en texto plano — ni siquiera yo como admin de la base puedo "ver" la contraseña de un usuario, solo comparar si una contraseña ingresada genera el mismo hash.
- El rol (`admin` / `lector`) decide, **a nivel de aplicación**, si se muestra la pestaña "Gestión de objetivos". No usamos roles nativos de PostgreSQL (como `GRANT`/`REVOKE` por usuario de base) para esto — se mantuvo simple: un solo usuario de conexión a la base (`tablero_app`) y el control de permisos vive en la tabla `usuario` + la lógica de la app.
- Todas las consultas usan **parámetros** (`:periodo`, `:fk_sector`, etc.) en vez de concatenar texto — así se evita la inyección SQL.

## 6. Preguntas que te puede hacer el profe (y cómo responderlas)

**¿Por qué no guardaste todo en una sola tabla?**
Porque mezclar hechos (inmutables) con objetivos (editables) rompe la integridad histórica y no permite tener distintos umbrales por período de forma prolija.

**¿Cómo evitás que un usuario "lector" edite objetivos?**
El control está en la app: se lee `usuario.rol` al hacer login y solo si es `admin` se muestra el formulario. La conexión a la base usa un único usuario técnico (`tablero_app`), el control de "quién puede hacer qué" es de negocio, no de PostgreSQL.

**¿Qué pasa si un sector no tiene venta cargada para un mes?**
Gracias al `LEFT JOIN`, igual aparece en el semáforo con venta real = $0 (en vez de no aparecer), siempre que tenga un objetivo cargado para ese período.

**¿Por qué `hecho_venta` y `objetivo` no tienen FK directa?**
Porque no representan lo mismo: se vinculan por sector + mes (fecha), no por una relación 1 a 1. Es una relación "conceptual", resuelta en el `JOIN` de la consulta, no en el modelo físico.

**¿Cómo se guardan las contraseñas?**
Con hash bcrypt (con "salt" incluido), nunca en texto plano.

## 7. Qué SÍ necesitás saber de la app (lo mínimo)

- Se conecta a PostgreSQL con SQLAlchemy, usando credenciales guardadas fuera del código (`.env` local / "secrets" en Streamlit Cloud) — nunca hardcodeadas.
- Las consultas usan parámetros, no concatenación de strings (evita inyección SQL).
- El login compara el hash de la contraseña ingresada contra `usuario.password_hash`.

No hace falta que sepas explicar Streamlit línea por línea (widgets, session_state, etc.) — eso es capa de presentación, no es el foco de una materia de Base de Datos.
