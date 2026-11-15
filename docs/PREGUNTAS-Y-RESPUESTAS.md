# Preguntas que te pueden hacer, y cómo contestarlas

Análisis del programa terminado, para que puedas defenderlo sin saber el código de memoria.

---

## 1. Tu posición, en una frase

No hace falta que sepas qué hace cada función. Te alcanza con poder decir:

> "Sé qué hace el sistema, por qué lo hace así, y qué no hace. El código lo construí con agentes de IA, y el proyecto está diseñado para que eso sea auditable: el verificador tacha las frases mal respaldadas **aunque las haya escrito yo**."

Eso no es una debilidad. Es una respuesta mejor que "lo programé todo a mano", porque además es comprobable: la autoprueba del verificador está en la app.

## 2. El sistema en sesenta segundos

Cuatro capas. Si te piden que lo dibujes en una servilleta, es esto:

```
1. DATOS        archivos reales de NASA + escenario simulado
                 ↓  cada adaptador conserva los errores del archivo
2. BASE         10.995 mediciones con procedencia completa
                 (de dónde salió, de qué fila, con qué calidad)
                 ↓
3. REGLAS       cada límite necesita una ficha con la cita literal
                 (sin ficha → gris, "sin umbral citado")
                 ↓
4. RESPUESTA    ocho preguntas fijas + un control que tacha
                 lo que no puede respaldar
```

Lo importante de esa arquitectura: **las capas 1 y 3 son reemplazables**. Cambiar de dataset o agregar indicadores no toca el motor ni el verificador. Por eso el proyecto puede crecer sin reescribirse.

## 3. Las cifras que conviene tener de memoria

| Qué | Cuánto |
|---|---|
| Mediciones en la base | **10.995** (532 reales de un estudio, 8.888 del otro, 1.575 simuladas) |
| Fichas de evidencia | **25**, con la cita verificada palabra por palabra |
| Preguntas que responde | **8** + una abstención explícita |
| Umbrales con fuente citada | **3** de 6 indicadores |
| Endpoints | **4** |
| Tablas en la base | **7** + 1 vista |
| Suites de verificación | **3**, todas en verde |
| Líneas de código | ~**4.400** |

---

## 4. Las ocho preguntas más probables

| # | Pregunta | Respuesta de una línea |
|---|---|---|
| 1 | "¿Esto no es solo un frontend?" | "Hay una base con 10.995 mediciones, un motor de reglas y un verificador. Podés pedirle a la app que se autopruebe." |
| 2 | "¿Dónde está la IA?" | "No tiene, a propósito. El requisito era que no invente." |
| 3 | "¿Eso no es un RAG?" | "No. Es recuperación sobre fichas curadas, sin indexar papers enteros." |
| 4 | "¿Los datos son reales?" | "Dos estudios publicados por NASA con licencia libre. El escenario simulado está etiquetado como simulado." |
| 5 | "¿Quién validó los umbrales?" | "Tres tienen fuente citada; tres están marcados provisional en pantalla porque NASA no los publica." |
| 6 | "¿Qué pasa si se equivoca?" | "No diagnostica. Muestra el dato, la regla y la fuente; la interpretación es del médico." |
| 7 | "¿Funciona sin internet?" | "Sí. No hay una sola URL remota en el código." |
| 8 | "¿Por qué debería importarle a NASA?" | "Porque el problema no es medir: es interpretar contra la base de cada persona y poder rastrear de dónde sale cada conclusión." |

---

## 5. Preguntas por tema, con el detalle si insisten

### A. "¿Esto es solo una interfaz?"

**"¿Dónde está la base de datos?"**
> Son siete tablas en SQLite, con 10.995 filas. Cada medición guarda de qué archivo salió, de qué fila, de qué columna, con qué unidad y con qué banderas de calidad.
*Si insisten:* la base se construye desde los archivos originales con un script, y la aplicación la abre **en modo solo lectura**: nada en tiempo de ejecución puede alterar lo que registró una misión.

**"¿Qué hiciste en 48 horas?"**
> Un importador para dos estudios reales, un motor de bandas con citas, un verificador de afirmaciones con autoprueba, una bitácora que no admite edición, el paquete de caso, y 25 fichas con la cita verificada contra su documento.

