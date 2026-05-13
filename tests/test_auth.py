# tests/test_auth.py
# ─────────────────────────────────────────────────────────────────────────────
# Pruebas del módulo de autenticación: /api/v1/auth/register y /auth/login
#
# Tipos de tests incluidos (Sesión 49):
#   🔬 Unitarias     → prueban AuthService aislado con mocks (monkeypatch)
#   🔗 Integración   → prueban el flujo HTTP → servicio → BD de test
#   📋 Parametrizados → un test, múltiples casos con @pytest.mark.parametrize
#
# ── COMPATIBILIDAD bcrypt ────────────────────────────────────────────────────
# bcrypt tiene un límite estricto de 72 bytes por password.
# passlib 1.7.4 codifica la cadena en UTF-8 antes de pasarla a bcrypt,
# así que caracteres multi-byte (tildes, ñ, emojis) cuentan más de 1 byte.
# Regla práctica: usar solo ASCII en passwords de prueba para evitar errores.
#   ✅  "clave123"         →  8  bytes
#   ✅  "claveCorrecta"    →  13 bytes
#   ❌  "miContraseña123"  →  puede superar 72 bytes con bcrypt 5.x
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# BLOQUE 1 — PRUEBAS UNITARIAS de AuthService (con mocks)
# Prueban la lógica de negocio de forma AISLADA, sin HTTP ni BD real.
# Usamos monkeypatch para reemplazar el repositorio con funciones falsas.
# =============================================================================

class TestAuthServiceUnit:
    """
    Analogía Sesión 49 — probar UN INGREDIENTE antes de cocinar el plato:
    solo nos interesa la lógica de AuthService, no la BD ni el HTTP.
    """

    def test_hash_password_genera_hash_diferente_al_original(self):
        """
        UNITARIA: hash_password() nunca devuelve el texto en claro.
        Es un método estático — no necesita BD ni HTTP.

        Nota: usamos password ASCII corto para evitar el límite de 72 bytes
        de bcrypt (passlib 1.7.4 + bcrypt 4.x).
        """
        from app.auth.services import AuthService

        password_original = "clave123"                        # ← ASCII, 8 bytes ✅
        hash_resultado    = AuthService.hash_password(password_original)

        assert hash_resultado != password_original            # no es texto en claro
        assert hash_resultado.startswith("$2b$")             # formato bcrypt

    def test_hash_password_mismo_input_genera_hashes_distintos(self):
        """
        UNITARIA: bcrypt usa un salt aleatorio → dos hashes del mismo
        password son diferentes. Propiedad de seguridad importante.

        Punto para clase: si los hashes fueran iguales, un atacante podría
        construir una tabla de hashes predefinidos (rainbow table) para
        revertir passwords masivamente.
        """
        from app.auth.services import AuthService

        hash1 = AuthService.hash_password("misma_clave")     # ← ASCII ✅
        hash2 = AuthService.hash_password("misma_clave")

        assert hash1 != hash2                                 # salt diferente cada vez

    def test_login_lanza_401_si_usuario_no_existe(self, monkeypatch):
        """
        UNITARIA con mock: si el repositorio no encuentra al usuario,
        el servicio debe lanzar HTTP 401.

        ¿Por qué 401 y no 404?
        Por seguridad: no revelamos si el email existe o no en el sistema.
        Un atacante podría usar 404 para descubrir qué emails están registrados.

        monkeypatch reemplaza get_by_email() con una función falsa que
        devuelve None → el test no depende de la BD real.
        """
        from fastapi import HTTPException
        from app.auth.services import AuthService

        monkeypatch.setattr(
            "app.users.repositories.UserRepository.get_by_email",
            lambda self, email: None,                         # MOCK: no existe
        )

        service = AuthService(db=None)                        # db=None: repo mockeado

        with pytest.raises(HTTPException) as exc_info:
            service.login("fantasma@test.com", "cualquierClave")

        assert exc_info.value.status_code == 401
        assert "Credenciales" in exc_info.value.detail

    def test_login_lanza_401_si_password_incorrecto(self, monkeypatch):
        """
        UNITARIA con mock: password incorrecto → 401.
        Misma respuesta que "usuario no existe" para no revelar cuál falló.
        """
        from fastapi import HTTPException
        from app.auth.services import AuthService, pwd_context

        hash_real = pwd_context.hash("claveCorrecta")        # ← ASCII ✅

        mock_user = type("User", (), {
            "id": 1,
            "email": "user@test.com",
            "password": hash_real,
            "role": "user",
            "is_active": True,
        })()
        monkeypatch.setattr(
            "app.users.repositories.UserRepository.get_by_email",
            lambda self, email: mock_user,
        )

        service = AuthService(db=None)

        with pytest.raises(HTTPException) as exc_info:
            service.login("user@test.com", "claveINCORRECTA") # ← password malo

        assert exc_info.value.status_code == 401

    def test_login_lanza_403_si_usuario_inactivo(self, monkeypatch):
        """
        UNITARIA con mock: usuario desactivado → 403 Forbidden.

        Diferencia clave para la clase:
          401 = "No sé quién eres" (credenciales inválidas o faltantes)
          403 = "Sé quién eres, pero no puedes entrar" (cuenta inactiva, rol insuficiente)
        """
        from fastapi import HTTPException
        from app.auth.services import AuthService, pwd_context

        hash_real = pwd_context.hash("clave123")             # ← ASCII ✅

        mock_user = type("User", (), {
            "id": 2,
            "email": "inactivo@test.com",
            "password": hash_real,
            "role": "user",
            "is_active": False,                               # ← cuenta desactivada
        })()
        monkeypatch.setattr(
            "app.users.repositories.UserRepository.get_by_email",
            lambda self, email: mock_user,
        )

        service = AuthService(db=None)

        with pytest.raises(HTTPException) as exc_info:
            service.login("inactivo@test.com", "clave123")

        assert exc_info.value.status_code == 403

    def test_register_lanza_400_si_email_duplicado(self, monkeypatch):
        """
        UNITARIA con mock: email ya registrado → 400 Bad Request.
        """
        from fastapi import HTTPException
        from app.auth.services import AuthService
        from app.auth.schemas import RegisterRequest

        monkeypatch.setattr(
            "app.users.repositories.UserRepository.get_by_email",
            lambda self, email: {"id": 1, "email": email},   # MOCK: ya existe
        )

        service = AuthService(db=None)
        data = RegisterRequest(name="Ana", email="dup@test.com", password="clave123")

        with pytest.raises(HTTPException) as exc_info:
            service.register(data)

        assert exc_info.value.status_code == 400
        assert "registrado" in exc_info.value.detail.lower()


