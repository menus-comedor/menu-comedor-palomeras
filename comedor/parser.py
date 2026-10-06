"""Lee el PDF mensual del menú del comedor y lo convierte en datos estructurados.

El PDF es una cuadrícula de 5 columnas (lunes a viernes) y una fila por semana.
Cada celda tiene, de arriba a abajo:

    Primer plato            (puede ocupar varias líneas)        [nº del día]
    Segundo plato           (puede ocupar varias líneas)
    Postre
    Pan
    Kcal ... / Prot ... / Lip ... / H.C. ...

Usamos las coordenadas de cada palabra (pdfplumber) en lugar del texto plano,
porque el texto plano mezcla las columnas.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date
from itertools import groupby

import pdfplumber

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}

# Leyenda de alérgenos que aparece al pie del PDF (los 14 alérgenos de la UE).
ALERGENOS = {
    1: "gluten", 2: "leche", 3: "huevo", 4: "pescado", 5: "crustáceos",
    6: "moluscos", 7: "cacahuete", 8: "soja", 9: "frutos secos", 10: "apio",
    11: "mostaza", 12: "sésamo", 13: "sulfitos", 14: "altramuces",
}

# "(1, 8, 12)". A veces el texto del PDF viene cortado y falta el ")" final.
RE_ALERGENOS = re.compile(r"\s*\(([\d,\s]+)(?:\)|,?\s*$)")
RE_NUTRICION = re.compile(
    r"Kcal\s*(\d+)\s*/\s*Prot\s*(\d+)\s*/\s*Lip\s*(\d+)\s*/\s*H\.C\.\s*(\d+)"
)

# Tolerancias en puntos PDF (1 pt = 1/72 pulgadas).
MARGEN_X = 4
SALTO_BLOQUE = 11  # los platos van cada ~9 pt; postre/pan/kcal cada ~12 pt


class ErrorDeFormato(Exception):
    """El PDF no tiene el formato esperado (¿ha cambiado la plantilla?)."""


@dataclass
class Plato:
    nombre: str
    alergenos: list[str] = field(default_factory=list)


@dataclass
class Dia:
    fecha: str  # AAAA-MM-DD
    festivo: bool = False
    nota: str = ""  # p. ej. "FIESTA"
    primero: Plato | None = None
    segundo: Plato | None = None
    otros_platos: list[Plato] = field(default_factory=list)  # por si hay más de dos
    postre: Plato | None = None
    pan: Plato | None = None
    kcal: int | None = None

    @property
    def platos(self) -> list[Plato]:
        return [p for p in (self.primero, self.segundo, *self.otros_platos) if p]


def _plato(texto: str) -> Plato:
    codigos: list[int] = []
    for grupo in RE_ALERGENOS.findall(texto):
        codigos += [int(c) for c in re.findall(r"\d+", grupo)]
    nombre = re.sub(r"\s+", " ", RE_ALERGENOS.sub("", texto)).strip()
    return Plato(nombre, [ALERGENOS.get(c, str(c)) for c in sorted(set(codigos))])


def _agrupar(valores: list[float], tolerancia: float) -> list[float]:
    """Agrupa valores cercanos y devuelve el mínimo de cada grupo."""
    grupos: list[list[float]] = []
    for v in sorted(valores):
        if grupos and v - grupos[-1][-1] <= tolerancia:
            grupos[-1].append(v)
        else:
            grupos.append([v])
    return [g[0] for g in grupos]


def _lineas(palabras: list[dict]) -> list[tuple[float, str]]:
    palabras = sorted(palabras, key=lambda w: (round(w["top"]), w["x0"]))
    return [
        (top, " ".join(w["text"] for w in grupo))
        for top, grupo in ((t, list(g)) for t, g in groupby(palabras, key=lambda w: round(w["top"])))
    ]


def _separar_platos(lineas: list[str]) -> list[str]:
    """Une las líneas partidas de cada plato.

    Los platos siempre empiezan por mayúscula; las líneas que continúan un
    plato empiezan por minúscula o por número ("casero", "11, 13)").
    """
    platos: list[str] = []
    for linea in lineas:
        if platos and not linea[:1].isupper():
            platos[-1] += " " + linea
        else:
            platos.append(linea)
    return platos


def _leer_celda(palabras: list[dict], fecha: date) -> Dia:
    dia = Dia(fecha=fecha.isoformat())
    lineas = _lineas(palabras)

    cuerpo: list[tuple[float, str]] = []
    for top, texto in lineas:
        if m := RE_NUTRICION.search(texto):
            dia.kcal = int(m.group(1))
        elif texto.startswith("Pan"):
            dia.pan = _plato(texto)
        else:
            cuerpo.append((top, texto))

    # El postre es la última línea, separada de los platos por un hueco mayor.
    if len(cuerpo) >= 2 and cuerpo[-1][0] - cuerpo[-2][0] > SALTO_BLOQUE:
        dia.postre = _plato(cuerpo.pop()[1])

    platos = [_plato(t) for t in _separar_platos([t for _, t in cuerpo])]
    if not platos and dia.postre is None:
        dia.festivo = True
    elif len(platos) == 1 and not dia.kcal and platos[0].nombre.isupper():
        # Celda con una sola palabra en mayúsculas, p. ej. "FIESTA".
        dia.festivo, dia.nota, platos = True, platos[0].nombre, []

    if platos:
        dia.primero = platos[0]
    if len(platos) > 1:
        dia.segundo = platos[1]
    dia.otros_platos = platos[2:]
    return dia


def leer_menu(ruta_pdf: str) -> dict:
    """Devuelve {"mes": "AAAA-MM", "titulo": ..., "dias": [Dia, ...]}."""
    with pdfplumber.open(ruta_pdf) as pdf:
        pagina = pdf.pages[0]
        palabras = pagina.extract_words(extra_attrs=["size"])

    # Título: "Octubre 2026 ..." (la letra más grande de la página).
    mayor = max(w["size"] for w in palabras)
    titulo = " ".join(w["text"] for w in palabras if w["size"] >= mayor - 0.5)
    m = re.search(r"([A-Za-zÁÉÍÓÚáéíóú]+)\s+(\d{4})", titulo)
    if not m or m.group(1).lower() not in MESES:
        raise ErrorDeFormato(f"No encuentro el mes en el título: {titulo!r}")
    mes, anio = MESES[m.group(1).lower()], int(m.group(2))

    # Cabecera de la tabla (Lunes ... Viernes) y líneas de "Kcal" de cada celda.
    cabecera = [w for w in palabras if w["text"] in ("Lunes", "Viernes")]
    kcal = [w for w in palabras if w["text"] == "Kcal"]
    if not cabecera or not kcal:
        raise ErrorDeFormato("No encuentro la cabecera de días o las líneas de Kcal")
    inicio_tabla = max(w["bottom"] for w in cabecera)

    columnas = _agrupar([w["x0"] for w in kcal], 20)  # borde izquierdo de cada columna
    filas = _agrupar([w["top"] for w in kcal], 5)  # línea Kcal = final de cada fila
    if len(columnas) != 5:
        raise ErrorDeFormato(f"Esperaba 5 columnas y encuentro {len(columnas)}")

    # Los números de día son las únicas palabras de tamaño ~9 que son solo dígitos.
    numeros = [
        w for w in palabras
        if w["text"].isdigit() and 8.5 <= w["size"] <= 10 and w["top"] > inicio_tabla
    ]

    dias: list[Dia] = []
    limites_x = [c - MARGEN_X for c in columnas] + [float("inf")]
    limites_y = [inicio_tabla] + [f + 2 for f in filas]
    for i in range(len(filas)):
        for j in range(5):
            def dentro(w):
                return (limites_x[j] <= w["x0"] < limites_x[j + 1]
                        and limites_y[i] < w["top"] <= limites_y[i + 1])

            numero = [w for w in numeros if dentro(w)]
            if not numero:
                continue  # celda vacía (días de otro mes)
            fecha = date(anio, mes, int(numero[0]["text"]))
            if fecha.weekday() != j:
                raise ErrorDeFormato(f"El día {fecha} no cae en la columna esperada")
            celda = [w for w in palabras if dentro(w) and w is not numero[0]]
            dias.append(_leer_celda(celda, fecha))

    if len(dias) < 15:
        raise ErrorDeFormato(f"Solo he encontrado {len(dias)} días")
    return {"mes": f"{anio}-{mes:02d}", "titulo": titulo, "dias": dias}


def a_json(menu: dict) -> dict:
    return {**menu, "dias": [asdict(d) for d in menu["dias"]]}


def desde_json(datos: dict) -> list[Dia]:
    def plato(p):
        return Plato(**p) if p else None

    return [
        Dia(**{
            **d,
            "primero": plato(d["primero"]),
            "segundo": plato(d["segundo"]),
            "postre": plato(d["postre"]),
            "pan": plato(d["pan"]),
            "otros_platos": [Plato(**p) for p in d["otros_platos"]],
        })
        for d in datos["dias"]
    ]
