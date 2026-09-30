# El "canon" (modelo canónico) aplicado a este TP

## ¿Qué es?

En tu propio parcial (B.1) dibujaste el proceso completo de un Data Warehouse así:

```
Fuentes de datos → ETL (extracción, transformación, carga) → Data Warehouse → Data Marts
```

El **modelo canónico** vive justo en el medio, dentro del ETL: es la representación de las entidades del negocio **unificada y neutral**, antes de convertirla en el modelo físico (estrella). Es el "lenguaje común" que usás para ponerte de acuerdo en qué es cada cosa, sin todavía preocuparte por tablas, claves foráneas ni tipos de dato de SQL.

Tu propio ejemplo del parcial lo explica perfecto: si el sistema de ventas le dice "cliente" a alguien y marketing le dice "contacto" a la misma persona, el modelo canónico es donde decidís que ambos son, en realidad, el mismo concepto: **Cliente**. Unifica antes de construir.

En proyectos reales, esto es crítico porque hay **muchas fuentes distintas** (sistema de ventas, planillas de stock, otro sistema de RRHH). En tu TP hay una sola fuente (`seed.sql`), así que el modelo canónico es más simple de armar — pero igual hay que mostrarlo, porque es el paso conceptual antes del modelo físico.

## El modelo canónico de tu proyecto

Son las mismas entidades que ya tenés, pero descriptas en términos de negocio (sin FK, sin tipos SQL, sin nombres técnicos):

| Entidad | Atributos (en términos de negocio) |
|---|---|
| **Sector** | Nombre de la categoría de productos |
| **Período** | Fecha, Mes, Trimestre, Año |
| **Venta** | Sector al que pertenece, Período en que ocurrió, Monto vendido |
| **Objetivo** | Sector, Período, Meta de venta esperada, Umbral para considerar "cumplida", Umbral para considerar "cerca" |
| **Usuario** | Nombre de usuario, Rol (quién puede ver / quién puede editar objetivos) |

Esto es intencionalmente **independiente de la implementación**: no dice "tabla", no dice "clave primaria", no dice "VARCHAR" ni "NUMERIC". Es el acuerdo conceptual de qué información existe y cómo se relaciona, en el idioma del negocio (una cadena de tecnología que quiere saber si cada categoría está cumpliendo sus metas de venta).

## Cómo pasa del canon al modelo físico (estrella)

Este es el paso que ya hicimos en `LOGICA.md`: cada entidad canónica se convierte en una tabla física, agregándole ahora sí las claves primarias/foráneas y tipos de dato:

```
Modelo canónico          →     Modelo físico (estrella)
─────────────────              ──────────────────────
Sector                    →     dim_sector (id, nombre)
Período                   →     dim_tiempo (id, fecha, mes, trimestre, anio)
Venta                     →     hecho_venta (fk_tiempo, fk_sector, monto_vendido)
Objetivo                  →     objetivo (fk_sector, periodo, meta_venta, umbral_verde, umbral_amarillo)
Usuario                   →     usuario (login, password_hash, rol)
```

`Sector` y `Período` se convierten en **dimensiones** (`dim_`) porque son las "perspectivas" desde las que se analiza la venta. `Venta` se convierte en el **hecho** (`hecho_venta`) porque es la medida numérica que se quiere analizar. `Objetivo` queda aparte porque, aunque también se relaciona con Sector y Período, no es un hecho histórico sino una regla de negocio editable (por eso tampoco es "hecho", va como tabla de control).

## Si te piden entregarlo como documento/diagrama

Lo más simple: un diagrama de 5 cajas (una por entidad canónica) con sus atributos en texto simple, sin flechas de FK — o directamente la tabla de arriba. Si querés, te lo armo como diagrama para pegar en el informe.
