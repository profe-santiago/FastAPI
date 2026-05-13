import logging
import os

# Nos aseguramos de que la carpeta logs/ exista antes de crear el archivo
# exist_ok=True evita error si ya existe
os.makedirs("app/logs", exist_ok=True)


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("fastapi_app")

    # Si ya tiene handlers configurados no los duplicamos
    # Esto evita que los logs aparezcan múltiples veces si la función se llama más de una vez
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Formato del log — timestamp, nivel, y mensaje
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler 1 — escribe en consola (útil en desarrollo)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Handler 2 — escribe en archivo (persiste los logs)
    # mode="a" = append — no sobreescribe, acumula
    file_handler = logging.FileHandler("app/logs/app.log", mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

'''
DEBUG detalles internos — solo en desarrollo
INFO: Eventos normales — request recibida, usuario creado
WARNING: Algo inusual pero no crítico — password intento fallido
ERROR: Algo falló pero la app sigue corriendo
CRITICAL: Algo falló y la app puede caer

'''