# =============================================================================
# BLOQUE 2 — PRUEBAS DE INTEGRACIÓN del endpoint /auth/register
# Flujo completo: HTTP → router → service → repositorio → BD de test
# =============================================================================

class TestRegisterIntegration:

    def test_registro_exitoso_devuelve_201(self, client):
        """
        INTEGRACIÓN: registro válido → 201 con datos del usuario (sin password).
        """
        payload = {
            "name": "Carlos Perez",                           # ← sin tilde, ASCII ✅
            "email": "carlos@test.com",
            "password": "segura123",
        }
        response = client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["email"]     == "carlos@test.com"
        assert data["name"]      == "Carlos Perez"
        assert data["role"]      == "user"                    # siempre "user" en registro público
        assert data["is_active"] is True
        assert "id"       in data
        assert "password" not in data                         # el hash NUNCA aparece en la respuesta

    def test_registro_no_permite_elegir_rol_admin(self, client):
        """
        INTEGRACIÓN — regla de seguridad:
        aunque el cliente mande role="admin", siempre se asigna role="user".
        """
        payload = {
            "name": "Intento Malicioso",
            "email": "hacker@test.com",
            "password": "hack123",
            "role": "admin",                                  # ← intento de escalada
        }
        response = client.post("/api/v1/auth/register", json=payload)

        if response.status_code == 201:
            assert response.json()["role"] == "user"

    def test_registro_email_duplicado_devuelve_400(self, client):
        """
        INTEGRACIÓN: mismo email dos veces → 400 Bad Request.
        """
        payload = {"name": "Maria", "email": "maria@test.com", "password": "clave123"}

        client.post("/api/v1/auth/register", json=payload)               # 1er registro ✅
        response = client.post("/api/v1/auth/register", json=payload)    # duplicado ❌

        assert response.status_code == 400
        assert "registrado" in response.json()["detail"].lower()


# =============================================================================
# BLOQUE 3 — PRUEBAS DE INTEGRACIÓN del endpoint /auth/login
# =============================================================================

class TestLoginIntegration:

    def test_login_exitoso_devuelve_token(self, client):
        """
        INTEGRACIÓN: credenciales válidas → 200 con JWT.

        ⚠️ /auth/login usa OAuth2PasswordRequestForm → recibe form-data,
           no JSON. Por eso usamos data={} en lugar de json={}.
        """
        client.post(
            "/api/v1/auth/register",
            json={"name": "Lucia", "email": "lucia@test.com", "password": "clave123"},
        )
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "lucia@test.com", "password": "clave123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    def test_login_password_incorrecto_devuelve_401(self, client):
        """INTEGRACIÓN: password incorrecto → 401."""
        client.post(
            "/api/v1/auth/register",
            json={"name": "Pedro", "email": "pedro@test.com", "password": "correcta"},
        )
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "pedro@test.com", "password": "incorrecta"},
        )
        assert response.status_code == 401

    def test_login_usuario_inexistente_devuelve_401(self, client):
        """INTEGRACIÓN: email no registrado → 401 (no 404)."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "noexiste@test.com", "password": "cualquier"},
        )
        assert response.status_code == 401


# =============================================================================
# BLOQUE 4 — PARAMETRIZACIÓN (@pytest.mark.parametrize)
# Un test, múltiples casos. pytest corre una iteración por cada fila.
# =============================================================================

@pytest.mark.parametrize("name, email, password, status_esperado", [
    # Casos VÁLIDOS
    ("Ana Garcia",   "ana@test.com",     "clave123",   201),
    ("Bob Smith",    "bob@test.com",     "secreto456", 201),
    # Casos INVÁLIDOS — Pydantic los rechaza antes del servicio → 422
    ("Sin Email",    "no-es-email",      "clave123",   422),
    ("Vacio",        "",                 "clave123",   422),
    ("",             "nombre@test.com",  "clave123",   422),  # name vacío
])
def test_register_multiples_casos(client, name, email, password, status_esperado):
    """
    PARAMETRIZADO: pytest ejecuta este test 5 veces y reporta cada una por separado.

    Los casos 422 nunca llegan al servicio — Pydantic los rechaza en el router.
    Los casos 201 sí crean un usuario en la BD (que se limpia entre tests gracias
    al fixture limpiar_bd_entre_tests del conftest.py).
    """
    payload = {"name": name, "email": email, "password": password}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status_esperado


@pytest.mark.parametrize("username, password, status_esperado", [
    ("noexiste1@test.com", "cualquier",  401),
    ("noexiste2@test.com", "otraclave",  401),
    ("@malformado",        "clave",      401),
])
def test_login_multiples_casos_fallidos(client, username, password, status_esperado):
    """PARAMETRIZADO: casos de login que siempre deben fallar con 401."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == status_esperado