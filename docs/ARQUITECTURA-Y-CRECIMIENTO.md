# Pulse-0G — cómo funciona, cómo se conectaría y hasta dónde puede crecer

Documento técnico-explicativo. No es una promesa de producto: separa lo que **está construido**, lo que **está diseñado y no implementado** y lo que **sería necesario para llevarlo a vuelo**.

---

## 1. Qué pasa cuando el astronauta toca la pantalla

El recorrido completo de un dato, de punta a punta.

### Paso 1 · La medición entra

Hoy entra por tres caminos, todos archivados:

- Un **archivo publicado por NASA** (OSD-575, OSD-656), descargado y guardado sin editar en `data/raw/`.
- Un **escenario sintético** generado con semilla fija, manifiesto y parámetros explícitos.
- La **bitácora**, que es texto libre y nunca se trata como medición.

### Paso 2 · El adaptador la normaliza

Cada estudio tiene su propio adaptador, porque cada archivo tiene sus rarezas. El adaptador:

1. Identifica el sujeto, la matriz y el tiempo a partir del identificador de muestra (`C001_serum_L-3`).
2. Detecta el token de faltante que usó ese archivo: `N/A`, `NA`, celda vacía. **Los tres se guardan como ausencia.**
3. Separa la referencia en dos columnas: mínimo y máximo. Si el archivo no la trae, queda `absent`.
4. Calcula el orden temporal **semántico** (`L-92` antes que `L-3`, no alfabético).
5. Rechaza lo que no puede identificar: una columna sin encabezado no se adivina, se registra en el log de rechazos.

### Paso 3 · Se guarda con procedencia

Cada fila de la base lleva consigo:

```
dataset · versión · sujeto · variable · valor · unidad
rango mínimo y máximo · de dónde salió el rango
tiempo etiquetado · fase · desplazamiento en días · orden
tipo de origen (real / reproducido / falla inyectada / sintético)
etiqueta de peligro · archivo fuente · fila fuente · columna fuente
token de faltante · banderas de calidad
```

Esa última tanda es la que permite que el sistema pueda **responder "de dónde sale este dato"** sin inventar nada.

### Paso 4 · El motor de bandas clasifica

Tres caminos, y ninguno inventa:

| Situación | Qué hace |
|---|---|
| El archivo trae rango de referencia | Clasifica contra eso y cita el archivo |
| Existe una tarjeta de evidencia para ese límite | Clasifica y cita la tarjeta |
| No hay ni rango ni tarjeta | **Gris: "sin umbral citado"** |

La cobertura se evalúa **por límite y no por variable**. Citar la línea de 6 horas de sueño no habilita la de 5: si el valor dispara el límite de 5, el indicador vuelve a decir "provisional". Eso evita el error más fácil de cometer, que es declarar cubierta una regla entera citando una de sus dos fronteras.

### Paso 5 · La interfaz muestra la decisión

Figura, tabla, banda y acción. El desvío contra la base propia se muestra **aunque la banda sea verde**, porque una persona puede estar dentro del rango y aun así haberse movido.

### Paso 6 · El verificador controla la respuesta

Cuando el astronauta pregunta, la respuesta no la escribe un modelo: la arma un motor de plantillas que conoce ocho intenciones. Cada frase sale con su ancla. Después, un verificador independiente:

1. Extrae los números del texto ya renderizado.
2. Los compara contra los valores del ancla, aceptando redondeo (`76.4` sanciona `76`).
3. Ignora los identificadores, que tienen dígitos pero no son cifras.
4. Tacha lo que no coincide.

### Paso 7 · La decisión queda registrada

La bitácora guarda notas con rol, hora de misión y hora de pared. Es **append-only**: no hay edición ni borrado, y una corrección es una nota nueva que apunta a la anterior. Los triggers de la base rechazan `UPDATE` y `DELETE` incluso si alguien los intenta por SQL directo.

### Paso 8 · Si hace falta, se escala

El paquete de caso reúne lo medido, las bandas disparadas, las reglas, la calidad de los datos y la bitácora. Se descarga como JSON y se previsualiza como informe legible. **No se envía nada.** Si esa función no se usa nunca, todo lo demás funciona igual.

---

## 2. Cómo se conectarían los sensores

Hoy no hay sensores: hay archivos y un escenario. La pregunta razonable es qué cambiaría si los hubiera, y la respuesta corta es **la capa de ingesta, y nada más**.

