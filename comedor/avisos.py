"""Mensajes de Telegram: resumen semanal y aviso del día siguiente."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import date, timedelta
from html import escape

from .categorias import categorias_dia, etiquetas

DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _fecha_corta(f: date) -> str:
    return f"{DIAS[f.weekday()]} {f.day}"


def _linea_dia(dia) -> str:
    f = date.fromisoformat(dia.fecha)
    if dia.festivo:
        return f"<b>{_fecha_corta(f)}</b> — 🎉 {escape(dia.nota or 'sin comedor')}"
    platos = "\n".join(f"   • {escape(p.nombre)}" for p in dia.platos)
    postre = f"\n   • <i>{escape(dia.postre.nombre)}</i>" if dia.postre else ""
    cats = categorias_dia(dia)
    resumen = f"\n   → {etiquetas(cats)}" if cats else ""
    return f"<b>{_fecha_corta(f)}</b>\n{platos}{postre}{resumen}"


def mensaje_semana(por_fecha: dict, lunes: date, url_web: str = "") -> str | None:
    semana = [lunes + timedelta(days=i) for i in range(5)]
    dias = [por_fecha[f.isoformat()] for f in semana if f.isoformat() in por_fecha]
    titulo = f"🍽 <b>Comedor: semana del {lunes.day} {MESES[lunes.month - 1]}</b>"
    if not dias:
        return (f"{titulo}\n\nTodavía no hay menú publicado para esta semana "
                f"(o no hay cole). Lo volveré a comprobar cada día.")
    cuerpo = "\n\n".join(_linea_dia(d) for d in dias)
    pie = f'\n\n<a href="{url_web}">Ver el menú completo</a>' if url_web else ""
    return f"{titulo}\n\n{cuerpo}{pie}"


def mensaje_dia(por_fecha: dict, fecha: date, cuando: str) -> str | None:
    dia = por_fecha.get(fecha.isoformat())
    if dia is None or dia.festivo:
        return None  # fin de semana, festivo o sin datos: no molestamos
    cats = categorias_dia(dia)
    evitar = f"\n\nPara la cena de {cuando}, mejor evitar: {etiquetas(cats)}" if cats else ""
    platos = "\n".join(f"• {escape(p.nombre)}" for p in dia.platos)
    postre = f"\n• <i>{escape(dia.postre.nombre)}</i>" if dia.postre else ""
    return f"🍽 <b>{cuando.capitalize()} ({_fecha_corta(fecha)}) en el comedor:</b>\n{platos}{postre}{evitar}"


def enviar_telegram(texto: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("(TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID no configurados: solo muestro el mensaje)\n")
        print(texto)
        return
    datos = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=datos, timeout=30) as r:
        respuesta = json.load(r)
    if not respuesta.get("ok"):
        raise RuntimeError(f"Telegram ha respondido con error: {respuesta}")
    print("Mensaje enviado a Telegram.")
