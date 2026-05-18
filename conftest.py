# conftest.py
# ─────────────────────────────────────────────────────────────────────────────
# Archivo especial de pytest: se carga AUTOMÁTICAMENTE antes de cualquier test.
# No necesitas importarlo — pytest lo detecta por su nombre.
#
# Responsabilidades:
#   1. Agregar la raíz del proyecto a sys.path para que "app/" sea importable
#   2. Inyectar variables de entorno ANTES de importar app/ (pydantic-settings
#      las lee al importar app.config, así que deben existir primero)
#   3. Crear la BD SQLite de test y limpiarla entre tests
#   4. Proveer fixtures compartidos: client, admin_token, user_token
# ─────────────────────────────────────────────────────────────────────────────

# ── PYTHONPATH ────────────────────────────────────────────────────────────────
# Agrega la raíz del proyecto a sys.path para que "from app.main import app"
# funcione en cualquier entorno (CI, local, cualquier versión de pytest).
#
# ❌ ANTES: dependía de 'pythonpath = .' en pytest.ini, opción añadida en
#           pytest 7.0 — causaba USAGE_ERROR (exit code 4) en CI Ubuntu cuando
#           el runner resolvía una versión de pytest que no la soportaba.
# ✅ AHORA: sys.path.insert() funciona con cualquier versión de pytest y no
#           depende de ninguna opción de configuración del ini.
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import os
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ── 1. Variables de entorno para el entorno de test ──────────────────────────
# Deben declararse ANTES de importar cualquier módulo de "app/".
# os.environ.setdefault() solo las setea si NO existen ya → no sobreescribe
# las que GitHub Actions u otro runner ya haya definido.
#
# ¿Por qué no el .env real?
#   El .env apunta a PostgreSQL. En tests usamos SQLite en memoria,
#   que no requiere servidor externo → los tests corren en cualquier máquina.

os.environ.setdefault("SECRET_KEY",                   "clave-secreta-solo-para-tests")
os.environ.setdefault("DEBUG",                        "True")
os.environ.setdefault("DB_NAME",                      "test_db")
os.environ.setdefault("DB_USER",                      "test_user")
os.environ.setdefault("DB_PASSWORD",                  "test_password")
os.environ.setdefault("DB_HOST",                      "localhost")
os.environ.setdefault("DB_PORT",                      "5432")
os.environ.setdefault("APP_NAME",                     "FastAPI Test")
os.environ.setdefault("APP_DESCRIPTION",              "Suite de tests")
os.environ.setdefault("APP_VERSION",                  "0.0.1")
os.environ.setdefault("ALGORITHM",                    "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES",  "30")

# ── 2. Imports del proyecto (DESPUÉS de setear las env vars) ─────────────────
from app.main import app
from app.database import Base, get_db


# ── 3. Motor de base de datos SQLite para tests ───────────────────────────────
# Archivo en disco (test_temp.db) en lugar de :memory: para que funcione
# correctamente con scopes de sesión mezclados (session + function fixtures).
#
# check_same_thread=False → necesario para SQLite en entornos multihilo.

SQLITE_URL = "sqlite:///./test_temp.db"

engine_test = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
)
SessionTest = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    """
    Reemplaza get_db() de FastAPI para usar la BD de test en lugar de
    PostgreSQL. Patrón oficial de FastAPI para testing con dependency_overrides.
    """
    db = SessionTest()
    try:
        yield db
    finally:
        db.close()


# ── 4. Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Scope SESSION: corre UNA SOLA VEZ al inicio y al final de toda la suite.

    Crea las tablas antes de los tests y las elimina al terminar.
    autouse=True → se aplica sin que cada test lo declare.
    """
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(autouse=True)
def limpiar_bd_entre_tests():
    """
    Scope FUNCTION (default): corre antes y después de CADA test individual.

    1. Inyecta la BD de test en FastAPI (override de get_db).
    2. Después de cada test, elimina todos los registros de la tabla users
       para que los tests sean independientes entre sí.
       → Evita errores de email duplicado entre tests.
    3. Limpia dependency_overrides para no contaminar el test siguiente.

    ⚠ Borra datos, NO tablas. Las tablas se crean una sola vez (setup_test_database).
    """
    # Antes del test: inyectar BD de test
    app.dependency_overrides[get_db] = override_get_db
    yield
    # Después del test: limpiar datos y overrides
    db = SessionTest()
    try:
        db.execute(text("DELETE FROM users"))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    # sqlite_sequence only exists when AUTOINCREMENT is declared on a table.
    # Run in a separate transaction so its absence never rolls back the user delete.
    db2 = SessionTest()
    try:
        db2.execute(text("DELETE FROM sqlite_sequence WHERE name='users'"))
        db2.commit()
    except Exception:
        db2.rollback()
    finally:
        db2.close()
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def client():
    """
    TestClient de FastAPI compartido en toda la sesión.

    scope="session" → se instancia una vez. Más eficiente que crear uno
    por test, y seguro porque limpiar_bd_entre_tests resetea el estado de la BD.
    """
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """
    Crea un usuario admin directamente en la BD de test y devuelve su JWT.

    Por qué insertar directo en lugar de usar /register:
      /register siempre asigna role="user". Para crear un admin hay que
      pasar por la BD directamente.

    Scope FUNCTION (default) → se crea uno nuevo por cada test que lo pida,
    pero como limpiar_bd_entre_tests borra la tabla entre tests, no hay
    conflictos de email duplicado.
    """
    from app.users.models import User
    from app.auth.services import AuthService

    db = SessionTest()
    try:
        admin = User(
            name="Admin Test",
            email="admin@test.com",
            password=AuthService.hash_password("admin123"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.com", "password": "admin123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def user_token(client):
    """
    Registra un usuario normal vía /register y devuelve su JWT.

    Scope FUNCTION → se crea uno nuevo por cada test que lo pida.
    La BD se limpia entre tests, así que el email nunca está duplicado.
    """
    client.post(
        "/api/v1/auth/register",
        json={"name": "Usuario Test", "email": "user@test.com", "password": "user123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "user@test.com", "password": "user123"},
    )
    return response.json()["access_token"]
