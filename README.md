# Scaffolding: FastAPI + SQLAlchemy + JWT + PostgreSQL
### Arquitectura Multicapa · DSD-2303

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

## Estructura de Carpetas

```
mi_proyecto/
├── app/
│   ├── __init__.py
│   ├── main.py               ← Punto de entrada: crea la app, registra routers, CORS
│   ├── config.py             ← Settings tipados con pydantic-settings
│   ├── database.py           ← Engine, SessionLocal, Base declarativa
│   │
│   └── users/
│       ├── __init__.py
│       ├── router.py         ← Endpoints HTTP: recibe requests, llama al service   ⚠️ crear manualmente
│       ├── schemas.py        ← Validación y serialización con Pydantic             ⚠️ crear manualmente
│       ├── services.py       ← Lógica de negocio                                   ⚠️ crear manualmente
│       ├── repositories.py   ← Acceso a datos, abstrae el ORM                      ⚠️ crear manualmente
│       └── models.py         ← Esquema de BD con SQLAlchemy                        ⚠️ crear manualmente
│
├── alembic/
│   ├── versions/
│   └── env.py                ← Configuración de migraciones
│
├── alembic.ini               ← Generado por `alembic init`
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

## Paso a Paso

### 1. Entorno virtual y dependencias

```bash
mkdir mi_proyecto && cd mi_proyecto

python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

pip install fastapi "uvicorn[standard]" \
            sqlalchemy alembic \
            psycopg2-binary \
            pydantic-settings "pydantic[email]" \
            "python-jose[cryptography]" \
            "passlib[bcrypt]"

pip freeze > requirements.txt
```

### 2. Scaffolding del proyecto

```bash
mkdir -p app/users
touch app/__init__.py
touch app/main.py app/config.py app/database.py

touch app/users/__init__.py
touch app/users/router.py
touch app/users/schemas.py
touch app/users/services.py
touch app/users/repositories.py
touch app/users/models.py

alembic init alembic

touch .env .env.example .gitignore
```

---

## Archivos de Configuración

### `.env`
```ini
SECRET_KEY=MySecretKeyForFastAPIApp
DEBUG=True
DB_NAME=fastapi_db
DB_USER=testuser
DB_PASSWORD=testuser
DB_HOST=localhost
DB_PORT=5432
APP_NAME=My FastAPI App
APP_DESCRIPTION=A simple FastAPI app
APP_VERSION=1.0.0
```

> ⚠️ La contraseña **no debe contener caracteres especiales** (acentos, ñ, símbolos). Usa solo letras, números, guiones y guiones bajos. PostgreSQL y psycopg2 pueden fallar al conectarse si la contraseña contiene caracteres fuera del rango ASCII.

### `.env.example`
```ini
SECRET_KEY=
DEBUG=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
APP_NAME=
APP_DESCRIPTION=
APP_VERSION=
```

### `.gitignore`
```
venv/
__pycache__/
*.pyc
.env
*.sqlite3
.DS_Store
```

### `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    debug: bool
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str
    app_name: str
    app_description: str
    app_version: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"

settings = Settings()
```

> **¿Por qué `pydantic-settings` en lugar de `os.getenv()`?**  
> Cada variable tiene tipo explícito y se valida al arrancar la app. Si falta `SECRET_KEY` o `DB_NAME`, FastAPI lanza un error claro antes de levantar el servidor.

### `app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# Dependencia para inyectar la sesión en los routers
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.users.router import router as users_router

