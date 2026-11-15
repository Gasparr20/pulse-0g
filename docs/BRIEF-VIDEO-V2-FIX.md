# Corrección del video — Pulse-0G

## Veredicto

La mitad del video no se entiende, y no es un problema de ejecución: es de gramática. El video copió la estructura del video de referencia de NVIDIA (Nemotron), donde **un número gigante ES el producto**: tokens por segundo, 420 %, el más rápido. Ahí un `420.2` comunica todo.

Pulse-0G no vende un número. Vende una **decisión**: *este valor está fuera de banda para vos, y esto hay que hacer*. Aplicarle la gramática de un benchmark convierte una herramienta clínica en una nube abstracta con cifras sueltas.

El segundo video de referencia (`igexport-DfZ_P5soFaR`, el de MONOLITH) tiene justamente la gramática que falta: **seleccionar una fila, hacer zoom, y seguir esa fila a través de las pantallas**. Eso es lo que hay que combinar: la terminación del primero, la estructura del segundo.

Hay un corte de referencia con la estructura correcta en the storyboard cut (kept outside the repository) (27,9 s). No es motion design final: son capturas reales del producto con push-in lento, más el único bloque del video entregado que ya funciona. **El trabajo es llevar ese orden a la calidad del video original.**

## Qué se tira y qué se queda

| Tramo | Qué hay | Decisión |
|---|---|---|
| 0:00 – 0:11 | `INITIAL\|`, el lockup `( pulse ⬡ 0g )`, la nube naranja de puntos, `0.3 h`, `2.9 h` ×4, `1` gigante con `METRIC 1 // out of band`, `19 ANALYTES` con `osdr.ingest(...)` | **Se tira completo** |
| 0:12 – 0:19 | `CLAIM VERIFIER`, `EVERY CLAIM IS TRACED / OR STRUCK OUT` | **Se queda, se comprime y se agranda** |
| 0:19 – 0:23 | `PULSE-0G` cuatro veces | **Se deja una sola, al final** |

Por qué se tira el primer tramo:

- **La nube de puntos no significa nada.** Ocupa seis de los veintitrés segundos y se lee como una nebulosa o un mapa de calor. No hay cuerpo, no hay indicador, no hay decisión.
- **Los números no tienen objeto.** `2.9 h` sin la palabra "sueño" es un dato huérfano. `1 // out of band` es jerga interna. `19 ANALYTES` con `osdr.ingest("OSD-575")` es una línea de código: eso es la implementación, no el valor para el tripulante.
- **No aparece el producto.** Nunca se ve el mapa corporal, ni el toque, ni la banda de color, ni el desvío contra la base propia. Es lo único que hay que mostrar.
- **Todo es diminuto.** El panel del verificador ocupa un tercio del ancho del cuadro, con texto de 20 px, flotando en un campo negro enorme. En un teléfono eso es invisible.

## Estructura nueva (30 s)

| Tiempo | En pantalla | Qué se ve |
|---|---|---|
| 0:00 – 0:03 | `250 million miles.` / `No doctor.` | Negro. Nada más. |
| 0:03 – 0:08 | `Tap a body region.` | **Mapa corporal**, día 180. La cabeza en rojo. Punch-in al tocar. |
| 0:08 – 0:13 | `Your number. Your own baseline.` | **La tarjeta de sueño**: `2.9 h`, base `7.3`, `−60 %`, la serie con su hueco. |
| 0:13 – 0:19 | `Every claim is traced. Or struck out.` | El bloque del verificador, ya existente |
| 0:19 – 0:25 | `Out of range? Export a case file.` | **Paquete de caso**: identificador, reglas, la nota de la tripulación |
| 0:25 – 0:28 | `PULSE-0G` | Wordmark, una sola vez |

## Reglas de dirección

1. **Zoom de verdad.** El elemento que importa ocupa al menos el 60 % del cuadro. Si en un teléfono no se lee, no existe.
2. **Las leyendas van en su propia banda.** Nunca encima de la interfaz. En el corte de referencia ocupan los 140 px inferiores, con el fondo limpio.
3. **Todo número lleva su objeto.** `2.9 h de sueño`, no `2.9 h`. `−60 % contra tu propia base`, no `−60 %`.
4. **Cero código en pantalla.** Nada de `osdr.ingest()`, `// out of band`, `v_norm_baseline`. Eso es para el README, no para un jurado.
5. **Un solo logo.** Cuatro repeticiones de `PULSE-0G` al final gastan cuatro segundos y no suman.
6. **Del video de NVIDIA se conserva la terminación**: la retícula, el hexágono, la confianza tipográfica, las transiciones secas. Se descarta su gramática de benchmark.
7. **Del video de MONOLITH se toma la estructura**: seleccionar, hacer zoom, seguir el dato a través de las pantallas, terminar en el estado final.

## Lo que no se puede romper

- El rótulo `SINTÉTICO` del producto tiene que poder leerse cuando aparece la interfaz de la misión.
- No decir que diagnostica. No decir "IA que detecta".
- Los únicos números válidos son los del brief original: `2.9 h`, `−60 %`, `4.3 / 10`, `76 mSv`, `2` indicadores fuera de banda, `4` faltantes, `4` tripulantes, `7` muestras, `19` analitos.

## Entregable

Un corte nuevo de ≤30 s, 1920×1080 y 1080×1920, con el bloque del verificador mejorado (más grande, y con la frase tachada visible al menos un segundo). Comparalo contra the storyboard cut (kept outside the repository): la historia tiene que ser la misma, la terminación mucho mejor.
