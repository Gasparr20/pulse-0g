# Pulse-0G — descripción completa del proyecto

Documento de referencia para presentaciones, jurados y para cualquiera que necesite entender qué es este proyecto sin leer el código.

---

## 1. En una frase

Un tablero de autoevaluación de salud para astronautas en misiones largas que muestra, para cada indicador, **el valor medido, la banda en la que cae, el desvío contra la base previa al vuelo del propio tripulante, la acción concreta a tomar y la fuente que respalda cada frase**.

## 2. El problema

En una misión a Marte, el astronauta no tiene un médico al lado y la comunicación con Tierra llega con hasta 22 minutos de retraso. Necesita poder responder solo tres preguntas:

1. ¿Este valor es normal **para mí**?
2. ¿Tengo que hacer algo ahora?
3. ¿Tengo que avisar a Tierra?

El programa de investigación humana de NASA mapeó cinco peligros del vuelo espacial —radiación, aislamiento y confinamiento, distancia a la Tierra, gravedad alterada y ambiente cerrado hostil— que producen pérdida de masa ósea, desacondicionamiento cardiovascular, cambios inmunitarios, alteraciones del sueño y del estado de ánimo. Los indicadores que el propio desafío propone medir son presión arterial, frecuencia cardíaca, glucemia, temperatura, horas de sueño y ánimo.

Un tablero que muestre esos números no resuelve nada. **La decisión es el producto, no la cifra.**

## 3. Qué hace el software

Tres pestañas, cada una con un trabajo distinto.

### Misión

El estado del tripulante en un momento dado de la misión, reproducible día a día con el **reloj de misión** (despegue, mes 1, mes 3, mes 4, mes 6, regreso +29 días).

- **Figura humana** con cinco zonas tocables: cabeza (sueño y ánimo), tórax (presión, frecuencia y temperatura), brazos (sitio de medición), piernas y ojos (sin instrumento a bordo).
- **Tabla de indicadores** con valor, base propia, desvío porcentual y banda.
- **Bloque de alarma**: cuando un valor sale de banda, la acción aparece en un bloque rojo con el valor y la base que la dispararon.
- **Calidad de datos**: cuatro cifras sobre lo que el importador encontró en los archivos originales y qué hizo con eso.
- **Paquete de caso**: un archivo con lo medido, las reglas aplicadas y la bitácora, para el médico de vuelo en Tierra.

### Biblioteca

Todo lo que el sistema puede mostrar como fuente, en un solo lugar y con búsqueda.

- **OSD-575** — panel metabólico de la misión Inspiration4: 4 tripulantes, 7 muestras por analito, 19 analitos, con los rangos de referencia que publica el propio archivo.
- **OSD-656** — panel de inflamación en orina del mismo vuelo: 4 tripulantes, 6 tiempos, 404 variables. Se describe, no se grafica: sus valores son NPQ normalizado, no concentraciones clínicas.
- **Biblioteca de evidencia** — 25 documentos curados, cada uno con su cita literal en inglés, un resumen en español, el enlace al documento y quién lo verificó.

### Consultar

Ocho consultas fijas sobre los datos, más una abstención explícita.

`series` · `alerts` · `baseline` · `missing` · `why` · `radiation` · `provenance` · `clinical_request`

Cada respuesta está construida con frases que **citan la fila de dato de la que salen**. Un verificador independiente vuelve a leer el texto renderizado y compara cada número impreso contra los valores citados. Si una frase no se puede anclar, o si imprime una cifra que no está en los datos, **se tacha en rojo en pantalla con el motivo**.

La consulta **"¿estoy deshidratado?"** devuelve una negativa explícita: el sistema no diagnostica. La consulta **"¿cuál es la capital de Francia?"** también: no está en el corpus.

## 4. Las tres cosas que lo diferencian

### 4.1 Bandas de dos capas

Un valor se compara contra dos cosas distintas:

1. **El rango de referencia** — poblacional, o el que publica el archivo de datos.
2. **La base propia del tripulante** — la mediana de sus registros previos al vuelo.

Un valor puede estar dentro del rango de población y aun así ser una señal de alarma para esa persona. Y al revés: en vuelo, hay indicadores donde **lo normal cambia**. La temperatura corporal central en reposo sube alrededor de **1,01 °C** en la Estación Espacial Internacional respecto de la medición previa al vuelo. Con ese corrimiento, casi cualquier tripulante quedaría por encima de un umbral poblacional de 37,5 °C todos los días. Por eso el sistema usa el techo de 38,0 °C solo como referencia absoluta, y deja que el desvío contra la base propia haga el trabajo real.

### 4.2 Verificador de afirmaciones visible

No es un chat. Es lo contrario: **cada frase tiene que poder rastrearse**.

- Toda oración cita un ancla: una fila de dato, un agregado o una tarjeta de evidencia.
- El verificador extrae los números del texto y los compara contra los valores del ancla, con tolerancia de redondeo y tratando los identificadores (`OSD-575`, `R+29`) como identificadores, no como cifras.
- Lo que no verifica, se tacha.

Cuando se construyó, **tachó siete frases escritas por el propio autor del sistema**: conteos sin ancla, un `9` que era `8,96`, un `11 %` que era `-11,13`. Eso es el argumento: el sistema no confía ni en su propio código.

Además, el verificador casi nunca rechaza nada en uso normal —las plantillas están escritas para anclar—, lo que volvería invisible lo más interesante. Por eso la pestaña de consultas incluye su **autoprueba**: seis frases de control, tres que debe aceptar y tres que debe rechazar, con el resultado a la vista.

### 4.3 Manejo honesto de los datos

Los archivos reales de NASA se ingieren **conservando sus defectos**:

