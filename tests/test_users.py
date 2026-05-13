# tests/test_users.py
# ─────────────────────────────────────────────────────────────────────────────
# Pruebas del módulo de usuarios: /api/v1/users/
#
# Este módulo tiene CONTROL DE ACCESO con JWT y roles:
#   - GET /users/          → solo admin
#   - GET /users/{id}      → admin ve cualquiera; user solo se ve a sí mismo
#   - POST /users/         → solo admin
#   - PUT /users/{id}      → solo admin
#   - POST /users/{id}/deactivate → solo admin
#   - DELETE /users/{id}   → solo admin
#
# Los fixtures admin_token y user_token vienen del conftest.py
#
# Para correr:
#   pytest tests/test_users.py -v
# ─────────────────────────────────────────────────────────────────────────────

import pytest
from fastapi.testclient import TestClient


# =============================================================================
# BLOQUE 1 — PRUEBAS UNITARIAS de UserService (con mocks)
# Prueban la lógica de negocio SIN hacer peticiones HTTP
# =============================================================================

class TestUserServiceUnit:
    """
    Analogía Sesión 49: probamos cada pieza (tornillo) de forma individual.
    monkeypatch reemplaza el repositorio con funciones falsas → sin BD.
    """

    def test_get_by_id_lanza_404_si_no_existe(self, monkeypatch):
        """
        UNITARIA: si el repo devuelve None, el servicio debe lanzar 404.
        No necesitamos BD ni HTTP para probar esta lógica.
        """
        from fastapi import HTTPException
        from app.users.services import UserService

        # MOCK: el repositorio siempre dice "no encontré nada"
        monkeypatch.setattr(
            "app.users.repositories.UserRepository.get_by_id",
            lambda self, user_id: None,
        )

        service = UserService(db=None)  # db=None porque el repo está mockeado

        with pytest.raises(HTTPException) as exc_info:
            service.get_by_id(9999)

        assert exc_info.value.status_code == 404
        assert "no encontrado" in exc_info.value.detail.lower()

    def test_create_lanza_400_si_email_duplicado(self, monkeypatch):
        """
        UNITARIA: si el email ya existe, create() debe lanzar 400.
        Usamos mock para simular que el repo "encuentra" ese email.
        """
        from fastapi import HTTPException
        from app.users.services import UserService
        from app.users.schemas import UserCreate

        # MOCK: el repo "encuentra" un usuario con ese email
        monkeypatch.setattr(
            "app.users.repositories.UserRepository.get_by_email",
            lambda self, email: {"id": 1, "email": email},
        )

        service = UserService(db=None)
        data = UserCreate(name="Test", email="dup@test.com", password="1234")

        with pytest.raises(HTTPException) as exc_info:
            service.create(data)

        assert exc_info.value.status_code == 400

    def test_deactivate_lanza_404_si_usuario_no_existe(self, monkeypatch):
        """
        UNITARIA: intentar desactivar un usuario inexistente → 404.
        """
        from fastapi import HTTPException
        from app.users.services import UserService

        monkeypatch.setattr(
            "app.users.repositories.UserRepository.get_by_id",
            lambda self, user_id: None,
        )

        service = UserService(db=None)

        with pytest.raises(HTTPException) as exc_info:
            service.deactivate(999)

        assert exc_info.value.status_code == 404

    def test_delete_lanza_404_si_usuario_no_existe(self, monkeypatch):
        """
        UNITARIA: intentar eliminar un usuario inexistente → 404.
        """
        from fastapi import HTTPException
        from app.users.services import UserService

        monkeypatch.setattr(
            "app.users.repositories.UserRepository.get_by_id",
            lambda self, user_id: None,
        )

        service = UserService(db=None)

        with pytest.raises(HTTPException) as exc_info:
            service.delete(999)

        assert exc_info.value.status_code == 404


# =============================================================================
# BLOQUE 2 — PRUEBAS DE AUTORIZACIÓN
# Verifican que el control de acceso (JWT + roles) funciona correctamente.
#
# Esta es la parte MÁS IMPORTANTE para la Actividad 11:
#   → 401 = sin token (no autenticado)
#   → 403 = con token pero sin el rol necesario
# =============================================================================

