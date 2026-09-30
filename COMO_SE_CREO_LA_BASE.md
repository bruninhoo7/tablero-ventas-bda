# Dónde y cómo se creó la base de datos

## Dónde vive (2 copias idénticas)

| | Local (tu PC) | Nube (Neon) |
|---|---|---|
| **Para qué** | Desarrollar y probar antes de subir cambios | La que usa la app pública que ven tus compañeros |
| **Motor** | PostgreSQL 16, instalado como servicio de Windows | PostgreSQL gestionado por [Neon](https://console.neon.tech) |
| **Nombre de la base** | `tablero_ventas` | `neondb` |
| **Quién la ve** | Solo vos, desde tu máquina | Cualquiera con el link de la app |
| **Administración** | pgAdmin 4 (se instala junto con Postgres) | Consola web de Neon (Tables + SQL Editor) |

Las dos tienen **exactamente las mismas 5 tablas y los mismos datos** — se crearon con los mismos dos archivos (ver abajo).

## Cómo se creó, paso a paso

1. **Instalación del motor** — se instaló PostgreSQL 16 + pgAdmin en tu PC (para poder desarrollar localmente), y se creó una cuenta en Neon (base en la nube, gratuita).
2. **Esquema** — se escribió [sql/schema.sql](sql/schema.sql): las sentencias `CREATE TABLE` de las 5 tablas (`dim_tiempo`, `dim_sector`, `hecho_venta`, `objetivo`, `usuario`), con sus claves primarias y foráneas.
3. **Datos de ejemplo** — se generaron con un script de Python (12 meses × 6 sectores, con variación entre sectores para que el semáforo diera verde, amarillo y rojo) y quedaron volcados en [sql/seed.sql](sql/seed.sql).
4. **Carga** — se ejecutó primero `schema.sql` y después `seed.sql`, contra las dos bases (local y Neon), dejando ambas con la misma estructura y los mismos datos.
5. **Credenciales** — nunca quedaron escritas en el código. Viven en `.env` (local, excluido de GitHub por `.gitignore`) y en "Secrets" de Streamlit Cloud (para la versión pública). El código (`db.py`) las lee de uno u otro lugar según dónde corra.

## Cómo reconstruirla si hiciera falta

Si algún día hay que recrear la base desde cero (por ejemplo en otra PC, o si Neon se resetea):

```sql
-- 1) Ejecutar sql/schema.sql   → crea las 5 tablas vacías
-- 2) Ejecutar sql/seed.sql     → carga los datos de ejemplo
```

Ambos archivos están en el repo de GitHub (`bruninhoo7/tablero-ventas-bda`, carpeta `sql/`), así que nunca se pierden — y si necesitás que te ayude a reconstruir o regenerar los datos, solo pedímelo.

## Documentos relacionados (ya existentes en el proyecto)

- [MODELO_CANONICO.md](MODELO_CANONICO.md) — el modelo conceptual, antes de pensar en tablas físicas
- [LOGICA.md](LOGICA.md) — el modelo físico (estrella), las relaciones y la consulta del semáforo explicada
- [GUIA_DEMO_SQL.md](GUIA_DEMO_SQL.md) — consultas listas para mostrarle a un tercero (profesor, compañero)
- [SETUP.md](SETUP.md) — cómo correr la app en una PC nueva