app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (solo desarrollo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers versionados
app.include_router(users_router, prefix="/api/v1")
```

### `alembic/env.py` — modificaciones necesarias

Después de `alembic init alembic`, editar `alembic/env.py` en tres puntos:

**1. Agregar al inicio del archivo, antes de cualquier import del proyecto:**
```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.config import settings
from app.database import Base
from app.users import models  # noqa: F401 — necesario para que Alembic detecte los modelos
```

**2. Agregar o actualizar justo después de la línea `config = context.config`:**
```python
config = context.config

config.set_main_option("sqlalchemy.url", settings.database_url)  # ← agregar o actualizar
```

> ⚠️ Esta línea puede no existir en el archivo generado. Si no está, agrégala. Si está con otro valor, reemplázala.

**3. Reemplazar `target_metadata = None` por:**
```python
target_metadata = Base.metadata
```

### `alembic.ini` — único cambio necesario

```ini
# Dejar en blanco — la URL se inyecta desde env.py
sqlalchemy.url =
```

---

## Esqueleto de Capas — Arquitectura Multicapa

### `models.py`
```python
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id:         Mapped[int]      = mapped_column(primary_key=True, index=True)
    name:       Mapped[str]      = mapped_column(String(100))
    email:      Mapped[str]      = mapped_column(String(255), unique=True, index=True)
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

### `schemas.py`
```python
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

> **`from_attributes = True`** es el equivalente a `read_only_fields` en Django: le dice a Pydantic que puede leer los datos directamente desde un objeto SQLAlchemy.

### `repositories.py`
```python
from sqlalchemy.orm import Session
from app.users.models import User
from app.users.schemas import UserCreate

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[User]:
        return self.db.query(User).order_by(User.created_at.desc()).all()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate(self, user: User) -> User:
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user
```

### `services.py`
```python
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.users.repositories import UserRepository
from app.users.schemas import UserCreate, UserResponse

class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def get_all(self) -> list[UserResponse]:
        return self.repo.get_all()

    def get_by_id(self, user_id: int) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return user

    def create(self, data: UserCreate) -> UserResponse:
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")
        return self.repo.create(data)

    def deactivate(self, user_id: int) -> UserResponse:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
        return self.repo.deactivate(user)
```

### `router.py`
```python
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.users.services import UserService
from app.users.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/", response_model=list[UserResponse])
def get_all(db: Session = Depends(get_db)):
    return UserService(db).get_all()

@router.get("/{user_id}", response_model=UserResponse)
def get_by_id(user_id: int, db: Session = Depends(get_db)):
    return UserService(db).get_by_id(user_id)

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create(data: UserCreate, db: Session = Depends(get_db)):
    return UserService(db).create(data)

@router.post("/{user_id}/deactivate", response_model=UserResponse)
def deactivate(user_id: int, db: Session = Depends(get_db)):
    return UserService(db).deactivate(user_id)
```

---

## Configurar y ejecutar Alembic

```bash
# Crear la primera migración (detecta los modelos automáticamente)
alembic revision --autogenerate -m "create users table"

# Aplicar la migración
alembic upgrade head
```

> ⚠️ Asegúrate de que la base de datos exista en PostgreSQL antes de migrar:
> ```sql
> CREATE DATABASE fastapi_db;
> ```

---

## Verificación Final

```bash
uvicorn app.main:app --reload
```

- `http://127.0.0.1:8000/docs` → Swagger UI carga correctamente ✅
- `http://127.0.0.1:8000/redoc` → ReDoc carga correctamente ✅
- `http://127.0.0.1:8000/api/v1/users/` → `401 Unauthorized` ✅

---

## Endpoints disponibles tras el scaffolding

| Método | URL | Acción | Auth |
|--------|-----|--------|------|
| GET | `/api/v1/users/` | Listar usuarios | JWT |
| POST | `/api/v1/users/` | Crear usuario | JWT |
| GET | `/api/v1/users/{id}` | Ver usuario | JWT |
| POST | `/api/v1/users/{id}/deactivate` | Desactivar usuario | JWT |
| GET | `/docs` | Swagger UI interactivo | No |
| GET | `/redoc` | ReDoc | No |

> Cuando el proyecto crezca y necesite una `v2`, basta con agregar un nuevo router con `prefix="/api/v2"` en `main.py` sin romper los clientes que usan `v1`.

---

## Errores frecuentes y soluciones

| Error | Causa | Solución |
|-------|-------|----------|
| `ValidationError` al arrancar | Variable faltante en `.env` | Verificar que todas las variables del `.env.example` estén en `.env` |
| `could not connect to server` | BD no creada o credenciales incorrectas | Crear la BD con `CREATE DATABASE fastapi_db;` y verificar `.env` |
| `Target database is not up to date` | Migraciones pendientes | Ejecutar `alembic upgrade head` |
| `Can't locate revision` | Carpeta `alembic/versions/` vacía | Ejecutar `alembic revision --autogenerate -m "init"` |
| `ModuleNotFoundError: app` | Alembic no encuentra el proyecto | Verificar el bloque `sys.path.append` en `alembic/env.py` |

---

*DSD-2303 · Desarrollo de Servicios Web · Instituto Tecnológico de Oaxaca*
