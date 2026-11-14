# Brief para el agente de video — Pulse-0G

> Copiá todo lo que está debajo de la línea y pegálo como prompt inicial.
> Está escrito para un agente que no sabe nada del proyecto.

---

## CONTEXTO DEL PROYECTO

Vas a producir una pieza de **motion graphics** de aproximadamente **30 segundos** para **Pulse-0G**, un software de monitoreo de salud para astronautas en misiones largas. Es un prototipo funcional, no una maqueta: existe, corre local, y todo lo que se describe acá es observable en la aplicación.

El objetivo de esta pieza es **explorar cómo se vería** un video para el proyecto y sacar ideas de dirección. Todavía no es la entrega final, pero tiene que estar bien hecho: si funciona, se usa.

### Qué es Pulse-0G, en una frase

Un tablero donde el astronauta toca una zona de su cuerpo y ve el valor medido, la banda en la que cae, el desvío contra **su propia base previa al vuelo**, la acción concreta a tomar y la fuente que respalda cada afirmación.

### Las tres cosas que lo hacen distinto

1. **Bandas de dos capas.** No compara solo contra rangos de población: compara también contra la línea base del propio tripulante antes de despegar. Un valor puede ser normal para cualquiera y aun así ser una señal de alarma para esa persona.
2. **Verificador de afirmaciones visible.** Cada frase que el sistema muestra tiene que estar anclada a un dato o a una tarjeta de evidencia. Si una frase no se puede respaldar —o si imprime un número que no está en los datos— **se muestra tachada en rojo, en pantalla, con el motivo**. El sistema desconfía incluso de su propio código.
3. **Paquete de caso.** Cuando un valor sale de banda, se arma un archivo con lo medido, las reglas aplicadas, la calidad de los datos y las notas de la tripulación, para que el médico de vuelo lo lea en Tierra. No envía nada: si esa función no se usa nunca, todo lo demás funciona igual.

### Datos reales que usa

Análisis de sangre de la misión **Inspiration4**, publicados por NASA en el Open Science Data Repository (estudio `OSD-575`, licencia CC0). Son **4 tripulantes** y **7 muestras puntuales** por analito, tomadas antes y después del vuelo (`L-92`, `L-44`, `L-3`, `R+1`, `R+45`, `R+82`, `R+194`). El software los ingesta **conservando sus defectos reales**: `N/A`, `NA` y celdas vacías conviven en el archivo, hay columnas sin encabezado en otro estudio, y un valor no tiene rango de referencia. Nada de eso se "arregla": se declara.

Para la demostración de la interfaz se usa un **escenario sintético etiquetado como tal**, porque los datos reales no tienen pulso, sueño, ánimo ni presión arterial.

## REGLAS QUE EL VIDEO NO PUEDE VIOLAR

Estas son restricciones de honestidad del proyecto. Violarlas invalida la pieza.

- **No digas que el software diagnostica.** No diagnostica, no predice enfermedades, no receta.
- **No digas "IA que diagnostica"**, "detecta enfermedades", "predice riesgos de salud" ni nada equivalente.
- **No presentes los datos sintéticos como datos de NASA.** Si aparece la interfaz de la misión, el rótulo `SINTÉTICO` está visible en el producto y debe poder leerse.
- **No inventes métricas.** Los únicos números permitidos son los de la lista de más abajo.
- **No uses imágenes de stock de astronautas** genéricos, ni fotos de la NASA de personas, ni música con derechos.
- **No uses Blender ni renders 3D.** Esta pieza es motion graphics 2D sobre datos e interfaz.

La honestidad es parte del atractivo: el sistema se niega a responder cuando no tiene evidencia, y eso es una virtud, no una debilidad. Si el video muestra eso, gana.

## NÚMEROS PERMITIDOS (reales, del escenario de demostración)

| Dato | Valor |
|---|---|
| Horas de sueño en el día 180 de misión | **2.9 h** |
| Desvío contra su propia base | **−60 %** |
| Estado de ánimo | **4.3 / 10** (banda ámbar) |
| Dosis acumulada | **76 mSv** de un límite de 600 |
| Indicadores fuera de banda ese día | **2** |
| Muestras de sueño sin valor | **4** |
| Tripulantes en el estudio real OSD-575 | **4** |
| Muestras por analito en el estudio real | **7** |
| Analitos ingestados del estudio real | **19** |

Podés mostrar estos números. No agregues otros.

## STACK OBLIGATORIO

Usá los repositorios **`rea-video`**, **`hyperframes`** y **`earshot`** como pipeline de producción. Antes de escribir una línea, leé sus README y su documentación y confirmá qué hace cada uno y qué formato de entrada acepta. Si alguno no está disponible o no cubre lo que el guion pide, **decilo y proponé el reemplazo más simple**, no inventes APIs ni flags.

