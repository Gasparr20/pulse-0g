# Pulse-0G — sistema actual (sincronizado)

Fuente única: `app/globals.css`. Todos los valores de esta tabla existen en ese archivo.
Es el sistema de la aplicación en producción, no una propuesta.

## Color

| Token | Valor | Uso |
| --- | --- | --- |
| `--bg` | `#0a0e13` | Fondo de la aplicación |
| `--surface` | `#121821` | Encabezado, tarjetas, paneles |
| `--surface-2` | `#182130` | Sólidos, medidor, botones secundarios |
| `--hair` | `#1f2937` | Bordes, separadores, hairlines |
| `--text` | `#e5e7eb` | Texto principal |
| `--text-2` | `#94a3b8` | Etiquetas, metadatos, texto secundario |
| `--green` | `#34d399` | Banda en rango |
| `--amber` | `#fbbf24` | Banda de atención |
| `--red` | `#f87171` | Banda de acción |
| `--nodata` | `#4b5563` | Sin medición o sin umbral |
| `--teal` | `#2dd4bf` | Acento estructural, pestaña activa |
| `--violet` | `#a78bfa` | Hazard de radiación, rótulo sintético |
| `--blue` | `#60a5fa` | Hazard de aislamiento |
| `--orange` | `#fb923c` | Hazard de ambiente |

## Tipografía

| Token | Valor | Uso |
| --- | --- | --- |
| `--mono` | `ui-monospace, "JetBrains Mono", "IBM Plex Mono", monospace` | Números, unidades, metadatos, rótulos |
| cuerpo | `Inter, "IBM Plex Sans", system-ui, -apple-system, sans-serif` | Texto, títulos |
| cuerpo tamaño | `15px` / `line-height: 1.5` | Base |

## Espaciado y radio

| Token | Valor | Uso |
| --- | --- | --- |
| separación de tarjetas | `12px` | Entre tarjetas del panel |
| padding de tarjeta | `14px 16px` | Interior de `.card` |
| radio | `8px` | `.card` |
| radio pequeño | `4px` / `3px` | Chips y pills |
| hairline | `1px solid var(--hair)` | Separadores |

## Reglas de componente

- `.card`: borde hairline, superficie, radio 8, sin sombra. Nunca anidada dentro de otra tarjeta.
- `.dot`: punto de 9 px que acompaña siempre a un rótulo de banda. El color nunca va solo.
- `.pill`: mono, 10 px, mayúsculas, tracking 0.06em, borde hairline. Se usa solo para estado reconocible.
- `.clock-step`: mono, 11 px, borde hairline; el paso activo invierte a fondo teal con texto oscuro.
- Escala numérica: valor `26px` mono 600; metadatos `11.5px` mono.
