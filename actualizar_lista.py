#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MI-IPTV-MUNDIAL: canales en directo + catalogo VOD legal.

Fuentes VOD:
- OnlineM3U/publicdomainm3u (peliculas y series de dominio publico).
- vod_manual.m3u (titulos manuales conservados del proyecto).

Genera:
- lista.m3u: canales + VOD
- canales.m3u: solo canales
- catalogo_vod.m3u: peliculas + series
- peliculas.m3u
- series.m3u
"""

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import os
import re
import sys

LIVE_SOURCE = "https://iptv-org.github.io/iptv/index.m3u"
MOVIES_SOURCE = "https://raw.githubusercontent.com/OnlineM3U/publicdomainm3u/main/movies.m3u"
SERIES_SOURCE = "https://raw.githubusercontent.com/OnlineM3U/publicdomainm3u/main/series.m3u"

OUTPUTS = {
    "all": Path("lista.m3u"),
    "live": Path("canales.m3u"),
    "vod": Path("catalogo_vod.m3u"),
    "movies": Path("peliculas.m3u"),
    "series": Path("series.m3u"),
}
MANUAL_VOD = Path("vod_manual.m3u")

COUNTRIES = {
    "MX": "México", "ES": "España", "AR": "Argentina", "CO": "Colombia",
    "CL": "Chile", "PE": "Perú", "VE": "Venezuela", "EC": "Ecuador",
    "BO": "Bolivia", "PY": "Paraguay", "UY": "Uruguay", "CR": "Costa Rica",
    "GT": "Guatemala", "HN": "Honduras", "SV": "El Salvador",
    "NI": "Nicaragua", "PA": "Panamá", "DO": "República Dominicana",
    "CU": "Cuba", "US": "Estados Unidos", "CA": "Canadá",
    "GB": "Reino Unido", "FR": "Francia", "DE": "Alemania",
    "IT": "Italia", "PT": "Portugal", "JP": "Japón", "KR": "Corea del Sur",
    "IN": "India", "TR": "Turquía", "BR": "Brasil", "CN": "China",
    "RU": "Rusia", "AU": "Australia", "NL": "Países Bajos",
    "BE": "Bélgica", "CH": "Suiza", "SE": "Suecia", "NO": "Noruega",
    "IE": "Irlanda", "PL": "Polonia", "GR": "Grecia", "IL": "Israel",
    "EG": "Egipto", "ZA": "Sudáfrica",
}


def download(url):
    request = Request(url, headers={"User-Agent": "MI-IPTV-MUNDIAL/3.0"})
    with urlopen(request, timeout=90) as response:
        return response.read().decode("utf-8-sig", errors="replace")


def get_attr(line, key):
    match = re.search(r'(?:^|\s)' + re.escape(key) + r'="([^"]*)"', line)
    return match.group(1).strip() if match else ""


def set_attr(line, key, value):
    pattern = r'((?:^|\s)' + re.escape(key) + r'=")[^"]*(")'
    if re.search(pattern, line):
        return re.sub(pattern, lambda m: m.group(1) + value + m.group(2), line, count=1)
    comma = line.find(",")
    if comma < 0:
        return line
    return line[:comma] + f' {key}="{value}"' + line[comma:]


def display_name(info):
    comma = info.find(",")
    return info[comma + 1:].strip() if comma >= 0 else info


def parse_m3u(raw):
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    entries = []
    i = 0
    while i < len(lines):
        if not lines[i].startswith("#EXTINF:"):
            i += 1
            continue
        info = lines[i]
        j = i + 1
        url = ""
        while j < len(lines):
            if lines[j].startswith("#EXTINF:"):
                break
            if lines[j].startswith(("http://", "https://")):
                url = lines[j]
                break
            j += 1
        if url:
            entries.append((info, url))
            i = j + 1
        else:
            i = max(j, i + 1)
    return entries


def country_label(value):
    codes = [part.strip().upper() for part in value.split(",") if part.strip()]
    if not codes:
        return "Internacional"
    names = []
    for code in codes[:3]:
        name = COUNTRIES.get(code, code)
        if name not in names:
            names.append(name)
    return " / ".join(names)


def prepare_live(entries):
    prepared = []
    seen = set()
    for info, url in entries:
        if url in seen:
            continue
        seen.add(url)
        country = country_label(get_attr(info, "tvg-country"))
        category = get_attr(info, "group-title") or "General"
        category = re.sub(r"\s+", " ", category).strip()[:70] or "General"
        info = set_attr(info, "group-title", f"{country} | {category}")
        prepared.append((country.casefold(), category.casefold(),
                         display_name(info).casefold(), info, url))
    prepared.sort(key=lambda item: (item[0], item[1], item[2]))
    return [(item[3], item[4]) for item in prepared]


def prepare_vod(entries, kind):
    prepared = []
    seen = set()
    for info, url in entries:
        if url in seen:
            continue
        seen.add(url)
        name = display_name(info)
        if kind == "movie":
            genre = get_attr(info, "group-title") or "Clásicos"
            genre = re.sub(r"\s+", " ", genre).strip()[:60] or "Clásicos"
            group = f"Movies: {genre}"
            info = set_attr(info, "tvg-type", "movie")
            info = set_attr(info, "group-title", group)
        else:
            show = get_attr(info, "group-title") or name.split(" - ")[0] or "Series clásicas"
            show = re.sub(r"\s+", " ", show).strip()[:70] or "Series clásicas"
            group = f"Series: {show}"
            info = set_attr(info, "tvg-type", "series")
            info = set_attr(info, "group-title", group)
        prepared.append((group.casefold(), name.casefold(), info, url))
    prepared.sort(key=lambda item: (item[0], item[1]))
    return [(item[2], item[3]) for item in prepared]


def write_m3u(path, entries):
    lines = ["#EXTM3U"]
    for info, url in entries:
        lines.extend((info, url))
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(temp, path)


def main():
    print("=== MI-IPTV-MUNDIAL 3.0 ===")
    print("Descargando canales en directo...")
    try:
        live_raw = download(LIVE_SOURCE)
        live_source_entries = parse_m3u(live_raw)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        print(f"No se pudo descargar la fuente de canales: {exc}", file=sys.stderr)
        print("No se modificó ninguna lista.", file=sys.stderr)
        return 1

    if not live_source_entries:
        print("La fuente de canales llegó vacía; se conservan las listas anteriores.", file=sys.stderr)
        return 2

    live = prepare_live(live_source_entries)
    movie_entries = []
    series_entries = []
    source_errors = []

    for url, kind, target in (
        (MOVIES_SOURCE, "movie", movie_entries),
        (SERIES_SOURCE, "series", series_entries),
    ):
        try:
            target.extend(parse_m3u(download(url)))
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            source_errors.append(f"{kind}: {exc}")

    # Agrega el catalogo manual anterior sin perderlo.
    if MANUAL_VOD.exists():
        try:
            movie_entries.extend(parse_m3u(MANUAL_VOD.read_text(encoding="utf-8-sig")))
        except OSError as exc:
            source_errors.append(f"catalogo manual: {exc}")

    movies = prepare_vod(movie_entries, "movie")
    series = prepare_vod(series_entries, "series")
    vod = movies + series

    if not vod:
        print("No se obtuvo VOD de ninguna fuente; no se modificaron las listas.", file=sys.stderr)
        return 3

    combined = live + vod

    try:
        write_m3u(OUTPUTS["live"], live)
        write_m3u(OUTPUTS["movies"], movies)
        write_m3u(OUTPUTS["series"], series)
        write_m3u(OUTPUTS["vod"], vod)
        write_m3u(OUTPUTS["all"], combined)
    except OSError as exc:
        print(f"Error guardando listas: {exc}", file=sys.stderr)
        return 4

    print(f"Canales: {len(live)}")
    print(f"Películas: {len(movies)}")
    print(f"Entradas de series: {len(series)}")
    print(f"Total en lista.m3u: {len(combined)}")
    if source_errors:
        print("Avisos de fuentes VOD:")
        for error in source_errors:
            print(f"- {error}")
    print("Listas generadas correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
