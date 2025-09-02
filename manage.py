#!/usr/bin/env python
import os
import sys


def main():
    """
    Punto de entrada de Django.
    Ajuste: inyectamos SECRET_KEY para que los comandos locales funcionen
    aunque no tengas variables de entorno configuradas en Windows/PowerShell.
    """
    # ⬇️ tu SECRET_KEY (la que me diste)
    os.environ.setdefault("SECRET_KEY", "9d29ed5ddd2a0ba5b122b5123cf9a628")

    # Selecciona el módulo de settings según la variable de entorno
    env = os.environ.get("DJANGO_ENV", "dev")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"project.settings.{env}")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y disponible en tu entorno virtual?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
