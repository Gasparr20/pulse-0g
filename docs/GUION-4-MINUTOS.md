# Guion de la presentación — 4 minutos

Objetivo: que alguien que no sabe nada del proyecto entienda **qué hace** en los primeros 40 segundos, y que se acuerde de **una** cosa al salir: que el sistema tacha lo que no puede respaldar.

Duración objetivo: **4:10**. Tolerancia: hasta 4:30. Ensayar con reloj.

## Antes de empezar

- Abrir estas tres pestañas en el navegador, en este orden, y no tocar nada más:
  1. `localhost:3000/?at=30`
  2. `localhost:3000/?at=180`
  3. `localhost:3000/?tab=ask&q=¿Qué está pidiendo atención?&at=180&probe=1`
- Tener el video ya grabado a mano, por si la computadora falla.
- Zoom del navegador al 100 %. Nada de notificaciones.
- **Regla de oro: nunca muestres una pantalla que no vayas a tocar.**

---

## 0:00 – 0:25 · El problema

**Decís** (25 s, sin slides, mirando al jurado):

> "Un astronauta en Marte está a 22 minutos de la Tierra. Si se siente mal, no hay médico al lado y no puede hacer una video llamada. Tiene que decidir solo: *¿esto es normal para mí, tengo que hacer algo, o tengo que avisar a Tierra?*
> Ese es el problema que atacamos."

**No digas** "hicimos una app de salud". Es lo que van a decir los otros 30 equipos.

---

## 0:25 – 0:55 · Qué es, en una frase

**Mostrás** la pantalla de escritorio (la de `/?at=30`), sin hacer clic.

**Decís** (30 s):

> "Esto es Pulse-0G. El astronauta toca una zona de su cuerpo y ve tres cosas: si el valor es normal **para él**, qué tiene que hacer, y de dónde sale esa conclusión.
> No es un tablero de números. Es un tablero de decisiones."

**Señalás con el dedo o el cursor**, sin clic:
- La figura de la persona.
- La tabla con valor, base y banda.
- El reloj de misión arriba.

---

## 0:55 – 1:45 · La demostración que importa

**Clic** en `/?at=180`. La cabeza se pone roja.

**Decís** (50 s):

> "Este es un día tranquilo del mes 1: todo en verde. Y así se ve el mes 6.
> El sueño cayó a 2.9 horas. Pero lo importante no es el número: es **contra qué se compara**.
> Su base antes de despegar era 7.3 horas. Está **60 % por debajo de sí mismo**.
> Ese es el punto: no lo comparamos con una tabla general. Lo comparamos con su propia historia."

**Clic en la fila de horas de sueño** (se abre el detalle).

> "Y acá abajo está la serie completa, con los huecos. Cuatro noches sin registro se ven como un hueco, no como un cero."

**Señalás el bloque rojo**:

> "Y esta es la única cosa que tiene que hacer ahora. No un párrafo: una acción."

---

## 1:45 – 2:20 · Lo que el sistema se niega a hacer

**Clic** en la pestaña Consultar, pregunta `¿estoy deshidratado?` (o escribirla).

**Decís** (35 s):

> "Ahora, la parte que casi nadie muestra.
> Le preguntamos si está deshidratado. Miren la respuesta: *no puedo responder eso, y esa es la respuesta correcta*.
> El sistema no diagnostica. Puede mostrar el dato, el rango y la fuente. La interpretación es del médico de vuelo.
> Un software de salud que contesta cualquier cosa es más peligroso que uno que reconoce lo que no sabe."

---

## 2:20 – 2:55 · El verificador (el momento más fuerte)

**Clic** en "Autoprueba del verificador" (ya viene abierta con `?probe=1`).

**Decís** (35 s):

> "Y esto es lo que nos parece que hace único al proyecto.
> Cada frase que este programa muestra tiene que estar pegada a un dato. Después de responder, un control independiente relee el texto, busca todos los números y verifica que existan.
> Si no puede respaldar una frase, **la tacha en rojo, en pantalla**.
> Miren: acá hay frases de control. Estas tres las acepta. Estas tres las tacha, y dice por qué.
> Y le pasó al propio programa: cuando lo construimos, tachó siete frases escritas por nosotros. Un 9 que en realidad era 8,96."

