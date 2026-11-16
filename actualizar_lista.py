#!/usr/bin/env python3
"""Descarga IPTV-org y genera lista.m3u agrupada por país y categoría."""
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from pathlib import Path
from collections import defaultdict
import re
import sys

SOURCE = "https://iptv-org.github.io/iptv/index.m3u"
OUTPUT = Path("lista.m3u")
COUNTRIES = {
    "MX": "México", "ES": "España", "AR": "Argentina", "CO": "Colombia",
    "CL": "Chile", "PE": "Perú", "VE": "Venezuela", "EC": "Ecuador",
    "BO": "Bolivia", "PY": "Paraguay", "UY": "Uruguay", "CR": "Costa Rica",
    "GT": "Guatemala", "HN": "Honduras", "SV": "El Salvador",
    "NI": "Nicaragua", "PA": "Panamá", "DO": "República Dominicana",
    "CU": "Cuba", "US": "Estados Unidos", "CA": "Canadá",
    "GB": "Reino Unido", "FR": "Francia", "DE": "Alemania",
    "IT": "Italia", "PT": "Portugal", "JP": "Japón", "KR": "Corea del Sur",
    "IN": "India", "TR": "Turquía", "BR": "Brasil",
}

def attr(line, key):
    match = re.search(r'(?:^|\s)' + re.escape(key) + r'="([^"]*)"', line)
    return match.group(1).strip() if match else ""

def country_label(code):
    codes = [x.strip().upper() for x in code.split(",") if x.strip()]
    if not codes:
        return "Internacional"
    return " / ".join(COUNTRIES.get(c, c) for c in codes[:2])

def main():
    req = Request(SOURCE, headers={"User-Agent": "MI-IPTV-MUNDIAL/1.0"})
    try:
        with urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8-sig", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"No se pudo descargar la fuente: {exc}", file=sys.stderr)
        return 1

    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF:"):
            url = ""
            j = i + 1
            while j < len(lines):
                if lines[j].startswith("#EXTINF:"):
                    break
                if lines[j].startswith("http://") or lines[j].startswith("https://"):
                    url = lines[j]
                    break
                j += 1
            if url:
                country = country_label(attr(line, "tvg-country"))
                category = attr(line, "group-title") or "General"
                # Evita etiquetas vacías y limita nombres excesivamente largos.
                category = re.sub(r"\s+", " ", category).strip()[:70] or "General"
                group = f"{country} | {category}"
                # Reemplaza group-title para que el reproductor muestre el país primero.
                if re.search(r'(?:^|\s)group-title="[^"]*"', line):
                    line = re.sub(r'((?:^|\s)group-title=")[^"]*(")', rf'\g<1>{group}\2', line, count=1)
                else:
                    comma = line.find(",")
                    if comma >= 0:
                        line = line[:comma] + f' group-title="{group}"' + line[comma:]
                    else:
                        line = line + f' group-title="{group}"'
                entries.append((group.casefold(), line, url))
            i = j
        i += 1

    if not entries:
        print("La fuente respondió, pero no se encontraron canales. No se modificó lista.m3u.", file=sys.stderr)
        return 2

    entries.sort(key=lambda item: (item[0], item[1].casefold()))
    output = ["#EXTM3U"]
    for _, info, url in entries:
        output.extend([info, url])

    OUTPUT.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"Lista actualizada: {len(entries)} canales en {OUTPUT}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
