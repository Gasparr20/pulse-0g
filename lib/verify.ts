import type { Anchor, Sentence } from "./types";

const NUMERIC = /\d+(?:[.,]\d+)?/g;

// Dataset and subject identifiers contain digits but are not measurements:
// OSD-575, R+29, SYNTH:ASTRO-01, CC0-1.0. They are removed before the check so
// the verifier only judges numeric claims.
const IDENTIFIER = /[A-Za-z_][A-Za-z0-9_:.+\-]*\d[A-Za-z0-9_:.+\-]*/g;

/** A printed number may be rounded for display, so an anchored value is accepted
 *  at zero, one or two decimals. 76.4 sanctions "76", "76.4" and "76.40". */
function forms(value: number): string[] {
  // The magnitude is accepted alongside the signed value: a sentence may state
  // "11 % por debajo", where 11 is backed by a delta of -11.1.
  return [value, Math.abs(value)].flatMap((v) =>
    [0, 1, 2].map((digits) => String(Math.round(v * 10 ** digits) / 10 ** digits)),
  );
}

function normaliseToken(token: string): string {
  return String(Number(token.replace(",", ".")));
}

/** Independent pass over an answer.
 *
 *  A sentence survives only when both hold:
 *    1. it cites at least one anchor (a data row, an aggregate or a card), and
 *    2. every number it prints appears in the anchored values.
 *
 *  The second rule is the one that matters. Templates are code, and code drifts:
 *  a sentence can claim "+12 %" while the data says +11. The verifier re-reads
 *  the rendered text, not the variables, so a drifted template is struck on
 *  screen instead of being trusted.
 */
export function verify(sentences: Sentence[]): Sentence[] {
  return sentences.map((sentence) => {
    if (sentence.anchors.length === 0) {
      return {
        ...sentence,
        struck: true,
        struckReason: "sin ancla: la frase no cita ningún dato ni ninguna tarjeta",
      };
    }
    const pool = new Set(
      sentence.anchors.flatMap((a: Anchor) => a.values.flatMap(forms)),
    );
    const claims = sentence.text.replace(IDENTIFIER, " ");
    const printed = claims.match(NUMERIC) ?? [];
    const unsupported = printed.filter((token) => {
      const value = Number(token.replace(",", "."));
      return Number.isFinite(value) && !pool.has(normaliseToken(token));
    });
    if (unsupported.length > 0) {
      return {
        ...sentence,
        struck: true,
        struckReason: `cifra sin respaldo en los datos citados: ${unsupported.join(", ")}`,
      };
    }
    return sentence;
  });
}

export function countStruck(sentences: Sentence[]): number {
  return sentences.filter((s) => s.struck).length;
}