**Pausa de dos segundos.** Este es el momento que el jurado tiene que recordar.

---

## 2:55 – 3:20 · De dónde sale todo

**Clic** en la pestaña Biblioteca.

**Decís** (25 s):

> "¿Y de dónde sale todo esto? De datos reales de NASA: los análisis de sangre y de orina de los cuatro tripulantes de la misión Inspiration4, publicados y de uso libre.
> Y de 25 fichas de respaldo. Cada una tiene la frase copiada textual del documento original, un resumen y el enlace.
> Los archivos reales tienen errores —faltantes escritos de tres maneras distintas, una columna sin nombre— y el programa **no los arregla en silencio**. Los declara."

**Señalás el buscador** y escribís "radiación" si hay tiempo. Filtra de 25 a 3.

---

## 3:20 – 3:40 · Cuando hay que avisar a Tierra

**Volvés** a `/?at=180` y **clic** en "Generar paquete".

**Decís** (20 s):

> "Cuando algo sale de banda, el sistema arma un informe para el médico de vuelo: qué se midió, qué regla se aplicó, qué datos faltan y qué anotó la tripulación.
> No envía nada. Y si esa función no se usa nunca, todo lo demás sigue funcionando igual."

---

## 3:40 – 4:10 · El cierre honesto

**Sacás la pantalla** o dejás el tablero limpio.

**Decís** (30 s):

> "Para cerrar, lo que **no** hace: no diagnostica, no predice, no inventa datos y no usa inteligencia artificial.
> Lo de la IA es a propósito. Podríamos haber puesto un chat. Pero si el objetivo es que no invente, un modelo de lenguaje es exactamente la herramienta equivocada. La IA, cuando esté, va a ser un traductor: agarra la conclusión que ya calculó el sistema y la escribe más claro. Nunca va a poner un número.
> Lo que ya está resuelto es lo difícil: que cada afirmación sobre una persona se pueda rastrear hasta su fuente."

**Última frase, mirando al jurado:**

> "Pulse-0G. No muestra números. Muestra decisiones, y muestra de dónde salen."

---

## Lo que hay que memorizar

Tres frases. Si te olvidás todo lo demás, decí estas:

1. **"No lo compara con una tabla general: lo compara con su propia historia."**
2. **"Si no puede respaldar una frase, la tacha en pantalla."**
3. **"No usa IA porque el objetivo es que no invente."**

## Las cinco preguntas que te van a hacer

| Pregunta | Respuesta corta |
|---|---|
| "¿Por qué no usan IA?" | "Porque el requisito es que no invente. Y la IA está diseñada como traductor, no como médico: nunca pone un número." |
| "¿De dónde sacaron los datos?" | "De dos estudios publicados por NASA de la misión Inspiration4, de uso libre. Y de un escenario simulado, claramente etiquetado como simulado." |
| "¿Esto sirve para un astronauta de verdad?" | "Sirve la capa de interpretación. Los sensores ya existen: Canadá tiene una camiseta, Europa tiene una app. Lo que faltaba es interpretar esos datos contra la base de cada persona." |
| "¿Y si el valor está mal medido?" | "El sistema marca la calidad de cada medición. Un valor con mala señal no debería disparar una alarma, y eso está en los datos." |
| "¿Cuántos son y cuánto tardaron?" | Contestá con la verdad. |

## Errores que hay que evitar

- **No leer las cifras de la pantalla.** El jurado las ve. Vos explicá qué significan.
- **No digas "revolucionario" ni "disruptivo".** Decí qué hace.
- **No digas "detecta enfermedades".** No lo hace, y es lo primero que un juez médico va a refutar.
- **No te disculpes por lo que falta.** Decilo como una decisión: "eso no está, y es a propósito".
- **Si algo falla en la demo**, no lo arregles en vivo más de 10 segundos. Pasá al video y seguí hablando.
