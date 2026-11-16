
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MI-IPTV-MUNDIAL
Descarga IPTV-org y genera lista.m3u
organizada por país y categoría.
"""

from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from pathlib import Path
from collections import defaultdict
import re
import sys
import os

SOURCE = "https://iptv-org.github.io/iptv/index.m3u"
OUTPUT = Path("lista.m3u")

COUNTRIES = {
    "MX": "México",
    "ES": "España",
    "AR": "Argentina",
    "CO": "Colombia",
    "CL": "Chile",
    "PE": "Perú",
    "VE": "Venezuela",
    "EC": "Ecuador",
    "BO": "Bolivia",
    "PY": "Paraguay",
    "UY": "Uruguay",
    "CR": "Costa Rica",
    "GT": "Guatemala",
    "HN": "Honduras",
    "SV": "El Salvador",
    "NI": "Nicaragua",
    "PA": "Panamá",
    "DO": "República Dominicana",
    "CU": "Cuba",
    "US": "Estados Unidos",
    "CA": "Canadá",
    "GB": "Reino Unido",
    "FR": "Francia",
    "DE": "Alemania",
    "IT": "Italia",
    "PT": "Portugal",
    "JP": "Japón",
    "KR": "Corea del Sur",
    "IN": "India",
    "TR": "Turquía",
    "BR": "Brasil",
    "CN": "China",
    "RU": "Rusia",
    "AU": "Australia",
    "NL": "Países Bajos",
    "BE": "Bélgica",
    "CH": "Suiza",
    "SE": "Suecia",
    "NO": "Noruega",
    "IE": "Irlanda",
    "PL": "Polonia",
    "GR": "Grecia",
    "IL": "Israel",
    "EG": "Egipto",
    "ZA": "Sudáfrica",
}

def attr(line, key):
    pattern = (
        r'(?:^|\s)'
        + re.escape(key)
        + r'="([^"]*)"'
    )
    match = re.search(pattern, line)
    return match.group(1).strip() if match else ""

def country_label(code):
    codes = [
        x.strip().upper()
        for x in code.split(",")
        if x.strip()
    ]

    if not codes:
        return "Internacional"

    names = []
    for c in codes[:3]:
        name = COUNTRIES.get(c, c)
        if name not in names:
            names.append(name)

    return " / ".join(names)

def update_group(line, group):
    if re.search(r'(?:^|\s)group-title="[^"]*"', line):
        return re.sub(
            r'((?:^|\s)group-title=")[^"]*(")',
            lambda m: m.group(1) + group + m.group(2),
            line,
            count=1
        )

    comma = line.find(",")
    if comma >= 0:
        return (
            line[:comma]
            + ' group-title="' + group + '"'
            + line[comma:]
        )

    return line

def download_playlist():
    req = Request(
        SOURCE,
        headers={
            "User-Agent": "MI-IPTV-MUNDIAL/2.0"
        }
    )

    with urlopen(req, timeout=90) as response:
        return response.read().decode(
            "utf-8-sig",
            errors="replace"
        )

def main():
    print("================================")
    print("     MI-IPTV-MUNDIAL")
    print("================================")
    print("Descargando canales...")

    try:
        raw = download_playlist()

    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        print(f"Error de descarga: {exc}", file=sys.stderr)
        return 1

    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip()
    ]

    entries = []
    seen = set()
    i = 0

    while i < len(lines):

        if not lines[i].startswith("#EXTINF:"):
            i += 1
            continue

        info = lines[i]
        j = i + 1
        url = ""

        while j < len(lines):
            current = lines[j]

            if current.startswith("#EXTINF:"):
                break

            if current.startswith(("http://", "https://")):
                url = current
                break

            j += 1

        if not url:
            i = j
            continue

        # Eliminar enlaces duplicados
        if url in seen:
            i = j + 1
            continue

        seen.add(url)

        # Obtener país y categoría
        country = country_label(
            attr(info, "tvg-country")
        )

        category = (
            attr(info, "group-title")
            or "General"
        )

        category = re.sub(
            r"\s+", " ", category
        ).strip()[:70] or "General"

        group = f"{country} | {category}"

        # Actualizar grupo en la información M3U
        info = update_group(info, group)

        entries.append((
            country.casefold(),
            category.casefold(),
            info.casefold(),
            info,
            url
        ))

        i = j + 1

    if not entries:
        print(
            "No se encontraron canales válidos."
            " Se conserva la lista anterior.",
            file=sys.stderr
        )
        return 2

    # Ordenar por país y categoría
    entries.sort(
        key=lambda x: (x[0], x[1], x[2])
    )

    output = ["#EXTM3U"]

    for _, _, _, info, url in entries:
        output.append(info)
        output.append(url)

    # Guardar de forma segura
    temp = OUTPUT.with_suffix(".tmp")

    try:
        temp.write_text(
            "\n".join(output) + "\n",
            encoding="utf-8"
        )
        os.replace(temp, OUTPUT)

    except OSError as exc:
        print(f"Error guardando lista: {exc}")
        return 3

    # Estadísticas
    countries = defaultdict(int)

    for country, _, _, _, _ in entries:
        countries[country] += 1

    print("--------------------------------")
    print(f"Canales encontrados: {len(entries)}")
    print(f"Países encontrados: {len(countries)}")
    print(f"Archivo generado: {OUTPUT}")
    print("--------------------------------")
    print("¡LISTA ACTUALIZADA!")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
