# Pulse-0G explicado simple

Para cualquiera que no sepa programar ni medicina. Sin palabras técnicas.

---

## Qué es

Es **una planilla de control de salud para astronautas**, que el astronauta completa solo, y que además de mostrarle el número le dice tres cosas: si ese número es normal **para él**, qué tiene que hacer, y de dónde sale esa conclusión.

Pensalo así: cuando vas al médico y te toma la presión, te dice "140/90, estás alto". Pero alto comparado con qué. Comparado con una tabla general. El problema es que si vos siempre anduviste en 110/70, un 140 es un salto enorme. Y si siempre anduviste en 135, un 140 no es nada.

En una misión a Marte no hay médico que te diga nada. Y la respuesta de la Tierra tarda hasta 22 minutos. Entonces el astronauta necesita algo que le diga: **"esto es raro para vos"**, no "esto es raro en general".

## Qué hace

Tiene tres pantallas, cada una con un trabajo distinto.

### Pantalla 1: Cómo estás ahora

Hay un dibujo de una persona. El astronauta toca una zona y ve los números de esa parte del cuerpo.

- La **cabeza** muestra cuánto durmió y cómo está su ánimo.
- El **pecho** muestra presión, pulso y temperatura.
- Los **brazos** muestran cómo se toma la presión (dónde va el manguito, cuánto hay que descansar antes).
- Las **piernas** y los **ojos** están en gris y dicen "sin medición". Eso es a propósito: en esta demostración no hay instrumento para medirlos, y **no se inventa un número**.

Cada número viene con un color y una palabra. Y debajo, en una sola línea, qué hacer: *"revisar el ciclo de sueño con el médico de vuelo"*.

Arriba hay una línea de tiempo de la misión: despegue, mes 1, mes 3, mes 4, mes 6, y el regreso. Se puede volver atrás y ver cómo estaba la persona en cada momento. **Un día cualquiera todo está en verde. En el mes 6 el sueño se derrumba y la cabeza se pone en rojo.**

### Pantalla 2: De dónde sale todo

Es la biblioteca. Tiene dos cosas:

- Los **datos reales de NASA** de la misión Inspiration4: análisis de sangre y de orina de los cuatro tripulantes, publicados y de uso libre.
- Las **fichas de respaldo**: 25 documentos donde cada uno tiene una frase copiada textualmente del original, un resumen en castellano y el enlace para ir a leerlo.

Esas fichas son las que le permiten al programa decir de dónde sale cada afirmación. Si un límite no tiene ficha, el programa lo dice en pantalla: **"umbral provisional"**.

Y una parte linda: los archivos reales de NASA tienen errores. Valores faltantes escritos de tres maneras distintas, una columna sin nombre, una muestra que el estudio no menciona en su descripción. El programa **no los arregla en silencio**: los muestra como son y anota qué encontró. Un dato que falta se ve como un hueco, nunca como un cero.

### Pantalla 3: Preguntar

El astronauta escribe una pregunta en castellano y el programa responde.

Pero no es un chat cualquiera. Responde **nueve cosas y nada más**, y cada frase viene con la etiqueta que dice de dónde salió. Por ejemplo:

> **¿Cómo viene el sueño?**
> La serie tiene 194 muestras, 190 con valor. · El mínimo es 1.7 h y el máximo 9 h. · Hay 4 muestras sin valor y se muestran como huecos. · La base previa al vuelo es 7.3 y la última lectura es 2.9.
> *Cada frase, con su etiqueta de dónde sale.*

Y cuando le preguntás algo que no puede responder, **lo dice**:

> **¿Estoy deshidratado?**
> No puedo responder eso, y esa es la respuesta correcta. Un valor medido no equivale a un diagnóstico.

## Cómo lo hace: las tres ideas que importan

### 1. Compara contra vos, no contra la tabla

Cada valor se mide contra dos cosas: el rango normal de cualquier persona **y** el promedio de esa persona antes de despegar. Lo segundo es lo que casi nadie hace.

