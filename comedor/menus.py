"""Los menús que publica el colegio.

Todos los PDF están en la misma carpeta de la web del colegio y usan la misma
plantilla. Si el colegio añade o quita alguno, basta con cambiar esta lista.
"""

import os

URL_BASE = os.environ.get("MENUS_URL_BASE") or (
    "https://palomerasbajas.org/wp/wp-content/uploads/menus_en_curso/"
)

# (clave, nombre que se ve en la web, fichero PDF)
MENUS = [
    ("orientativo", "Orientativo", "ORIENTATIVO.pdf"),
    ("sin-huevo", "Sin huevo", "SIN-HUEVO.pdf"),
    ("sin-lacteos", "Sin lácteos ni proteína de leche", "SIN-LACTEOS.pdf"),
    ("sin-frutos-secos", "Sin frutos secos", "SIN-FRUTOS-SECOS.pdf"),
    ("sin-pescado", "Sin pescado", "SIN-PESCADO.pdf"),
    ("celiacos", "Celíacos (sin gluten)", "CELIACOS.pdf"),
    ("multialergico", "Multialérgico", "MULTIALERGICO.pdf"),
    ("musulmanes", "Musulmán", "MUSULMANES.pdf"),
    ("musulman-sin-carne", "Musulmán sin carne", "MUSULMAN-SIN-CARNE.pdf"),
]

# El menú del que se envían los avisos por Telegram.
MENU_AVISOS = os.environ.get("MENU_AVISOS") or "orientativo"


def url_pdf(fichero: str) -> str:
    return URL_BASE + fichero
