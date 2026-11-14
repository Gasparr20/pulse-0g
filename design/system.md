# Pulse-0G — sistema actual (sincronizado)

Fuente: `app/globals.css` y `design/pulse-0g-style/04-consola-animada.html`, que es la
dirección implementada. Todos los valores existen en ese archivo.

## Color

| Token | Valor | Uso |
| --- | --- | --- |
| `--bg` | `#0b0b0c` | Fondo de la aplicación |
| `--surface` | `#101012` | Encabezado, tarjetas, paneles |
| `--surface-2` | `#17171a` | Fila seleccionada, botones secundarios |
| `--hair` | `#26262a` | Separadores finos |
| `--hair-2` | `#3a3a3f` | Bordes de 2 px, chips, contornos |
| `--text` | `#ede9e2` | Texto principal y banda "en rango" |
| `--text-2` | `#8c877e` | Etiquetas y metadatos |
| `--dim` | `#55514a` | Sin medición, notas al pie |
| `--amber` | `#ffb020` | Banda de atención |
| `--red` | `#ff5347` | Banda de acción y bloque de alarma |
| `--nasa` | `#0b3d91` | Pantone 286 del emblema de NASA. **Solo identidad.** |
| `--nasa-hi` | `#3b7bd4` | Compañero claro del azul, porque el puro desaparece sobre negro |

Regla de color: **nominal no tiene color**. El color aparece solo cuando hay una
decisión que tomar. El azul es marca, nunca estado.

## Tipografía

| Rol | Valor | Uso |
| --- | --- | --- |
| `--mono` | `ui-monospace, "JetBrains Mono", "IBM Plex Mono", monospace` | Números, unidades, rótulos, metadatos |
| cuerpo | `system-ui, -apple-system, "Segoe UI", sans-serif` a `18px`/`1.5` | Texto y tabla |
| peso de rótulos | `800` | Todo rótulo en mayúsculas, tracking `.14em`–`.16em` |
| peso de tabla | `800` | Nombres de indicador y valores |
| peso de cifras | `800` mono, `tabular-nums` | Lectura alineada por columna |

Sin webfonts: el producto corre offline y no puede depender de una fuente remota.

## Espaciado, radio y sombra

| Token | Valor | Uso |
| --- | --- | --- |
| regla | `2px solid var(--hair-2)` | Bordes de tarjeta, tabla, chips |
| regla del encabezado | `3px solid var(--nasa-hi)` | Firma de identidad |
| radio | `0` | Todo. No hay esquinas redondeadas en el sistema |
| sombra | `6px 6px 0 #000` | **Solo** el bloque de alarma |
| padding de tarjeta | `16px 18px` | Interior de `.card` |

## Movimiento

Cuatro efectos, todos por debajo de 900 ms y ninguno en bucle:

| Efecto | Duración | Dónde |
| --- | --- | --- |
| contador del valor | 700 ms, easing cúbico | valor del indicador |
| serie que se dibuja | 900 ms, `stroke-dashoffset` | sparkline |
| tachado que se dibuja | 320 ms, `scaleX` | verificador de afirmaciones |
| destello de banda + entrada de alarma | 900 / 500 ms, una vez | figura y bloque de alarma |

Todo se apaga con `prefers-reduced-motion: reduce` y el estado final es idéntico al
estático. Ningún efecto aporta información nueva: solo revela la que ya está.