**"¿Cuánto código es tuyo y cuánto de la IA?"**
> Todo el código lo escribí con agentes. Lo que es mío es el diseño: qué se guarda, qué regla necesita fuente, qué se rechaza. Un agente puede escribir una función; no puede decidir que un hueco no se rellena.

**"¿Por qué SQLite y no Postgres?"**
> Un solo proceso, sin servidor, y la base viaja en el repositorio ya construida. La demo no depende de que algo arranque.

### B. Inteligencia artificial

**"¿No tiene IA? Entonces no es innovador."**
> El desafío pide una herramienta que ayude a evaluar la salud con información confiable. Agregar un chat es lo que va a hacer todo el mundo. Lo difícil es que el sistema **no pueda inventar**, y eso se logra sin IA.

**"¿Esto no es un RAG?"**
> No. Un RAG indexa documentos enteros y deja que el modelo elija fragmentos. Acá hay 25 fichas curadas a mano, cada una con una cita textual y un enlace, y la recuperación es por etiquetas. Menos cobertura, cero invención.

**"¿Y si le agregás un modelo?"**
> Tendría tres reglas: no produce ningún número, no agrega afirmaciones nuevas, y el verificador corre **después** del modelo, sobre el texto final. El modelo sería un traductor, no un médico.

**"¿Cómo evitan que alucine?"**
> Cada frase de la respuesta cita un dato. El verificador relee el texto, extrae los números y los compara contra los valores citados. Lo que no coincide se tacha en pantalla con el motivo.

**"¿Y si el propio verificador está mal?"**
> Por eso tiene una autoprueba visible en la app: seis frases de control, tres que debe aceptar y tres que debe rechazar. Si falla una, el sistema miente sobre su propia fiabilidad y se ve.

### C. Los datos

**"¿De dónde salen?"**
> Dos estudios publicados por NASA del vuelo Inspiration4: panel metabólico en sangre y panel de inflamación en orina. Cuatro tripulantes, licencia libre.

**"¿Cuatro personas no es muy poco?"**
> Sí, y por eso no generalizamos. Lo usamos para probar fidelidad de ingesta y trazabilidad, no para inferir nada clínico. Está escrito en el producto.

**"¿Cómo sabés que las citas son correctas?"**
> Cada cita se buscó literalmente en el documento. En la última tanda verifiqué las 23 citas completas contra su página: 23 de 23.

**"¿Y si NASA cambia el documento?"**
> Hoy las fichas registran de dónde sale una afirmación, pero no qué versión se leyó. Falta guardar el archivo y hashearlo. Lo tenemos anotado como deuda.

**"¿Los datos son inventados?"**
> Hay dos orígenes y nunca se mezclan: el estudio real y un escenario simulado con semilla fija, etiquetado **SINTÉTICO** en cada serie. Sin el simulado no podríamos mostrar sueño, ánimo ni pulso, porque los estudios reales no los tienen.

### D. Validez y seguridad

**"¿Quién validó esos umbrales?"**
> Tres tienen fuente: sueño, radiación y temperatura. Los otros tres están marcados provisional en pantalla porque la NASA no publica umbral numérico para ellos, y lo dice explícitamente sobre los conductuales.

**"¿Por qué 38 °C de temperatura y no 37,5?"**
> Porque en la Estación Espacial la temperatura en reposo sube alrededor de un grado respecto de la base previa al vuelo. Con el umbral de 37,5 casi todos los tripulantes aparecerían con fiebre todos los días. Usamos 38 como techo citado y el desvío contra la base propia como criterio real.

**"¿Esto puede hacer daño si se usa mal?"**
> El sistema no diagnostica ni indica tratamiento: ante una banda roja dice "repetir la medición y notificar al médico de vuelo". Es una capa de trazabilidad, no de decisión clínica.

**"¿Qué pasa si un sensor mide mal?"**
> Cada medición lleva banderas de calidad. Un valor con mala señal no debería disparar una alarma, y eso está en los datos: el escenario incluye un artefacto etiquetado como sospechoso.

### E. Cómo funciona por dentro

