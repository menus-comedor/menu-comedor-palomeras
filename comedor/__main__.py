"""Uso:

    python -m comedor actualizar [--menu CLAVE] [--pdf RUTA]
                                     descarga los PDF, los lee y guarda datos/MENU/AAAA-MM.json
    python -m comedor publicar       genera la web y los calendarios en sitio/
    python -m comedor avisar [auto|semana|manana|hoy] [--fecha AAAA-MM-DD]

La lista de menús está en comedor/menus.py.

Variables de entorno (todas opcionales):
    MENU_AVISOS          menú del que se envían los avisos (por defecto "orientativo")
    MENUS_URL_BASE       carpeta donde el colegio publica los PDF
    NOMBRE_CALENDARIO    nombre del calendario (por defecto "Comedor Palomeras")
    URL_WEB              dirección de la web publicada, para enlazarla en los avisos
    TELEGRAM_CANAL       nombre del canal público de Telegram (sin @), para enlazarlo en la web
    TELEGRAM_BOT_TOKEN   token del bot (sin él, los avisos solo se muestran por pantalla)
    TELEGRAM_CHAT_ID     id del grupo o chat de Telegram
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from . import avisos
from .calendario import generar_ics
from .categorias import categorias_dia
from .menus import MENU_AVISOS, MENUS, url_pdf
from .parser import a_json, desde_json, leer_menu

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"
SITIO = RAIZ / "sitio"
WEB = RAIZ / "web"

NOMBRE = os.environ.get("NOMBRE_CALENDARIO") or "Comedor Palomeras"
URL_WEB = os.environ.get("URL_WEB", "")
CANAL = os.environ.get("TELEGRAM_CANAL", "").lstrip("@")
ZONA = ZoneInfo("Europe/Madrid")


def todos_los_dias(clave: str):
    dias = []
    for fichero in sorted((DATOS / clave).glob("*.json")):
        dias += desde_json(json.loads(fichero.read_text(encoding="utf-8")))
    return dias


def descargar(url: str, destino: Path) -> None:
    peticion = urllib.request.Request(url, headers={"User-Agent": "menu-comedor (GitHub Actions)"})
    with urllib.request.urlopen(peticion, timeout=60) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def actualizar_menu(clave: str, nombre: str, pdf: Path, avisar: bool) -> bool:
    """Lee un PDF y guarda el mes en datos/CLAVE/. Devuelve True si ha cambiado algo."""
    huella = hashlib.sha256(pdf.read_bytes()).hexdigest()
    menu = {**a_json(leer_menu(str(pdf))), "pdf_sha256": huella}

    carpeta = DATOS / clave
    carpeta.mkdir(parents=True, exist_ok=True)
    fichero = carpeta / f"{menu['mes']}.json"
    nuevo = not fichero.exists()
    # Comparamos el PDF y no los datos, para respetar las correcciones hechas a mano en datos/.
    if not nuevo and json.loads(fichero.read_text(encoding="utf-8")).get("pdf_sha256") == huella:
        print(f"  {nombre}: sin cambios en {menu['mes']}.")
        return False

    fichero.write_text(json.dumps(menu, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  {nombre}: {'nuevo' if nuevo else 'actualizado'} {fichero.relative_to(RAIZ)} "
          f"({len(menu['dias'])} días)")
    if nuevo and avisar and clave == MENU_AVISOS:
        enlace = f'\n<a href="{URL_WEB}">Ver el menú</a>' if URL_WEB else ""
        avisos.enviar_telegram(f"📅 Ya está publicado el menú del comedor de <b>{menu['titulo']}</b>.{enlace}")
    return True


def cmd_actualizar(args) -> None:
    menus = [m for m in MENUS if not args.menu or m[0] == args.menu]
    if not menus:
        sys.exit(f"No conozco el menú {args.menu!r}. Mira la lista en comedor/menus.py")
    if args.pdf and len(menus) != 1:
        sys.exit("Con --pdf hay que indicar también --menu")

    fallos = []
    with tempfile.TemporaryDirectory() as tmp:
        for clave, nombre, fichero in menus:
            try:
                pdf = Path(args.pdf) if args.pdf else Path(tmp) / fichero
                if not args.pdf:
                    descargar(url_pdf(fichero), pdf)
                actualizar_menu(clave, nombre, pdf, avisar=not args.sin_avisar)
            except Exception as e:  # un menú roto no debe impedir actualizar los demás
                print(f"  {nombre}: ERROR {e}")
                fallos.append(nombre)

    cmd_publicar(args)
    if fallos:
        # Fallamos al final para que GitHub avise por email, pero con la web ya publicada.
        sys.exit(f"No se han podido leer: {', '.join(fallos)}")


def cmd_publicar(_args) -> None:
    SITIO.mkdir(exist_ok=True)
    indice = []
    for clave, nombre, fichero in MENUS:
        dias = todos_los_dias(clave)
        if not dias:
            continue
        titulo = NOMBRE if clave == "orientativo" else f"{NOMBRE} · {nombre}"
        enlace = URL_WEB and (URL_WEB if clave == "orientativo" else f"{URL_WEB}?menu={clave}")
        (SITIO / f"{clave}.ics").write_bytes(generar_ics(dias, titulo, clave, enlace).encode("utf-8"))
        datos_web = a_json({"dias": dias})["dias"]
        for dia, d in zip(dias, datos_web):
            d["categorias"] = categorias_dia(dia)
        (SITIO / f"{clave}.json").write_text(
            json.dumps({"dias": datos_web}, ensure_ascii=False), encoding="utf-8")
        indice.append({"clave": clave, "nombre": nombre, "pdf": url_pdf(fichero),
                       "avisos": clave == MENU_AVISOS})

    # menu.ics es la dirección original del calendario: la mantenemos para quien ya esté suscrito.
    if (SITIO / "orientativo.ics").exists():
        shutil.copy(SITIO / "orientativo.ics", SITIO / "menu.ics")
    (SITIO / "menus.json").write_text(json.dumps({
        "nombre": NOMBRE,
        "telegram": f"https://t.me/{CANAL}" if CANAL else "",
        "menus": indice,
    }, ensure_ascii=False), encoding="utf-8")
    shutil.copy(WEB / "index.html", SITIO / "index.html")
    print(f"Web y calendarios generados en {SITIO.relative_to(RAIZ)}/ ({len(indice)} menús)")


def cmd_avisar(args) -> None:
    hoy = date.fromisoformat(args.fecha) if args.fecha else datetime.now(ZONA).date()
    por_fecha = {d.fecha: d for d in todos_los_dias(MENU_AVISOS)}
    modo = args.modo
    if modo == "auto":
        # Domingo: resumen de la semana. Lunes a jueves: aviso de mañana.
        modo = {6: "semana", 0: "manana", 1: "manana", 2: "manana", 3: "manana"}.get(hoy.weekday())
        if modo is None:
            print("Viernes o sábado: no hay aviso.")
            return

    if modo == "semana":
        lunes = hoy + timedelta(days=(7 - hoy.weekday()) % 7)  # el próximo lunes (u hoy si es lunes)
        texto = avisos.mensaje_semana(por_fecha, lunes, URL_WEB)
    elif modo == "manana":
        texto = avisos.mensaje_dia(por_fecha, hoy + timedelta(days=1), "mañana")
    else:
        texto = avisos.mensaje_dia(por_fecha, hoy, "hoy")

    if texto:
        avisos.enviar_telegram(texto)
    else:
        print("No hay comedor ese día: no se envía nada.")


def main() -> None:
    p = argparse.ArgumentParser(prog="python -m comedor", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="orden", required=True)

    a = sub.add_parser("actualizar", help="descarga y lee los PDF del mes")
    a.add_argument("--menu", help="actualizar solo este menú (p. ej. sin-huevo)")
    a.add_argument("--pdf", help="usar un PDF local en vez de descargarlo (con --menu)")
    a.add_argument("--sin-avisar", action="store_true", help="no avisar por Telegram del menú nuevo")
    a.set_defaults(func=cmd_actualizar)

    sub.add_parser("publicar", help="genera la web y los calendarios").set_defaults(func=cmd_publicar)

    v = sub.add_parser("avisar", help="envía el aviso por Telegram")
    v.add_argument("modo", nargs="?", default="auto", choices=["auto", "semana", "manana", "hoy"])
    v.add_argument("--fecha", help="hacer como si hoy fuera esta fecha (para probar)")
    v.set_defaults(func=cmd_avisar)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