Ejemplo real, sacado de un paper: en la Estación Espacial, la temperatura corporal en reposo sube **un grado** comparada con la de antes del vuelo. Un grado. Si usás la tabla normal, donde 37,5 ya es fiebre, **todos los astronautas tienen fiebre todos los días**. El programa entonces no usa solo ese número: compara contra la temperatura propia de esa persona en vuelo, y reserva el 38 como techo absoluto.

### 2. No confía en sí mismo

Esta es la parte más rara y la más fuerte.

Cada frase que el programa muestra tiene que estar **pegada a un dato**. Después de armar la respuesta, un control independiente vuelve a leer el texto, busca todos los números y comprueba que cada uno exista realmente en los datos.

Si una frase no se puede respaldar, o si tiene un número que no está en los datos, **el programa la tacha en rojo, en la pantalla, delante del usuario**, y dice por qué.

Y le pasa al propio programa: cuando se lo construyó, tachó **siete frases escritas por quien lo hizo**. Un `9` que en realidad era `8,96`. Un `11 %` que era `-11`. Eso es lo que lo hace confiable: no se cree ni a sí mismo.

### 3. Si falta un dato, lo dice

Nunca completa un hueco con un número inventado. Nunca convierte un "no hay dato" en cero. Nunca interpola una línea entre dos mediciones para que el gráfico se vea lindo.

Un gráfico con un hueco dice la verdad. Un gráfico completado miente con elegancia.

## ¿Y la inteligencia artificial?

### Sin IA: funciona completo

Hoy el programa **no usa IA**, y eso es una decisión. Responde con nueve recetas fijas que consultan los datos. Nada queda librado a un modelo.

Por qué: lo más importante de este proyecto es que **no invente**. Un modelo de lenguaje es justamente una máquina de sonar convincente. Y además, en una nave —o en un hackatón con la notebook del evento— no podés depender de algo que a veces no arranca.

### Con IA: un traductor, no un médico

Si se le agrega IA, el rol es acotado y vale la pena entenderlo con una comparación:

- La IA **no es el médico**. El médico ya está: son los datos y las fichas de respaldo.
- La IA sería **el traductor**: agarra la conclusión que ya calculó el programa y la escribe más lindo, más natural, más fácil de leer.

Tres reglas que no se rompen:

1. La IA **nunca inventa un número**. Todos los números los pone el programa.
2. La IA **no agrega afirmaciones nuevas**. Solo redacta mejor lo que ya está respaldado.
3. El control de las frases corre **después** de la IA, sobre el texto final que el usuario va a leer.

Lo que se gana: preguntas más libres, respuestas más naturales. Lo que se pierde: la garantía de que la respuesta va a ser idéntica siempre. Por eso está pensada para estar **apagada por defecto**.

## Potencial

**Corto plazo.** Más fichas de respaldo: alcanza con leer y verificar documentos, no hay que programar nada nuevo. Cada indicador nuevo es una ficha más.

**Mediano plazo.** Conectar sensores de verdad. Y acá hay una buena noticia: **no hay que inventar ninguno**. Canadá ya tiene una camiseta que mide electrocardiograma, respiración, oxígeno y temperatura. Europa ya tiene una app que junta cuestionarios, nutrición, medicación y sensores. Lo que falta no es hardware: es la capa que **interpreta** esos datos contra la base de cada persona y muestra de dónde sale cada conclusión. Eso es lo que este proyecto propone.

**Largo plazo.** Que sirva para toda la tripulación, con permisos distintos para el astronauta y para el médico de Tierra. Y, mucho más adelante, formar parte de un sistema médico de verdad, que necesita validación clínica y certificación: cosas que un prototipo no puede fingir.

## Qué NO es

- No diagnostica enfermedades.
- No reemplaza al médico.
- No inventa datos.
- No simula el cuerpo humano.
- No manda información a ningún lado (el informe para el médico se genera y se descarga).

## Lo que hay que recordar de todo esto

Tres frases:

1. **No muestra números: muestra decisiones.**
2. **No confía en sí mismo: si no puede respaldar una frase, la tacha.**
3. **No rellena huecos: si falta un dato, lo dice.**
