# Preguntas para mostrar la diferencia entre con IA y sin IA

Cómo prender el modo: el botón **IA LOCAL** en la pestaña Consultar, o agregar `&ai=1` a la URL.
`localhost:3000/?tab=ask&q=¿Cómo viene el sueño?&at=180&ai=1`

Todo lo de abajo se probó contra el modelo local `qwen2.5:7b` el 2026-11-15. Las respuestas están copiadas de la salida real.

---

## El orden recomendado para la demo

### 1 · Para mostrar qué gana la IA

**`¿Cómo viene el sueño?`**

| Sin IA | Con IA |
|---|---|
| La serie de Horas de sueño tiene 194 muestras, 190 con valor. · El mínimo registrado es 1.7 h y el máximo 9 h. · Hay 4 muestras sin valor, y se muestran como huecos en la serie. · La base previa al vuelo es 7.3 y la última lectura es 2.9. | *"Las horas de sueño varían mucho, desde 1.7 hasta 9 horas. Faltan algunas lecturas, lo que hace difícil ver una tendencia clara. La persona duerme menos que antes del vuelo."* |

**Qué decir:** *"La versión sin IA son cuatro datos correctos. La versión con IA es la misma información contada como se la contarías a alguien. Y fijate que no apareció ninguna cifra nueva."*

---

### 2 · Para mostrar que el motor también aprende

**`¿Cómo va la dosis de radiación?`**

| Sin IA | Con IA |
|---|---|
| La dosis acumulada es 76 mSv. · El límite configurado es 620 mSv. · La acumulada no se reinicia. | *"La dosis actual es 76 mSv. Quedan 544 mSv antes de alcanzar el límite configurado. La dosis no se reinicia, así que cualquier exposición adicional se suma."* |

**Qué decir, y esta es la mejor historia del modo IA:**

> *"La primera vez que le preguntamos esto, el modelo contestó 'faltan 544 mSv'. Y el sistema lo tachó: 544 no estaba en los datos. El modelo tenía razón —620 menos 76— pero el número no existía en la respuesta del motor. Así que arreglamos el motor: ahora calcula el margen y lo ancla. El modelo encontró un agujero en nuestro propio diseño."*

Eso muestra el ciclo completo: el modelo no decide, pero **señala** lo que falta, y el motor lo incorpora con su fuente.

---

### 3 · Para mostrar que la IA no cambia las reglas de seguridad

**`¿Estoy deshidratado?`**

Con IA encendida responde **exactamente lo mismo**:

> *"Un valor medido no equivale a un diagnóstico, y este software no tiene la información necesaria para sostener uno."*

**Qué decir:** *"El modelo ni siquiera interviene acá. La abstención la decide el motor, y prender la IA no la cambia. Eso es lo importante: el modo más poderoso no puede desactivar el límite."*

---

### 4 · Opcional, si querés mostrar cuándo el sistema descarta al modelo

**`¿Cómo cambió la presión respecto a mi base?`**

| Sin IA | Con IA |
|---|---|
| Presión sistólica: 121.9 contra una base de 110.6, 10 % por encima de tu propio registro previo al vuelo. | *"La presión arterial subió un poco, llegando a 121.9 contra 110.6 en tu base. Eso es 10 % más alto que antes del vuelo. Es importante seguir monitoreándolo."* |

Fijate en la última oración: **"es importante seguir monitoreándolo" no está en los datos.** Es una recomendación que el modelo agregó. Los controles no la cortan porque no es una cifra ni una causalidad ni un diagnóstico.

**Qué decir, sin esquivarlo:** *"El modelo agrega consejos que los datos no contienen. Por eso la interfaz dice que sus afirmaciones no se pueden verificar una por una, y por eso la versión del motor queda siempre abajo como la que manda."*

Esta es la pregunta más honesta de las cuatro y la que conviene mostrar si el jurado es técnico.

---

## Lo que hay que saber antes de mostrarlo

| | |
|---|---|
| Modelo | `qwen2.5:7b` en Ollama, elegido automáticamente entre los instalados |
| Primer tiempo de respuesta | ~8 s si el modelo está frío (5 s son de carga de pesos) |
| En caliente | ~2-3 s |
| Lo que el sistema controla | cifras que no estén en los datos, lenguaje causal ("esto indica", "debido a"), lenguaje diagnóstico |
| Lo que el sistema NO controla | recomendaciones suaves y adjetivos ("es importante", "un poco alto") |
| Si el modelo falla | la respuesta del motor aparece igual, con una nota que dice por qué |

**El precalentamiento es automático:** al prender el botón, el modelo se carga en segundo plano. Si vas a mostrar el modo IA, prendelo **antes** de empezar a hablar de otra cosa.

## Si el modelo no arranca en el evento

El botón dice **"IA local: no disponible"** y las respuestas siguen funcionando. No hay que hacer nada. Es el caso que se probó con un modelo inexistente: la app responde igual, con el aviso visible.