**"¿Cómo funciona la banda de dos capas?"**
> El valor se compara contra dos cosas: el rango de referencia y la mediana de las mediciones previas al vuelo de esa persona. La segunda es la que detecta un cambio que el rango general no ve.

**"¿Cómo se dibuja un hueco?"**
> La serie se corta cuando falta un valor. No hay interpolación: un hueco es un hueco. Un gráfico completado miente con elegancia.

**"¿Cómo se tacha una frase?"**
> La frase se marca como no respaldada y una línea la atraviesa con una animación de 320 ms. Con movimiento reducido aparece directamente tachada.

**"¿Qué pasa si alguien edita un comentario?"**
> No puede. La bitácora está en una base aparte con reglas que rechazan edición y borrado, incluso si alguien lo intenta por SQL. Una corrección es una nota nueva que apunta a la anterior.

**"¿Cómo prueban que funciona?"**
> Tres suites automáticas: una prueba las ocho preguntas y la autoprueba del verificador; otra la bitácora y el paquete; la tercera la estructura de las fichas y que el umbral de la ficha coincida con el que usa el sistema.

### F. Producto y futuro

**"¿Cómo se conectarían sensores reales?"**
> El esquema de la base es el contrato. Un sensor nuevo escribe las mismas columnas que ya existen, y todo lo de arriba no se toca. Lo único específico es el adaptador, que es barato.

**"¿Por qué no una app móvil?"**
> Porque la demo tenía que funcionar sin red en cualquier computadora. Una web que corre local resuelve eso en un proceso.

**"¿Quién lo usaría?"**
> El tripulante para autoevaluarse y el médico de vuelo para recibir el paquete de caso. Los roles están previstos aunque el prototipo tenga un solo usuario.

### G. Preguntas trampa

**"¿Cuántos falsos positivos tiene?"**
> No medí eso, y por eso no lo afirmo. Lo que sí puedo mostrarte es que un valor con mala calidad de señal lleva su bandera, y que el sistema no dispara alarma sobre un hueco.

**"Tu verificador es trivial: solo compara números."**
> Sí, y esa es la idea. No es un juez clínico, es un control de consistencia. Un control simple que funciona vale más que uno complejo que nadie entiende.

**"La interfaz la hizo otra persona."**
> El diseño es parte del trabajo: hay cuatro direcciones documentadas, un sistema de diseño sincronizado y una implementada. La cuarta es la que está en el producto.

**"Esto ya existe."**
> Existen los sensores: Canadá tiene una camiseta que mide cardiograma y respiración, Europa tiene una app que junta cuestionarios y wearables. Lo que no existe es la capa que interpreta esos datos contra la base de cada persona y muestra de dónde sale cada conclusión.

**"¿Y el modelo de negocio?"**
> No es el objetivo del hackatón. Lo que sí está claro es el socio natural: el sistema no compite con los sensores, se enchufa arriba.

---

## 6. Cómo responder cuando no sabés

Esta es la respuesta más importante del documento.

**La fórmula:** *"No lo medí, y por eso no lo afirmo. Lo que sí sé es [lo que sí sabés]."*

Ejemplos:

- "¿Cuánta batería consume en un dispositivo real?" → *"No lo medí, no corrimos esto en hardware. Lo que sí está resuelto es que el sistema funciona sin red."*
- "¿Qué precisión tiene el algoritmo de pulso?" → *"No hay algoritmo de pulso: la frecuencia viene como dato, no se estima desde una onda. Por eso no puedo darte una precisión."*
- "¿Soporta a toda la tripulación?" → *"No está implementado. El modelo de datos lo soporta porque cada sujeto está identificado, pero la interfaz muestra un tripulante."*

Eso te posiciona mejor que inventar. Un equipo que dice "no lo medí" cuando no lo midió, y "esto sí" cuando sí, es un equipo creíble. Y es exactamente lo que hace el software.

## 7. Las tres frases para el cierre de cualquier respuesta

1. **"No muestra números: muestra decisiones."**
2. **"No confía en sí mismo: si no puede respaldar una frase, la tacha."**
3. **"No rellena huecos: si falta un dato, lo dice."**

Si te quedás sin tiempo o sin aire, esas tres resumen todo.