| Defecto encontrado | Qué hace el sistema |
|---|---|
| `N/A`, `NA` y celda vacía conviviendo en el mismo archivo | Las tres se guardan como ausencia; convertir a cero falsearía cualquier promedio |
| Un analito sin rango de referencia en una muestra | Se muestra el valor y se declara "sin rango en el archivo" |
| Una muestra a 194 días del regreso que la narrativa del estudio no menciona | Se conserva y se marca la discrepancia |
| Dos columnas sin encabezado en el segundo estudio | Se rechazan y quedan en el log del importador; no se adivina qué contienen |
| Un estudio sin `R+194` que el otro sí tiene para los mismos cuatro tripulantes | Se registra la diferencia; no se armoniza |

Nada se corrige en silencio, y **un faltante nunca es un cero**.

## 5. Qué respalda los números

25 tarjetas de evidencia. **Cada cita fue verificada palabra por palabra contra su documento en vivo.** Si el enlace no lleva al pasaje exacto, la tarjeta no entra.

| Indicador | Umbral | Fuente |
|---|---|---|
| Sueño | restricción = menos de 6 h por 24 h | Página de riesgo de HRP, i=100 |
| Radiación | 620 mSv de límite de carrera al 3 % de REID | HRP Evidence Book, Tabla 4-1 |
| Temperatura | techo de 38,0 °C; +1,01 °C en vuelo | Stahn et al., *Scientific Reports* 2017 |

Presión arterial, frecuencia en reposo y estado de ánimo quedan marcados **provisional**: HRP no publica umbrales numéricos para ellos, y NASA declara que sus umbrales de salud conductual todavía deben normalizarse contra la población de astronautas. **Esa ausencia está documentada en una tarjeta en lugar de rellenarse con un número inventado.**

## 6. Qué NO hace

- No diagnostica, no predice enfermedades, no receta.
- No simula fisiología.
- No transmite nada: el paquete de caso se genera y se descarga, no se envía.
- No usa inteligencia artificial generativa. Todos los números salen de un motor determinístico.
- No generaliza: los estudios reales tienen cuatro tripulantes y entre seis y siete muestras puntuales.

## 7. Cómo está construido

| Capa | Tecnología | Decisión |
|---|---|---|
| Interfaz | Next.js 16, React 19, TypeScript | Un solo proceso, sin CDN ni fuentes remotas |
| Datos | SQLite (`node:sqlite`) | Base **de solo lectura** en runtime, sembrada en el build |
| Ingesta | Python, biblioteca estándar | Un adaptador por estudio, un esquema común |
| Bitácora | SQLite aparte | Append-only: triggers rechazan `UPDATE` y `DELETE` |
| Evidencia | JSON, un archivo por tarjeta | Leído en cada request: soltar un archivo cambia la pantalla |

**Funciona sin red.** No hay una sola URL remota en el código de la aplicación.

## 8. Verificación

Tres suites automáticas, todas en verde:

| Suite | Qué prueba |
|---|---|
| `check_answers.py` | Las nueve intenciones responden; ninguna frase queda tachada por error; el verificador **sí** rechaza las seis frases de control; el momento de la demo (FD180) también |
| `check_case.py` | La bitácora no admite edición ni borrado; el paquete lleva el hilo; las entradas inválidas se rechazan |
| `check_cards.py` | 25 tarjetas, 0 errores: estructura, cita primero, y coherencia entre el umbral de la tarjeta y el que usa el sistema |

## 9. Por qué estas decisiones

**Por qué nada de IA generativa.** El requisito del proyecto es información real, no inventada. Un generador de texto libre es la mayor fuente de invención posible: lo que se gana en fluidez se pierde en verificabilidad, y acá la verificabilidad **es** el producto. La IA está diseñada como capa futura, opcional y narradora (ver `docs/ARQUITECTURA-Y-CRECIMIENTO.md`).

**Por qué la base de evidencia es inmutable.** Nada en tiempo de ejecución puede alterar lo que registró una misión. Los comentarios operativos viven en un archivo aparte, append-only, porque son contexto y no evidencia.

**Por qué se muestran los huecos.** Un gráfico con un hueco dice la verdad; uno interpolado miente con elegancia.

**Por qué las tarjetas provisionales siguen visibles.** Si un umbral no tiene fuente, el sistema lo dice en pantalla. Es peor esconder la deuda que mostrarla.

## 10. Estado actual

| | |
|---|---|
| Datos | 10.995 mediciones: 532 de OSD-575, 8.888 de OSD-656, 1.575 del escenario sintético |
| Tarjetas | 25 · todas las citas verificadas literalmente |
| Umbrales citados | 3 de 6 indicadores (sueño, radiación, temperatura) |
| Consultas | 8 intenciones + abstención, con autoprueba del verificador |
| Interfaz | Tres pestañas, cinco zonas corporales, reloj de misión, animaciones con movimiento reducido |
| Diseño | Sistema sincronizado y cuatro láminas; la cuarta está implementada |

## 11. Glosario mínimo

- **Banda**: la clasificación de un valor en en rango / atención / acción / sin dato.
- **Base propia**: la mediana de las mediciones del tripulante antes del lanzamiento.
- **Ancla**: el dato o la tarjeta que respalda una frase de la respuesta.
- **Tarjeta de evidencia**: documento curado con una cita literal, un resumen y un enlace verificable.
- **Provisional**: banda cuyo umbral todavía no tiene una fuente citada.
- **Paquete de caso**: archivo con lo medido, las reglas y la bitácora, para el médico de vuelo.
- **REID**: riesgo de muerte inducida por exposición, la medida con la que NASA fija sus límites de radiación.
- **NPQ**: cuantificación normalizada de proteínas; sirve para comparar una proteína consigo misma, no como concentración clínica.
