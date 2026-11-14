# Cómo armar las tarjetas de evidencia

Las tarjetas son la única fuente de la que el sistema puede sacar una afirmación. Si una tarjeta está mal, el sistema miente con seguridad. Por eso el orden del trabajo importa: **primero se copia la cita real del documento, después la IA solo la reformula en español.**

## Lo que NO hay que hacer

No le preguntes a la IA "¿cuál es el umbral de presión sistólica en vuelo espacial?". Ese es el error que rompe el proyecto: la IA contesta algo que suena perfecto y que puede no existir en ningún paper. Si un juez pide la fuente, no la tenés.

## Los 5 pasos, por tarjeta

**1. Descargá el documento y anotá de dónde salió.**
Guardá la URL, la fecha en que lo abriste, la sección y la página. Después corré:

```bash
sha256sum nombre-del-archivo.pdf
```

Ese hash va en el campo `sha256`. Si el documento cambia en el futuro, el hash deja de coincidir y la tarjeta queda marcada como desactualizada. Es la prueba de que leíste algo que existe.

**2. Buscá el pasaje a mano y copialo tal cual.**
Usá Ctrl+F, encontrá el párrafo y **copialo textual en inglés**. Sin traducir, sin resumir, sin arreglar la redacción. Esa cita es la prueba, y va en el campo `quote`.

**3. Pasale a la IA solo esa cita, con este mensaje exacto:**

```
Traducí y resumí el siguiente pasaje en español rioplatense neutro, 2 o 3 oraciones.
Reglas estrictas:
- No agregues ningún dato, número, unidad ni afirmación que no esté en este texto.
- No completes información faltante.
- No uses lenguaje diagnóstico ("el astronauta tiene...").
- Si el pasaje no alcanza para responder, escribí "INSUFICIENTE".

PASAJE:
"""
<pegá acá la cita literal>
"""
```

**4. Verificá la salida.** Si el resumen contiene **un solo número que no aparece en la cita**, descartá la tarjeta y repetí. Si la IA devolvió "INSUFICIENTE", el pasaje no servía: buscá otro.

**5. Guardá el archivo.** Un archivo JSON por tarjeta, en `evidence/cards/`, copiando `_TEMPLATE.json`. Nombre: `EVD-<AREA>-<NNN>.json`.

## Antes de dar una tarjeta por terminada, pasala por el validador

```bash
python3 tools/check_cards.py
```

Es offline, no necesita nada corriendo, y dice exactamente qué está mal. Corta con
error si falta un campo, si el `id` no coincide con el nombre del archivo, si el
resumen agrega un número que la cita no tiene, o si una tarjeta `threshold` choca
con el umbral que usa el sistema. Avisa —sin bloquear— cuando la URL parece un
índice en vez del pasaje, cuando el `sha256` es un marcador, o cuando falta quién
verificó la cita.

## Los cuatro tipos

| `kind` | Qué contiene | Quién la valida |
|---|---|---|
| `threshold` | Un límite numérico con su fuente | **Solo el responsable técnico** |
| `measurement` | Cómo se mide algo en una misión real | Cualquiera, con el protocolo |
| `protocol` | Qué acción tomar ante una situación | Cualquiera, con el protocolo |
| `hazard` | Contexto de una de las cinco hazards | Cualquiera, con el protocolo |

Las `threshold` son las únicas que necesitan juicio clínico: son ocho y las valida el responsable del proyecto. El resto lo podés hacer con el protocolo de arriba, sin decidir nada médico vos.

## Las cinco hazards (para `applies_to`)

`hazard:radiation` · `hazard:isolation` · `hazard:gravity` · `hazard:distance` · `hazard:environment`

## Checklist antes de dar una tarjeta por terminada

- [ ] La cita está en inglés y es textual, no parafraseada
- [ ] Tengo la URL y la fecha
- [ ] Tengo el `sha256` del archivo
- [ ] El resumen en español no agrega ningún número que no esté en la cita
- [ ] El resumen no diagnostica ni receta
- [ ] `applies_to` tiene al menos un indicador o una hazard
- [ ] Si es `threshold`, tiene el objeto `thresholds` completo y lo revisó el responsable técnico

## Orden de prioridad

1. **8 tarjetas `threshold`** — sin estas no hay bandas de color y el producto no funciona
2. **5 `measurement`** — cómo se mide cada cosa
3. **3 `protocol`** — qué hacer ante cada banda
4. **2 `hazard`** — contexto para el pitch

Con 18 está completo. Con 10 el producto sigue en pie.