class TestUsersAutorizacion:
    """
    Analogía Sesión 49:
    Probamos que el SISTEMA DE SEGURIDAD funciona, no solo que el endpoint existe.
    """

    # ── Sin token (401) ───────────────────────────────────────────────────────

    def test_listar_usuarios_sin_token_devuelve_401(self, client):
        """
        Sin token → 401 Unauthorized.
        El endpoint requiere autenticación — cualquier petición sin JWT falla.
        """
        response = client.get("/api/v1/users/")
        assert response.status_code == 401

    def test_crear_usuario_sin_token_devuelve_401(self, client):
        """Sin token en POST /users/ → 401."""
        response = client.post(
            "/api/v1/users/",
            json={"name": "Test", "email": "t@t.com", "password": "1234"},
        )
        assert response.status_code == 401

    def test_eliminar_usuario_sin_token_devuelve_401(self, client):
        """Sin token en DELETE /users/{id} → 401."""
        response = client.delete("/api/v1/users/1")
        assert response.status_code == 401

    # ── Con token de usuario normal (403) ─────────────────────────────────────

    def test_listar_usuarios_como_user_devuelve_403(self, client, user_token):
        """
        Con token de rol "user" en un endpoint que requiere "admin" → 403 Forbidden.

        Diferencia clave:
          401 = "¿Quién eres?" (sin token o token inválido)
          403 = "Sé quién eres, pero no tienes permiso" (rol insuficiente)
        """
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_crear_usuario_como_user_devuelve_403(self, client, user_token):
        """Crear usuarios es solo para admins → user recibe 403."""
        response = client.post(
            "/api/v1/users/",
            json={"name": "Nuevo", "email": "nuevo@test.com", "password": "1234"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    def test_eliminar_usuario_como_user_devuelve_403(self, client, user_token):
        """Eliminar usuarios es solo para admins → user recibe 403."""
        response = client.delete(
            "/api/v1/users/1",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 403

    # ── Con token inválido (401) ──────────────────────────────────────────────

    def test_token_malformado_devuelve_401(self, client):
        """Un JWT con formato incorrecto debe rechazarse con 401."""
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": "Bearer esto-no-es-un-jwt"},
        )
        assert response.status_code == 401

    def test_token_falso_devuelve_401(self, client):
        """Un JWT firmado con clave diferente debe rechazarse."""
        # Este token está firmado con "clave-falsa", no con la clave real del servidor
        import jwt as pyjwt
        fake_token = pyjwt.encode(
            {"sub": "1", "role": "admin", "email": "fake@test.com"},
            "clave-falsa-no-valida",
            algorithm="HS256",
        )
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert response.status_code == 401


# =============================================================================
# BLOQUE 3 — PRUEBAS DE INTEGRACIÓN con rol admin
# Prueban el flujo completo: petición HTTP autenticada → BD → respuesta
# =============================================================================

class TestUsersAdminIntegration:
    """
    Analogía Sesión 49: probamos el SISTEMA COMPLETO (sistema de frenos).
    Aquí todo trabaja junto: HTTP + JWT + servicio + repositorio + BD.
    """

    def test_admin_puede_listar_usuarios(self, client, admin_token):
        """
        INTEGRACIÓN: admin con token válido puede ver la lista de usuarios.
        La respuesta debe ser una lista (puede estar vacía o tener elementos).
        """
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_admin_puede_crear_usuario(self, client, admin_token):
        """
        INTEGRACIÓN: admin crea un usuario → 201 con datos del usuario.
        """
        payload = {
            "name": "Nuevo por Admin",
            "email": "nuevo_admin@test.com",
            "password": "segura456",
            "role": "user",
        }
        response = client.post(
            "/api/v1/users/",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"]     == "nuevo_admin@test.com"
        assert data["is_active"] is True
        assert "id" in data
        assert "password" not in data  # nunca devolvemos el hash

    def test_admin_puede_obtener_usuario_por_id(self, client, admin_token):
        """
        INTEGRACIÓN: admin crea un usuario y luego lo consulta por ID.
        Verifica que el flujo crear → consultar funciona end-to-end.
        """
        # Crear
        create = client.post(
            "/api/v1/users/",
            json={"name": "Para Consultar", "email": "consultar@test.com", "password": "1234", "role": "user"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        user_id = create.json()["id"]

        # Consultar
        response = client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["id"] == user_id

    def test_admin_get_usuario_inexistente_devuelve_404(self, client, admin_token):
        """
        INTEGRACIÓN: consultar un ID que no existe → 404 Not Found.
        """
        response = client.get(
            "/api/v1/users/99999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404

    def test_admin_puede_desactivar_usuario(self, client, admin_token):
        """
        INTEGRACIÓN: admin desactiva un usuario → is_active pasa a False.
        """
        # Crear usuario activo
        create = client.post(
            "/api/v1/users/",
            json={"name": "Para Desactivar", "email": "desactivar@test.com", "password": "1234", "role": "user"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        user_id = create.json()["id"]

        # Desactivar
        response = client.post(
            f"/api/v1/users/{user_id}/deactivate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_admin_puede_eliminar_usuario(self, client, admin_token):
        """
        INTEGRACIÓN: admin elimina un usuario → 204 No Content.
        Luego verifica que el usuario ya no existe (404).
        """
        # Crear
        create = client.post(
            "/api/v1/users/",
            json={"name": "Para Eliminar", "email": "eliminar@test.com", "password": "1234", "role": "user"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        user_id = create.json()["id"]

        # Eliminar
        delete_res = client.delete(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert delete_res.status_code == 204

        # Verificar que ya no existe
        get_res = client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert get_res.status_code == 404


# =============================================================================
# BLOQUE 4 — PRUEBAS DEL USUARIO NORMAL (acceso a su propio perfil)
# Un "user" no puede ver otros usuarios, pero sí puede ver el suyo.
# =============================================================================

class TestUserPropioAcceso:

    def test_user_puede_ver_su_propio_perfil(self, client, user_token):
        """
        INTEGRACIÓN: un usuario con rol "user" puede consultar SU propio ID.

        Para esto necesitamos saber el ID del usuario que tiene el token.
        Lo obtenemos decodificando el JWT (sin verificar firma, solo leyendo).
        """
        import base64
        import json

        # Decodificar el payload del JWT (parte del medio, sin verificar firma)
        payload_b64 = user_token.split(".")[1]
        # Agregar padding si es necesario (base64url)
        padding = 4 - len(payload_b64) % 4
        payload_b64 += "=" * (padding % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        user_id = int(payload["sub"])

        response = client.get(
            f"/api/v1/users/{user_id}",
            headers={"Authorization": f"Bearer {user_token}"},
        )

        # El usuario puede ver su propio perfil
        assert response.status_code == 200
        assert response.json()["id"] == user_id


# =============================================================================
# BLOQUE 5 — PARAMETRIZACIÓN sobre creación de usuarios
# =============================================================================

@pytest.mark.parametrize("name, email, password, role, status_esperado", [
    # Casos válidos (con token de admin)
    ("Valido Uno",  "valido1@test.com", "clave1", "user",  201),
    ("Valido Dos",  "valido2@test.com", "clave2", "admin", 201),
    # Email inválido → 422 (Pydantic lo rechaza antes de llegar al servicio)
    ("Mal Email",   "no-es-email",      "clave3", "user",  422),
    ("Email Vacio", "",                 "clave4", "user",  422),
])
def test_crear_usuario_admin_multiples_casos(client, admin_token, name, email, password, role, status_esperado):
    """
    PARAMETRIZADO: verifica que la creación por admin funciona con distintos inputs.

    Punto educativo: los casos 422 NUNCA llegan al servicio — Pydantic los
    rechaza en el router antes de ejecutar cualquier lógica de negocio.
    """
    payload = {"name": name, "email": email, "password": password, "role": role}
    response = client.post(
        "/api/v1/users/",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == status_esperado