**No uses Blender.** No hace falta ningún 3D.

Si tenés acceso al repositorio del proyecto (`crewcheck`), usá las capturas reales de la aplicación. Si no lo tenés, replicá la interfaz a partir de la descripción visual de este brief y de los colores exactos: el resultado tiene que parecer el producto, no una interpretación libre.

## ESTRUCTURA NARRATIVA (6 bloques, 30 segundos)

Texto en pantalla **en inglés**, frases de 3 a 6 palabras. Nada de párrafos.

| Tiempo | En pantalla (EN) | Qué se ve |
|---|---|---|
| 0:00 – 0:03 | `250 million miles.` / `No doctor.` | Fondo casi negro. Una retícula técnica se dibuja. Silencio. |
| 0:03 – 0:08 | `Tap a body region.` | Se dibuja una silueta humana de línea fina. El cursor toca el tórax; el panel se abre con un valor. |
| 0:08 – 0:16 | `Your number.` / `Your own baseline.` | El número cuenta hasta `2.9 h`. Aparece `−60 %` y una marca de base. La zona de la cabeza pasa a rojo. |
| 0:16 – 0:23 | `Every claim is traced.` / `Or struck out.` | Una frase aparece en blanco y se tacha en rojo con un motivo. El tachado es el protagonista del plano. |
| 0:23 – 0:28 | `Out of range? Export a case file.` | Se arma un documento: líneas de texto monoespaciado, un identificador, una lista de reglas. |
| 0:28 – 0:30 | `Pulse-0G` | Wordmark sobre negro. Sin slogan. |

El bloque de 0:16 es el corazón de la pieza. Si hay que recortar, se recorta cualquier otro.

## SISTEMA VISUAL

Usá exactamente estos colores. Son los del producto.

```
fondo            #0A0E13
superficie       #121821
superficie 2     #182130
línea / borde    #1F2937
texto            #E5E7EB
texto secundario #94A3B8
verde (en rango) #34D399
ámbar (atención) #FBBF24
rojo (acción)    #F87171
sin dato         #4B5563
acento teal      #2DD4BF
acento violeta   #A78BFA
```

- **Números en tipografía monoespaciada** (JetBrains Mono, IBM Plex Mono o similar). El texto general, en una sans neutra (Inter o IBM Plex Sans). Si no hay esas fuentes disponibles, usá la monoespaciada del sistema para los números: el contraste entre mono y sans es parte de la identidad.
- Tono: **sala de control**, plano técnico, instrumental. Nada de degradados brillantes, nada de glassmorphism, nada de estilo publicitario.
- El color nunca va solo: siempre color **más** forma **más** texto. Es una decisión del producto (si la visión de un tripulante se altera, el color solo no alcanza).
- Movimiento: entradas por dibujo de trazo (`stroke-dashoffset`), números que cuentan, desplazamientos cortos con easing seco. **Sin rebotes, sin overshoot, sin zooms bruscos.** El metrónomo es de instrumento, no de reel.

## ENTREGABLES

1. **Master vertical 1080×1920, 30 fps, MP4 H.264, ≤30 s.** Es el formato para redes.
2. **Master horizontal 1920×1080** del mismo corte, misma duración.
3. **Tres stills 1080×1350** sacados de los planos más fuertes.
4. **Subtítulos en inglés** en un archivo `.srt` aparte, además del texto en pantalla.
5. **Los scripts y assets del proyecto** en una carpeta reproducible, con un README de una página que explique cómo se regenera el video.

Sin audio, o con un pulso muy tenue y libre de derechos. Si el pipeline de `earshot` resuelve audio, avisá qué propone antes de generarlo.

## CÓMO SABER SI SALIÓ BIEN

Una persona que no sabe nada del proyecto tiene que entender **qué hace Pulse-0G en los primeros 10 segundos**, sin leer nada más.

Y un segundo criterio, más importante: al terminar, tiene que quedar claro que **el sistema no inventa datos**. Si el video termina pareciendo un lujo de ciencia ficción, falló. Si termina pareciendo una herramienta seria que se niega a mentir, salió bien.

## QUÉ NECESITO DE VOS ANTES DE PRODUCIR

Respondeme en cinco líneas:

1. Qué hace exactamente cada uno de los tres repositorios y cuál es la división de trabajo entre ellos.
2. Si podés acceder al repositorio del producto o si vas a replicar la interfaz desde este brief.
3. Qué fuentes tipográficas tenés disponibles.
4. Cómo vas a resolver el plano del tachado (0:16), que es el más importante.
5. Qué necesitás de mí que no esté en este brief.

Después de esas respuestas, producí una primera versión vertical completa y mostrámela antes de hacer la horizontal.
