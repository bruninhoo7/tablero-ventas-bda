# Setup del entorno - Tablero de Ventas (BDA)

## Ya instalado
- Python 3.12.10
- Entorno virtual en `venv/` con: streamlit, pandas, SQLAlchemy, psycopg2-binary, plotly, passlib[bcrypt], python-dotenv
- PostgreSQL 16 (servicio `postgresql-x64-16`, corriendo en el puerto 5432)
- pgAdmin 4 (incluido con el instalador de PostgreSQL)

## Paso pendiente (a hacer una sola vez, manualmente)
El instalador de PostgreSQL no dejó una contraseña conocida para el superusuario `postgres`.
Por seguridad, esto hay que definirlo vos mismo:

1. Abrí **pgAdmin 4** (buscalo en el menú de Windows).
2. Al conectar por primera vez al servidor "PostgreSQL 16" te va a pedir setear/ingresar la
   contraseña del usuario `postgres`. Si no la sabés, podés reinstalar solo el paso de
   configuración o restablecerla desde el "Server Configuration" de pgAdmin.
3. Una vez con acceso, abrí una "Query Tool" sobre la base `postgres` y ejecutá:

```sql
CREATE DATABASE tablero_ventas;
CREATE ROLE tablero_app WITH LOGIN PASSWORD 'elegí_una_password_segura';
GRANT ALL PRIVILEGES ON DATABASE tablero_ventas TO tablero_app;
```

4. Copiá `.env.example` a `.env` y completá `DB_PASSWORD` con la password que elegiste para
   `tablero_app`.
5. Conectate a la base `tablero_ventas` y ejecutá el contenido de [sql/schema.sql](sql/schema.sql)
   para crear las tablas del modelo de datos.
6. Cargá los datos de ejemplo con un `seed.sql` (a crear con 6-12 meses de ventas por sector).

## Cómo activar el entorno virtual (PowerShell)

```powershell
cd "tablero_ventas"
.\venv\Scripts\Activate.ps1
```

## Estado: completo y probado
- Base `tablero_ventas` con las 5 tablas, cargada con `sql/schema.sql` y `sql/seed.sql`
  (12 meses de datos, 6 sectores, con mezcla de estados verde/amarillo/rojo)
- `app.py`: login (roles admin/lector), tablero con gráficos Plotly, panel de semáforos
  y gestión de objetivos (solo admin) — probado end-to-end en el navegador
- Usuarios de prueba: `admin` / `admin123` (rol admin) y `lector` / `lector123` (rol lector)

## Cómo correr la app

```powershell
cd "tablero_ventas"
.\venv\Scripts\streamlit.exe run app.py
```

Se abre automáticamente en `http://localhost:8501`.
