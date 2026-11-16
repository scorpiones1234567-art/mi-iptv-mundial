# MI-IPTV-MUNDIAL

Proyecto que reúne canales gratuitos de televisión y un catálogo VOD de películas y series disponibles legalmente.

## Actualización automática

GitHub Actions ejecuta `actualizar_lista.py` cada 3 horas (UTC). También se puede iniciar manualmente desde **Actions**.

## Archivos generados

- `lista.m3u`: lista combinada de canales, películas y series.
- `canales.m3u`: solo televisión en directo.
- `catalogo_vod.m3u`: películas y series.
- `peliculas.m3u`: solo películas.
- `series.m3u`: solo series.
- `vod_manual.m3u`: títulos manuales conservados; no lo reemplaces por los archivos generados.
- `actualizar_lista.py`: generador de listas.
- `.github/workflows/actualizar.yml`: ejecución automática.

## Fuentes

- Canales: https://iptv-org.github.io/iptv/index.m3u
- Películas: https://github.com/OnlineM3U/publicdomainm3u
- Series: https://github.com/OnlineM3U/publicdomainm3u

La fuente VOD reúne títulos de dominio público o compartidos libremente, alojados por terceros como Internet Archive. No contiene necesariamente estrenos, doblaje latino, doblaje de España ni series coreanas. El idioma depende de cada título y de la pista disponible en el archivo.

## Enlaces públicos

- Lista completa: https://raw.githubusercontent.com/scorpiones1234567-art/mi-iptv-mundial/main/lista.m3u
- Solo canales: https://raw.githubusercontent.com/scorpiones1234567-art/mi-iptv-mundial/main/canales.m3u
- Catálogo VOD: https://raw.githubusercontent.com/scorpiones1234567-art/mi-iptv-mundial/main/catalogo_vod.m3u
- Películas: https://raw.githubusercontent.com/scorpiones1234567-art/mi-iptv-mundial/main/peliculas.m3u
- Series: https://raw.githubusercontent.com/scorpiones1234567-art/mi-iptv-mundial/main/series.m3u

## Compatibilidad VOD

Las entradas VOD se etiquetan con `tvg-type="movie"` o `tvg-type="series"` y grupos `Movies:` / `Series:` siguiendo una convención M3U pública. El reproductor debe reconocer esos atributos para mostrar apartados VOD; si no los reconoce, puede mostrar los títulos como canales normales.

## Activar permisos de Actions

En GitHub, abre **Settings > Actions > General > Workflow permissions** y selecciona **Read and write permissions**. Después entra a **Actions** y ejecuta manualmente `Actualizar MI IPTV MUNDIAL` una vez.

La actualización automática ocurre cada 3 horas (UTC), siempre que el flujo esté habilitado y las fuentes estén disponibles.
