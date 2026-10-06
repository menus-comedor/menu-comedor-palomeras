"""Clasifica los platos en grandes grupos de alimentos.

Sirve para el aviso de "para la cena, mejor evitar: pescado, huevo...".
Si echas en falta alguna palabra, añádela aquí (en minúsculas y sin tildes).
"""

import re
import unicodedata

# (clave, emoji, palabras que la identifican)
CATEGORIAS = [
    ("pescado", "🐟", ["pescado", "merluza", "bacalao", "palometa", "boquerones", "abadejo",
                       "salmon", "atun", "lenguado", "gallo", "sardinas", "rape", "bonito",
                       "caballa", "dorada", "lubina", "panga", "fletan", "surimi"]),
    ("marisco", "🦐", ["calamar", "calamares", "sepia", "gambas", "mejillones", "pota"]),
    ("huevo", "🥚", ["huevo", "huevos", "tortilla"]),
    ("carne", "🥩", ["lomo", "magro", "lacon", "chorizo", "ternera", "morcillo", "cerdo",
                     "jamon", "salchichas", "hamburguesa", "albondigas", "filete", "cordero",
                     "pollo", "pavo", "morcilla", "carne", "cocido completo"]),
    ("legumbres", "🫘", ["garbanzos", "lentejas", "judias blancas", "judias pintas", "alubias",
                         "cocido", "habas", "guisantes"]),
    ("pasta", "🍝", ["macarrones", "espaguetis", "fideos", "pasta", "tallarines", "lasana",
                     "canelones", "fideua"]),
    ("arroz", "🍚", ["arroz"]),
    ("patata", "🥔", ["patatas", "patata", "pure de patata"]),
]

EMOJI = {clave: emoji for clave, emoji, _ in CATEGORIAS}


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower()


def categorias(texto: str) -> list[str]:
    """Devuelve las categorías de un plato, p. ej. ["pescado", "patata"]."""
    t = _normalizar(texto)
    # "boloñesa con soja texturizada" no es carne.
    if "soja texturizada" in t:
        t = t.replace("bolonesa", "")
    return [
        clave for clave, _, palabras in CATEGORIAS
        if any(re.search(rf"\b{re.escape(p)}\b", t) for p in palabras)
    ]


def categorias_dia(dia) -> list[str]:
    vistas: list[str] = []
    for plato in dia.platos:
        for c in categorias(plato.nombre):
            if c not in vistas:
                vistas.append(c)
    return vistas


def etiquetas(claves: list[str]) -> str:
    return " · ".join(f"{EMOJI[c]} {c}" for c in claves)
