"""Middleware utilitario para volcar información de errores.

`DumpOnErrorMiddleware` registra en los logs los datos relevantes de la
solicitud y el *traceback* cuando ocurre una excepción no controlada.
"""

import logging
import traceback


logger = logging.getLogger(__name__)


class DumpOnErrorMiddleware:
    """Registra detalles de la petición si se produce un error."""

    def __init__(self, get_response):
        """Inicializa el middleware.

        Args:
            get_response (Callable): Función que procesa la solicitud y
                devuelve la respuesta.
        """

        self.get_response = get_response

    def __call__(self, request):
        """Procesa la solicitud y captura excepciones.

        Args:
            request (HttpRequest): La solicitud entrante.

        Returns:
            HttpResponse: Respuesta generada por la vista.

        Raises:
            Exception: Propaga la excepción original tras registrarla.
        """

        try:
            return self.get_response(request)
        except Exception:
            try:
                logger.error(
                    "500 en %s %s\nPOST=%s\nFILES=%s\nTRACE=\n%s",
                    request.method,
                    request.path,
                    dict(request.POST),
                    {k: v.name for k, v in request.FILES.items()},
                    traceback.format_exc(),
                )
            except Exception:
                logger.exception("No se pudo volcar el error")
            raise
