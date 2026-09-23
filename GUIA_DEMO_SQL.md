# Guía para demostrar la base de datos (paso a paso, copiar y pegar)

Todo esto lo corrés en **Neon → tu proyecto → "SQL Editor"** (en el navegador, no necesitás instalar nada).
Son todas consultas `SELECT` (solo lectura): podés correrlas las veces que quieras, nunca rompen ni cambian nada.

Antes de empezar, un mini-diccionario de lo que vas a escribir:
- `SELECT columnas FROM tabla` → "traeme estas columnas de esta tabla"
- `JOIN otra_tabla ON condición` → "combiná esta tabla con otra, usando esta condición para saber qué fila corresponde con qué fila"
- `WHERE condición` → "pero solo las filas que cumplen esto"
- `ORDER BY columna` → "ordenado por esta columna"
- `LIMIT 10` → "mostrame nomás las primeras 10"

---

## Paso 1 — Mostrar los sectores (tabla de dimensión)

> "Esta es una de las tablas de dimensión: los 6 rubros de la cadena."

```sql
SELECT * FROM dim_sector;
```

## Paso 2 — Mostrar los períodos de tiempo

> "Esta es la otra tabla de dimensión: un renglón por cada mes que tenemos cargado."

```sql
SELECT * FROM dim_tiempo ORDER BY fecha;
```

## Paso 3 — Mostrar el hecho "crudo" (sin nombres, solo IDs)

> "Esta es la tabla de hechos: acá vive el dato real de venta. Fijate que solo tiene números de ID, no nombres — por eso hacen falta las tablas de dimensión."

```sql
SELECT * FROM hecho_venta LIMIT 10;
```

## Paso 4 — El mismo hecho, pero legible (con JOIN)

> "Si le pego las dos tablas de dimensión con un JOIN, ya veo el sector y la fecha en texto, no solo números."

```sql
SELECT t.fecha, s.nombre AS sector, v.monto_vendido
FROM hecho_venta v
JOIN dim_tiempo t ON t.id = v.fk_tiempo
JOIN dim_sector s ON s.id = v.fk_sector
ORDER BY t.fecha
LIMIT 10;
```

## Paso 5 — Mostrar los objetivos (metas y umbrales)

> "Esta es la tabla que sí se puede editar, pero solo desde la pantalla de admin de la app, nunca a mano en la base. Acá está la meta y los umbrales de cada sector por mes."

```sql
SELECT s.nombre AS sector, o.periodo, o.meta_venta, o.umbral_verde, o.umbral_amarillo
FROM objetivo o
JOIN dim_sector s ON s.id = o.fk_sector
ORDER BY o.periodo DESC, s.nombre
LIMIT 12;
```

## Paso 6 — La consulta del semáforo (la más importante)

> "Esta es la consulta que usa la app para armar el semáforo. Compara la venta real contra la meta, y calcula el porcentaje directamente en SQL — no en el código de la aplicación."

Podés cambiar la fecha `'2025-09-01'` por cualquier mes que tengas cargado (mirá el resultado del Paso 2 para ver las fechas disponibles):

```sql
SELECT
    s.nombre AS sector,
    COALESCE(v.monto_vendido, 0) AS venta_real,
    o.meta_venta,
    o.umbral_verde,
    o.umbral_amarillo,
    ROUND(100.0 * COALESCE(v.monto_vendido, 0) / o.meta_venta, 1) AS porcentaje_cumplido
FROM dim_sector s
JOIN objetivo o ON o.fk_sector = s.id AND o.periodo = '2025-09-01'
LEFT JOIN dim_tiempo t ON t.fecha = '2025-09-01'
LEFT JOIN hecho_venta v ON v.fk_sector = s.id AND v.fk_tiempo = t.id
ORDER BY s.nombre;
```

> "Este número de `porcentaje_cumplido` es exactamente el que la app compara contra `umbral_verde` y `umbral_amarillo` para pintar cada fila de verde, amarillo o rojo."

Después de correr esto, andá a la app desplegada, elegí el mismo mes en "Período a evaluar", y mostrale al profe que los números coinciden — eso demuestra que el semáforo no es "magia" de la aplicación, sino el resultado directo de esta consulta.

## Paso 7 — Mostrar los usuarios (sin exponer contraseñas)

> "Acá se guardan los usuarios y su rol. La contraseña nunca se ve en texto plano, solo un hash — ni yo puedo leerla."

```sql
SELECT login, rol FROM usuario;
```

Si quieren ver que efectivamente la contraseña está "encriptada":

```sql
SELECT login, password_hash FROM usuario;
```

(vas a ver algo tipo `$2b$12$...` en vez de `admin123` — ese es el hash bcrypt).

---

## Para demostrar que `objetivo` es editable pero `hecho_venta` no

**No lo hagas con SQL directo** (podrías equivocarte en vivo) — mejor mostralo con la app:
1. Entrá como `admin`, andá a "Gestión de objetivos".
2. Cambiá una meta y guardá.
3. Volvé a correr la consulta del **Paso 5** en Neon → vas a ver el número actualizado al instante.

Eso prueba que la única forma de modificar datos desde la aplicación es a través de esa pantalla, y que impacta directo en la tabla `objetivo` — nunca en `hecho_venta`.

## Si el profe pregunta algo y no sabés la respuesta al toque

Está bien decir: "esa parte específica no la tengo memorizada, pero está documentada en `LOGICA.md`" — mostrar que entendés el diseño general vale más que memorizar cada línea de SQL de memoria.