### 2.1 El contrato ya existe

El esquema de la base es, en la práctica, el contrato de integración. Un sensor nuevo aporta filas con los mismos campos que ya existen. Todo lo que está arriba —bandas, verificador, bitácora, paquete de caso— no se toca.

```
Lector → Adaptador → measurement → [motor de bandas] → pantalla
```

El adaptador es lo único específico de cada dispositivo. Es deliberado: los adaptadores son baratos y desechables; el motor de bandas y el verificador son el activo.

### 2.2 Qué tendría que resolver un adaptador real

| Problema | Por qué importa | Cómo se resuelve |
|---|---|---|
| **Calidad de señal** | Un PPG con movimiento da un pulso falso | Banderas de calidad por muestra; el valor con mala calidad no puede disparar una banda roja |
| **Deriva del sensor** | Un termómetro sin calibrar miente sistemáticamente | Calibración declarada por dispositivo, guardada junto a la serie |
| **Huecos de conexión** | Un parche se cae y vuelve | Se guarda el hueco como hueco; nunca se interpola |
| **Reloj** | Fuera de la Tierra, el tiempo del dispositivo y el de misión difieren | Se guardan los dos: hora de dispositivo y hora de misión |
| **Unidades** | mg/dL y mmol/L conviven en la literatura | Unidad obligatoria por muestra; el motor convierte, no adivina |
| **Procedencia** | Un valor manual y uno de sensor no son comparables | `origin_type` distingue sensor, manual, reproducido y sintético |

### 2.3 Los sistemas que existen y qué aportarían

No hay que inventar hardware: la estación y las agencias ya tienen estos. Lo que falta —y es lo que este proyecto propone— es la capa que **interpreta** esos datos contra la base del propio tripulante y muestra de dónde sale cada afirmación.

| Sistema | Qué mide | Qué aportaría a Pulse-0G |
|---|---|---|
| **Bio-Monitor / Astroskin** (CSA) | ECG, frecuencia y variabilidad, presión, respiración, SpO₂, temperatura de piel, actigrafía | Serie continua de las variables cardíacas y de sueño que hoy son sintéticas |
| **EveryWear** (CNES/MEDES/ESA) | Hub de cuestionarios, nutrición, medicación y wearables | El canal de entrada manual —ánimo, adherencia, síntomas— con sello de tiempo |
| **Double Sensor / Thermo-Mini** (ESA/DLR) | Temperatura central no invasiva en la frente y ritmos circadianos | Convertiría la temperatura en serie continua y permitiría ver el corrimiento de base en vuelo |
| **Dosímetros pasivos** | Dosis acumulada de radiación | La única entrada necesaria hoy es manual, y ya está soportada |

La consecuencia de diseño es importante y conviene decirla: **este proyecto no necesita un sensor nuevo**. Necesita que los datos que ya se generan en vuelo tengan una capa de interpretación verificable. Eso lo posiciona como complemento de los sistemas existentes, no como competencia.

### 2.4 Lo que un dispositivo real NO podría hacer

No podría mejorar la calidad de la evidencia. Un sensor entrega números con incertidumbre; el umbral que decide si ese número importa sigue necesitando una fuente. **Más datos no arreglan la falta de criterio.**

---

## 3. Cómo se conectaría la IA

Hoy hay **un modo opcional con modelo local, apagado por defecto**, y la regla no cambió: el modelo nunca produce un número. Lo que sigue sin existir es cualquier dependencia de él: sin modelo, el producto responde igual.

Está implementado así: al activar el interruptor, la consulta se resuelve primero con el motor determinístico; después el modelo reescribe esas frases ya ancladas; y un control compara **todos los números del texto reescrito contra los del texto original**. Si aparece una cifra que no estaba, el párrafo se descarta, se muestra el motivo y queda la versión del motor. La llamada tiene un tiempo máximo de 25 segundos y cualquier fallo devuelve la respuesta determinística con una nota visible.

### 3.1 El rol que sí tiene sentido

Un **narrador**. Nada más.

```
pregunta → [motor determinístico calcula] → resultados estructurados
        → [recuperación de tarjetas] → evidencia
        → [modelo] reescribe en lenguaje humano
        → [verificador] controla cada número y cada ancla
        → respuesta, o tachado
```

Tres reglas que no se negocian:

1. **El modelo nunca produce un número.** No calcula, no promedia, no redondea. Todo número que aparece en pantalla lo puso el motor determinístico.
2. **El modelo no agrega afirmaciones.** Su trabajo es redactar mejor lo que ya está anclado.
3. **El verificador corre después del modelo, no antes.** El texto que se controla es el que el usuario va a leer, no el que el sistema creyó generar.

### 3.2 Qué se gana y qué se pierde

| Se gana | Se pierde |
|---|---|
| Preguntas más libres que las ocho intenciones fijas | Determinismo total de la respuesta |
| Redacción más natural en español | Una dependencia de hardware o de red |
| Explicaciones más largas sin sonar a plantilla | Arranque en frío y latencia |

Por eso el diseño lo pone **apagado por defecto** y con el camino sin modelo siempre disponible. Si el modelo falla, la pantalla no se cae: se degrada.

### 3.3 Dónde sí aportaría un modelo, hoy

- Reescribir la explicación de una banda en lenguaje llano para un tripulante no médico.
- Traducir preguntas libres a una de las ocho intenciones, en vez de rechazar lo que no coincide literalmente.
- Redactar el informe del paquete de caso para el médico de vuelo, a partir de los resultados ya calculados.

### 3.4 Dónde NO

- **Decidir una banda.** Eso es una regla con una fuente, no una opinión.
- **Interpretar una imagen** sin un modelo validado y sin declarar su incertidumbre.
- **Completar un dato faltante.** Un hueco es información.
- **Hablar de diagnóstico.** El sistema no diagnostica, y un modelo no cambia eso.

---

## 4. Potencial de crecimiento más allá del prototipo

Cuatro direcciones, ordenadas por relación entre esfuerzo y valor. Las tres primeras son extensiones naturales de lo construido; la cuarta es otra categoría de proyecto.

### 4.1 Más cobertura de evidencia (días)

El cuello de botella actual no es técnico: es documental. Cada indicador necesita su tarjeta con cita literal. Con el validador y el protocolo ya escritos, sumar cobertura es trabajo de lectura, no de ingeniería.

- Umbrales de presión y frecuencia contra guías clínicas, **etiquetadas como estándar terrestre** y no como criterio de vuelo.
- Umbrales conductuales cuando NASA los publique: la tarjeta que documenta su ausencia se convierte en la tarjeta que los cita.
- Protocolos de acción por banda, con su fuente, que hoy son parámetros del escenario.

### 4.2 Más datos reales (semanas)

- Un dataset con señal continua —por ejemplo un conjunto terrestre de PPG con referencia de ECG— para probar el procesamiento de ondas, siempre etiquetado como terrestre y nunca presentado como NASA.
- Series de misión más largas, si se abre el acceso a datos controlados de otras misiones.
- Telemetría ambiental (CO₂ de cabina, dosis de radiación) para completar la hazard del ambiente cerrado.

### 4.3 De un tripulante a una misión (meses)

- **Roles**: tripulación y médico de vuelo, con permisos distintos sobre el paquete de caso y la bitácora.
- **Multi-tripulante**: comparación entre personas sin mezclar identidades, que es exactamente el error que hoy el sistema evita por diseño.
- **Fase de misión**: umbrales distintos antes, durante y después del vuelo, con la base calculada por fase.
- **Modo desconectado real**: hoy funciona sin red; el paso siguiente es sincronización diferida cuando vuelve el enlace, con resolución explícita de conflictos en lugar de "gana el último".

### 4.4 De herramienta a sistema operativo clínico (años)

Esto requiere cosas que un prototipo no tiene y no puede fingir: validación clínica, certificación, gestión de identidad, auditoría formal y un programa médico detrás. Lo honesto es decirlo así: **Pulse-0G es la capa de interpretación y trazabilidad, no el sistema médico completo.** Su valor es que, cuando ese sistema exista, ya va a tener resuelto lo más difícil: que cada afirmación sobre una persona pueda rastrearse hasta su fuente.

---

## 5. Las tres decisiones que sostienen todo

1. **El número no es el producto, la decisión lo es.** Por eso hay bandas, acciones y un bloque de alarma en lugar de un tablero de cifras.
2. **Ninguna afirmación sin fuente.** Por eso hay tarjetas, verificador y abstención en lugar de un chat.
3. **Ningún dato inventado, ni para completar un hueco.** Por eso un faltante se dibuja como hueco, una columna sin nombre se rechaza y un umbral sin fuente se marca provisional delante del usuario.

Cualquier función futura que rompa alguna de las tres deja de ser este proyecto.
