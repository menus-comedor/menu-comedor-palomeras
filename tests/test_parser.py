"""Pruebas con el PDF real de octubre de 2026.

Si el colegio cambia la plantilla del PDF, añade el nuevo PDF a tests/pdf/
y una prueba parecida a estas.
"""

from pathlib import Path

from comedor.calendario import generar_ics
from comedor.categorias import categorias, categorias_dia
from comedor.parser import a_json, desde_json, leer_menu

PDF = Path(__file__).parent / "pdf" / "2026-10-orientativo.pdf"
MENU = leer_menu(str(PDF))
DIAS = {d.fecha: d for d in MENU["dias"]}


def test_mes_y_numero_de_dias():
    assert MENU["mes"] == "2026-10"
    assert len(MENU["dias"]) == 22  # 1 y 2, y de lunes a viernes del 5 al 30


def test_dia_normal():
    d = DIAS["2026-10-01"]
    assert d.primero.nombre == "Garbanzos guisados con calabaza"
    assert d.segundo.nombre == "Cinta lomo plancha con lechuga y zanahoria"
    assert d.segundo.alergenos == ["sulfitos"]
    assert d.postre.nombre == "Fruta de temporada"
    assert d.pan.nombre == "Pan integral"
    assert d.kcal == 758


def test_plato_en_varias_lineas_con_alergenos_partidos():
    d = DIAS["2026-10-14"]
    assert d.primero.nombre == "Sopa de cocido con fideos"
    assert d.primero.alergenos == ["gluten", "huevo", "soja", "mostaza", "sulfitos"]


def test_texto_cortado_en_el_pdf():
    # En el PDF falta el ")" final de los alérgenos de este plato.
    d = DIAS["2026-10-13"]
    assert d.segundo.nombre == "Boquerones en tempura con ensalada lechuga y maíz"
    assert "pescado" in d.segundo.alergenos


def test_festivo():
    d = DIAS["2026-10-12"]
    assert d.festivo and d.nota == "FIESTA" and not d.platos


def test_todos_los_dias_tienen_dos_platos():
    for d in MENU["dias"]:
        if not d.festivo:
            assert d.primero and d.segundo and not d.otros_platos, d.fecha


def test_ida_y_vuelta_json():
    assert desde_json(a_json(MENU)) == MENU["dias"]


def test_categorias():
    assert categorias("Merluza a la gallega con patata cocida") == ["pescado", "patata"]
    assert categorias("Espaguetis boloñesa con soja texturizada") == ["pasta"]
    assert categorias("Tortilla de queso con ensalada") == ["huevo"]
    assert categorias_dia(DIAS["2026-10-07"]) == ["carne", "patata", "huevo"]


def test_calendario():
    ics = generar_ics(MENU["dias"], "Comedor")
    assert ics.count("BEGIN:VEVENT") == 22
    assert all(len(l.encode()) <= 75 for l in ics.split("\r\n"))


def test_todos_los_pdf_de_prueba():
    # Cada PDF de tests/pdf (uno por menú) debe leerse con dos platos por día.
    for pdf in sorted(PDF.parent.glob("*.pdf")):
        menu = leer_menu(str(pdf))
        assert len(menu["dias"]) >= 15, pdf.name
        for d in menu["dias"]:
            if not d.festivo:
                assert d.primero and d.segundo and not d.otros_platos, (pdf.name, d.fecha)


def test_lista_de_menus():
    from comedor.menus import MENU_AVISOS, MENUS

    claves = [m[0] for m in MENUS]
    assert len(claves) == len(set(claves))
    assert MENU_AVISOS in claves
