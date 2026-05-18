# Scaffolding: FastAPI + SQLAlchemy + JWT + PostgreSQL
### Arquitectura Multicapa · DSD-2303

<!-- Badge de CI: se actualiza automáticamente con cada push -->
<!-- ⚠️ Reemplaza TU_USUARIO y TU_REPO con tus datos de GitHub -->
[![Tests CI](https://github.com/TU_USUARIO/TU_REPO/actions/workflows/tests.yml/badge.svg)](https://github.com/TU_USUARIO/TU_REPO/actions)

> **¿Cuándo usar este enfoque?**  
> Proyectos donde se necesita alto rendimiento, validación de datos estricta con tipado explícito y una arquitectura clara separada por responsabilidades. FastAPI incluye Swagger UI y ReDoc de forma automática, sin librerías adicionales.

---

## Diferencia clave vs. Django Way

| | FastAPI Multicapa | Django Way |
|---|---|---|
| Framework | FastAPI (ASGI) | Django (WSGI) |
| ORM | SQLAlchemy 2.x | Django ORM |
| Migraciones | Alembic (explícito) | `manage.py migrate` (automático) |
| Validación | Schemas Pydantic | Serializers DRF |
| Documentación | Swagger integrado en `/docs` | drf-spectacular (librería extra) |
| Routing | `APIRouter` por módulo | `urls.py` + `DefaultRouter` |
| Auth JWT | `python-jose` + `passlib` | `djangorestframework-simplejwt` |

---

## Stack

| Componente | Versión recomendada |
|---|---|
| Python | 3.12+ |
| fastapi | 0.115+ |
| uvicorn[standard] | 0.30+ |
| sqlalchemy | 2.x |
| alembic | 1.13+ |
| psycopg2-binary | 2.9+ |
| pydantic-settings | 2.x |
| pydantic[email] | 2.x |
| python-jose[cryptography] | 3.x |
| passlib[bcrypt] | 1.7+ |

---

## Testing y CI

### Correr tests localmente

```bash
# Desde la carpeta backend/, con el entorno virtual activado
pip install pytest httpx PyJWT
pytest -v
```

### Dependencias de test (NO van en requirements.txt)

| Librería | Propósito |
|----------|-----------|
| pytest | Framework de tests |
| httpx | Requerido por TestClient de FastAPI |
| PyJWT | Para generar tokens de prueba con firma falsa |

### Estructura de tests

```
backend/
├── conftest.py          ← fixtures globales + variables de entorno para CI
└── tests/
    ├── __init__.py
    ├── test_auth.py     ← pruebas de /auth/register y /auth/login
    └── test_users.py    ← pruebas de /users/ con JWT y roles
```

---

## Estructura de Carpetas

```
mi_proyecto/
├── .github/
│   └── workflows/
│       └── tests.yml         ← workflow de GitHub Actions CI
├── app/
│   ├── __init__.py
│   ├── main.py               ← Punto de entrada: crea la app, registra routers, CORS
│   ├── config.py             ← Settings tipados con pydantic-settings
│   ├── database.py           ← Engine, SessionLocal, Base declarativa
│   ├── auth/
│   │   ├── router.py         ← Endpoints de autenticación
│   │   ├── schemas.py        ← TokenResponse, RegisterRequest, TokenPayload
│   │   ├── services.py       ← Login, register, hash de contraseñas
│   │   └── dependencies.py   ← verify_token, require_role
│   └── users/
│       ├── router.py         ← Endpoints HTTP: recibe requests, llama al service
│       ├── schemas.py        ← Validación y serialización con Pydantic
│       ├── services.py       ← Lógica de negocio
│       ├── repositories.py   ← Acceso a datos, abstrae el ORM
│       └── models.py         ← Esquema de BD con SQLAlchemy
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── test_auth.py
│   └── test_users.py
├── conftest.py
├── alembic.ini
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Arquitectura Multicapa

| Capa | Archivo | Responsabilidad |
|------|---------|-----------------|
| Router / Controller | `router.py` | Endpoints HTTP, recibe y responde requests |
| Schema | `schemas.py` | Valida entradas y serializa salidas (Pydantic) |
| Servicio | `services.py` | Lógica de negocio |
| Repositorio | `repositories.py` | Acceso a datos, abstrae el ORM |
| Modelo | `models.py` | Esquema de BD (SQLAlchemy) |

---

## Verificación Final

```bash
uvicorn app.main:app --reload
```

- `http://127.0.0.1:8000/docs` → Swagger UI carga correctamente ✅
- `http://127.0.0.1:8000/redoc` → ReDoc carga correctamente ✅
- `http://127.0.0.1:8000/api/v1/users/` → `401 Unauthorized` ✅

---

## Endpoints disponibles

| Método | URL | Acción | Auth requerida |
|--------|-----|--------|----------------|
| POST | `/api/v1/auth/register` | Registrar usuario (rol siempre "user") | No |
| POST | `/api/v1/auth/login` | Obtener JWT | No |
| GET | `/api/v1/users/` | Listar usuarios | JWT (admin) |
| POST | `/api/v1/users/` | Crear usuario | JWT (admin) |
| GET | `/api/v1/users/{id}` | Ver usuario | JWT (admin o propio) |
| PUT | `/api/v1/users/{id}` | Actualizar usuario | JWT (admin) |
| POST | `/api/v1/users/{id}/deactivate` | Desactivar usuario | JWT (admin) |
| DELETE | `/api/v1/users/{id}` | Eliminar usuario | JWT (admin) |
| GET | `/docs` | Swagger UI interactivo | No |
| GET | `/redoc` | ReDoc | No |

---

## Errores frecuentes y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `ValidationError` al arrancar | Variable faltante en `.env` | Verificar que todas las variables del `.env.example` estén en `.env` |
| `could not connect to server` | BD no creada o credenciales incorrectas | Crear la BD con `CREATE DATABASE fastapi_db;` y verificar `.env` |
| `Target database is not up to date` | Migraciones pendientes | Ejecutar `alembic upgrade head` |
| `ModuleNotFoundError: app` en pytest | pytest no corre desde `backend/` | Ejecutar `pytest` desde la carpeta `backend/`, no desde la raíz |

---

*DSD-2303 · Desarrollo de Servicios Web*
