"""Genera un calendario .ics al que suscribirse desde el iPhone, Google Calendar, etc."""

from datetime import date, datetime, timedelta, timezone

from .categorias import categorias_dia, etiquetas


def _escapar(texto: str) -> str:
    return (texto.replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def _plegar(linea: str) -> str:
    """El formato iCalendar pide líneas de 75 bytes como máximo."""
    salida, actual = [], b""
    for caracter in linea:
        c = caracter.encode()
        if len(actual) + len(c) > (75 if not salida else 74):
            salida.append(actual.decode())
            actual = b""
        actual += c
    salida.append(actual.decode())
    return "\r\n ".join(salida)


def generar_ics(dias, nombre: str, clave: str = "orientativo", url_web: str = "") -> str:
    ahora = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lineas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//menu-comedor-palomeras//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escapar(nombre)}",
        "X-WR-TIMEZONE:Europe/Madrid",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]
    for dia in dias:
        fecha = date.fromisoformat(dia.fecha)
        if dia.festivo:
            resumen = f"🎉 {dia.nota or 'Sin comedor'}"
            descripcion = dia.nota or "Festivo"
        else:
            resumen = "🍽 " + " · ".join(p.nombre for p in dia.platos)
            partes = [f"1º {dia.primero.nombre}" if dia.primero else "",
                      f"2º {dia.segundo.nombre}" if dia.segundo else "",
                      *(p.nombre for p in dia.otros_platos),
                      f"Postre: {dia.postre.nombre}" if dia.postre else "",
                      f"Pan: {dia.pan.nombre}" if dia.pan else ""]
            if cats := categorias_dia(dia):
                partes += ["", "Para la cena, mejor evitar: " + etiquetas(cats)]
            if url_web:
                partes += ["", url_web]
            descripcion = "\n".join(p for p in partes if p is not None)
        lineas += [
            "BEGIN:VEVENT",
            f"UID:{fecha:%Y%m%d}-{clave}@menu-comedor-palomeras",
            f"DTSTAMP:{ahora}",
            f"DTSTART;VALUE=DATE:{fecha:%Y%m%d}",
            f"DTEND;VALUE=DATE:{fecha + timedelta(days=1):%Y%m%d}",
            f"SUMMARY:{_escapar(resumen)}",
            f"DESCRIPTION:{_escapar(descripcion.strip())}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lineas.append("END:VCALENDAR")
    return "\r\n".join(_plegar(l) for l in lineas) + "\r\n"
