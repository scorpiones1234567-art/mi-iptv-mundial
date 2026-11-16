
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MI-IPTV-MUNDIAL 6.0
Canales + películas + series + RegioFlix + DE TODO.
"""

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import os
import re
import sys

# FUENTES
LIVE_SOURCE = "https://iptv-org.github.io/iptv/index.m3u"

MOVIES_SOURCE = (
    "https://raw.githubusercontent.com/OnlineM3U/"
    "publicdomainm3u/main/movies.m3u"
)

SERIES_SOURCE = (
    "https://raw.githubusercontent.com/OnlineM3U/"
    "publicdomainm3u/main/series.m3u"
)

DE_TODO_SOURCE = (
    "https://raw.githubusercontent.com/JMigue85/"
    "IPTV-SV/refs/heads/main/IPTVSV.m3u"
)

REGIOFLIX_SOURCE = os.environ.get("REGIOFLIX_URL", "")

# ARCHIVOS DE SALIDA
OUTPUTS = {
    "all": Path("lista.m3u"),
    "live": Path("canales.m3u"),
    "vod": Path("catalogo_vod.m3u"),
    "movies": Path("peliculas.m3u"),
    "series": Path("series.m3u"),
    "de_todo": Path("de_todo.m3u"),
}

MANUAL_VOD = Path("vod_manual.m3u")

COUNTRIES = {
    "MX": "México", "ES": "España", "AR": "Argentina",
    "CO": "Colombia", "CL": "Chile", "PE": "Perú",
    "VE": "Venezuela", "EC": "Ecuador", "BO": "Bolivia",
    "PY": "Paraguay", "UY": "Uruguay", "CR": "Costa Rica",
    "GT": "Guatemala", "HN": "Honduras", "SV": "El Salvador",
    "NI": "Nicaragua", "PA": "Panamá",
    "DO": "República Dominicana", "CU": "Cuba",
    "US": "Estados Unidos", "CA": "Canadá",
    "GB": "Reino Unido", "FR": "Francia", "DE": "Alemania",
    "IT": "Italia", "PT": "Portugal", "JP": "Japón",
    "KR": "Corea del Sur", "IN": "India", "TR": "Turquía",
    "BR": "Brasil", "CN": "China", "RU": "Rusia",
    "AU": "Australia", "NL": "Países Bajos",
    "BE": "Bélgica", "CH": "Suiza", "SE": "Suecia",
    "NO": "Noruega", "IE": "Irlanda", "PL": "Polonia",
    "GR": "Grecia", "IL": "Israel", "EG": "Egipto",
    "ZA": "Sudáfrica",
}


def download(url):
    request = Request(
        url,
        headers={"User-Agent": "MI-IPTV-MUNDIAL/6.0"}
    )

    with urlopen(request, timeout=90) as response:
        return response.read().decode(
            "utf-8-sig", errors="replace"
        )


def get_attr(line, key):
    match = re.search(
        r'(?:^|\s)' + re.escape(key) + r'="([^"]*)"',
        line
    )
    return match.group(1).strip() if match else ""


def set_attr(line, key, value):
    pattern = (
        r'((?:^|\s)' + re.escape(key) + r'=")[^"]*(")'
    )

    if re.search(pattern, line):
        return re.sub(
            pattern,
            lambda m: m.group(1) + value + m.group(2),
            line,
            count=1
        )

    comma = line.find(",")

    if comma < 0:
        return line

    return (
        line[:comma]
        + f' {key}="{value}"'
        + line[comma:]
    )


def display_name(info):
    comma = info.find(",")
    return info[comma + 1:].strip() if comma >= 0 else info


def parse_m3u(raw):
    lines = [
        line.strip()
        for line in raw.splitlines()
        if line.strip()
    ]

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
    codes = [
        part.strip().upper()
        for part in value.split(",")
        if part.strip()
    ]

    if not codes:
        return "Internacional"

    names = []

    for code in codes[:3]:
        name = COUNTRIES.get(code, code)

        if name not in names:
            names.append(name)

    return " / ".join(names)


def remove_duplicates(entries):
    result = []
    seen = set()

    for info, url in entries:
        if url in seen:
            continue

        seen.add(url)
        result.append((info, url))

    return result


def prepare_live(entries):
    prepared = []
    seen = set()

    for info, url in entries:
        if url in seen:
            continue

        seen.add(url)

        country = country_label(
            get_attr(info, "tvg-country")
        )

        category = (
            get_attr(info, "group-title") or "General"
        )

        category = re.sub(
            r"\s+", " ", category
        ).strip()[:70] or "General"

        info = set_attr(
            info,
            "group-title",
            f"{country} | {category}"
        )

        prepared.append((
            country.casefold(),
            category.casefold(),
            display_name(info).casefold(),
            info,
            url
        ))

    prepared.sort(
        key=lambda item: (item[0], item[1], item[2])
    )

    return [(item[3], item[4]) for item in prepared]


def is_series_entry(info, url=""):
    name = display_name(info).lower()
    group = get_attr(info, "group-title").lower()
    kind = get_attr(info, "tvg-type").lower()

    if kind in ("series", "serie", "tv"):
        return True

    if any(word in group for word in (
        "series", "serie", "doramas", "dramas",
        "temporada", "episodios"
    )):
        return True

    if re.search(r"\bS\d{1,2}E\d{1,2}\b", name, re.I):
        return True

    if re.search(r"\b\d{1,2}x\d{1,2}\b", name, re.I):
        return True

    return False


def split_regioflix(entries):
    movies = []
    series = []

    for info, url in entries:
        if is_series_entry(info, url):
            series.append((info, url))
        else:
            movies.append((info, url))

    return movies, series


def split_manual_vod(entries):
    movies = []
    series = []

    for info, url in entries:
        if is_series_entry(info, url):
            series.append((info, url))
        else:
            movies.append((info, url))

    return movies, series


def prepare_vod(entries, kind):
    prepared = []
    seen = set()

    for info, url in entries:
        if url in seen:
            continue

        seen.add(url)

        name = display_name(info)

        genre = (
            get_attr(info, "group-title")
            or (
                "Clásicos"
                if kind == "movie"
                else "Series clásicas"
            )
        )

        genre = re.sub(
            r"\s+", " ", genre
        ).strip()[:60]

        country = get_attr(info, "tvg-country").upper()
        lower_data = (
            name + " " + genre
        ).lower()

        if country == "KR" or any(word in lower_data for word in (
            "korea", "korean", "corea", "coreano",
            "k-drama", "doramas"
        )):
            genre = "Doramas coreanos"

        elif country == "CN" or any(word in lower_data for word in (
            "china", "chinese", "chino"
        )):
            genre = "Dramas chinos"

        elif country == "JP" or any(word in lower_data for word in (
            "japan", "japanese", "japón", "japones"
        )):
            genre = "Series japonesas"

        if kind == "movie":
            group = f"Movies: {genre or 'Clásicos'}"
            info = set_attr(info, "tvg-type", "movie")
        else:
            group = f"Series: {genre or 'Series clásicas'}"
            info = set_attr(info, "tvg-type", "series")

        info = set_attr(info, "group-title", group)

        prepared.append((
            group.casefold(),
            name.casefold(),
            info,
            url
        ))

    prepared.sort(
        key=lambda item: (item[0], item[1])
    )

    return [(item[2], item[3]) for item in prepared]


def prepare_de_todo(entries):
    prepared = []
    seen = set()

    for info, url in entries:
        if url in seen:
            continue

        seen.add(url)

        info = set_attr(
            info,
            "group-title",
            "DE TODO"
        )

        prepared.append((info, url))

    return prepared


def write_m3u(path, entries):
    lines = ["#EXTM3U"]

    for info, url in entries:
        lines.extend((info, url))

    temp = path.with_suffix(path.suffix + ".tmp")

    temp.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    os.replace(temp, path)


def main():
    print("=== MI-IPTV-MUNDIAL 6.0 ===")

    source_errors = []

    # CANALES
    print("Descargando canales...")

    try:
        live_raw = download(LIVE_SOURCE)
        live_source_entries = parse_m3u(live_raw)

    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        print(f"Error canales: {exc}", file=sys.stderr)
        return 1

    if not live_source_entries:
        print("Canales vacíos. Se conservan listas anteriores.")
        return 2

    live = prepare_live(live_source_entries)

    # PELÍCULAS Y SERIES
    movie_entries = []
    series_entries = []

    sources = (
        (MOVIES_SOURCE, "movie", movie_entries),
        (SERIES_SOURCE, "series", series_entries),
    )

    for url, kind, target in sources:
        try:
            print(f"Descargando {kind}...")
            target.extend(parse_m3u(download(url)))

        except (
            HTTPError, URLError, TimeoutError, OSError
        ) as exc:
            source_errors.append(f"{kind}: {exc}")

    # REGIOFLIX
    if REGIOFLIX_SOURCE:
        try:
            print("Descargando RegioFlix...")

            regio_entries = parse_m3u(
                download(REGIOFLIX_SOURCE)
            )

            regio_movies, regio_series = split_regioflix(
                regio_entries
            )

            movie_entries.extend(regio_movies)
            series_entries.extend(regio_series)

            print(f"RegioFlix películas: {len(regio_movies)}")
            print(f"RegioFlix series: {len(regio_series)}")

        except (
            HTTPError, URLError, TimeoutError, OSError
        ) as exc:
            source_errors.append(f"RegioFlix: {exc}")

    # CATÁLOGO MANUAL
    if MANUAL_VOD.exists():
        try:
            print("Leyendo catálogo manual...")

            manual_entries = parse_m3u(
                MANUAL_VOD.read_text(
                    encoding="utf-8-sig"
                )
            )

            manual_movies, manual_series = split_manual_vod(
                manual_entries
            )

            movie_entries.extend(manual_movies)
            series_entries.extend(manual_series)

        except (OSError, UnicodeError) as exc:
            source_errors.append(f"Manual: {exc}")

    # DE TODO
    de_todo = []

    try:
        print("Descargando lista DE TODO...")

        de_todo_entries = parse_m3u(
            download(DE_TODO_SOURCE)
        )

        if not de_todo_entries:
            raise ValueError("La lista no contiene entradas M3U válidas")

        de_todo = prepare_de_todo(de_todo_entries)

        print(f"Entradas DE TODO: {len(de_todo)}")

    except (
        HTTPError, URLError, TimeoutError, OSError, ValueError
    ) as exc:
        source_errors.append(f"DE TODO: {exc}")

        # Si la descarga falla, conservar el archivo anterior.
        if OUTPUTS["de_todo"].exists():
            try:
                de_todo = parse_m3u(
                    OUTPUTS["de_todo"].read_text(
                        encoding="utf-8-sig"
                    )
                )
            except (OSError, UnicodeError):
                de_todo = []

    # PREPARAR CATÁLOGOS
    movies = prepare_vod(movie_entries, "movie")
    series = prepare_vod(series_entries, "series")
    vod = movies + series

    # EVITAR DUPLICADOS EN LA LISTA GENERAL
    combined = remove_duplicates(
        live + vod + de_todo
    )

    # GUARDAR ARCHIVOS
    try:
        write_m3u(OUTPUTS["live"], live)
        write_m3u(OUTPUTS["movies"], movies)
        write_m3u(OUTPUTS["series"], series)
        write_m3u(OUTPUTS["vod"], vod)
        write_m3u(OUTPUTS["de_todo"], de_todo)
        write_m3u(OUTPUTS["all"], combined)

    except OSError as exc:
        print(f"Error guardando listas: {exc}")
        return 4

    # RESULTADOS
    print("\n=== RESULTADOS MI IPTV MUNDIAL ===")
    print(f"Canales: {len(live)}")
    print(f"Películas: {len(movies)}")
    print(f"Series: {len(series)}")
    print(f"DE TODO: {len(de_todo)}")
    print(f"Total lista general: {len(combined)}")

    if source_errors:
        print("\nAvisos:")

        for error in source_errors:
            print("-", error)

    print("\nListas generadas correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
