# MI IPTV MUNDIAL

Este repositorio genera `lista.m3u` a partir del catálogo público de canales de IPTV-org.

## Actualización automática

GitHub Actions ejecuta `actualizar_lista.py` cada 3 horas (UTC). También se puede iniciar manualmente desde la pestaña **Actions**.

## Archivos

- `actualizar_lista.py`: descarga el catálogo y agrupa canales por país y categoría.
- `.github/workflows/actualizar.yml`: programa la ejecución automática.
- `lista.m3u`: archivo generado que usan los reproductores IPTV.

## Fuente y alcance

Fuente: https://iptv-org.github.io/iptv/index.m3u

La fuente contiene canales de televisión en directo. La disponibilidad y legalidad de cada canal dependen de sus titulares y de la ubicación del usuario. Este generador no incorpora películas individuales ni series bajo demanda, ni garantiza que cada enlace esté siempre disponible.

## Enlace público de la lista

Después de la primera ejecución correcta:

https://raw.githubusercontent.com/scorpiones1234567-art/mi-iptv-mundial/main/lista.m3u

## Activar GitHub Actions

En GitHub, abre **Actions** y habilita los flujos de trabajo si GitHub muestra el botón para hacerlo. El repositorio debe permitir que el flujo escriba contenido (`Settings > Actions > General > Workflow permissions > Read and write permissions`).
