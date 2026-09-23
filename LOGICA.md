# Lógica del Tablero de Ventas (para explicar el TP)

## 1. El modelo de datos (5 tablas)

Es un modelo tipo "estrella": una tabla de hechos rodeada de tablas de dimensión.

| Tabla | Qué guarda | Quién la toca |
|---|---|---|
| `dim_tiempo` | Un renglón por mes (fecha, mes, trimestre, año) | Nadie desde la app — se carga una vez con `seed.sql` |
| `dim_sector` | Los 6 rubros de la cadena (Electrónica, Celulares, etc.) | Nadie desde la app — fijo |
| `hecho_venta` | **El hecho**: cuánto se vendió, por mes y por sector | **Solo lectura**, nadie la edita desde la app |
| `objetivo` | La meta de venta y los umbrales del semáforo, por sector y mes | **Solo el admin**, desde "Gestión de objetivos" |
| `usuario` | Login, contraseña (hasheada) y rol de cada usuario | Nadie desde la app (se carga con el seed) |

**Idea clave para explicar:** separamos "lo que pasó" (`hecho_venta`, un dato histórico e inmutable) de "lo que se espera" (`objetivo`, un dato de gestión que el admin puede ajustar). Por eso son dos tablas distintas y no una sola: si mezcláramos meta y venta real en la misma tabla, cada vez que el admin cambiara una meta futura correríamos el riesgo de pisar datos históricos de venta.

## 2. Cómo se relacionan (claves foráneas)

```
dim_tiempo (id) ──┐
                   ├──< hecho_venta (fk_tiempo, fk_sector, monto_vendido)
dim_sector (id) ───┘

dim_sector (id) ──< objetivo (fk_sector, periodo, meta_venta, umbral_verde, umbral_amarillo)
```

`hecho_venta` y `objetivo` se conectan entre sí por `fk_sector` + el mes (`fk_tiempo.fecha` = `objetivo.periodo`), no por una clave directa. Eso permite comparar "lo real" contra "la meta" del mismo sector y mes.

## 3. Cómo se calcula el semáforo

Para un sector y un período determinado:

```
porcentaje = (venta_real / meta_venta) * 100

🟢 verde:    porcentaje >= umbral_verde      (por defecto 100 → superó la meta)
🟡 amarillo: umbral_amarillo <= porcentaje < umbral_verde   (por defecto 90-99 → cerca)
🔴 rojo:     porcentaje < umbral_amarillo    (por defecto <90 → lejos)
```

Los umbrales (`umbral_verde`, `umbral_amarillo`) **no están hardcodeados en el código** — son columnas de la tabla `objetivo`, configurables por sector y por período desde la pantalla de admin. Eso es lo que pide el enunciado ("el único dato modificable desde la UI es la meta/objetivo") y de paso te da flexibilidad: un sector estacional como Climatización puede tener una meta distinta en verano que en invierno.

## 4. Roles y seguridad

- La tabla `usuario` guarda `password_hash` (con bcrypt), nunca la contraseña en texto plano.
- El login (`auth.py`) compara la contraseña ingresada contra ese hash.
- Según el rol (`admin`/`lector`) guardado en `usuario`, la app (`app.py`) muestra o esconde la pestaña "Gestión de objetivos". Es un control a nivel de aplicación, no de PostgreSQL (no usamos roles nativos de Postgres para esto, para mantenerlo simple).

## 5. Mapa rápido: pantalla → consulta (en `db.py`)

- **Semáforo:** `get_semaforo(periodo)` — hace el `JOIN` entre `dim_sector`, `objetivo` y `hecho_venta` para un mes, y calcula el porcentaje en SQL.
- **Evolución histórica:** `get_ventas(...)` — trae todas las ventas filtradas por sector/fecha para graficar la serie de tiempo.
- **Gestión de objetivos:** `upsert_objetivo(...)` — hace `INSERT ... ON CONFLICT ... DO UPDATE` sobre `objetivo` (nunca toca `hecho_venta`).
