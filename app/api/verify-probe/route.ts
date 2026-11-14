import { NextResponse } from "next/server";
import { verify } from "@/lib/verify";
import type { Anchor } from "@/lib/types";

/** Self-test for the claim verifier. A verifier that never rejects anything is
 *  decoration, so this feeds it known-good and known-bad sentences and reports
 *  whether each one was handled as intended. */
export const dynamic = "force-dynamic";

const ANCHOR: Anchor = {
  kind: "measurement",
  ref: "probe",
  label: "valor de prueba",
  values: [76.4, -11.13],
};

const CASES = [
  { text: "La dosis acumulada es 76 mSv.", anchors: [ANCHOR], mustStrike: false,
    why: "cifra redondeada para mostrar, respaldada por 76.4" },
  { text: "La dosis acumulada es 999 mSv.", anchors: [ANCHOR], mustStrike: true,
    why: "cifra inventada, no existe en los datos citados" },
  { text: "Bajó 11 % respecto de la base.", anchors: [ANCHOR], mustStrike: false,
    why: "magnitud de un delta de -11.13" },
  { text: "Bajó 40 % respecto de la base.", anchors: [ANCHOR], mustStrike: true,
    why: "porcentaje que no coincide con el dato" },
  { text: "La serie de glucosa tiene 19 muestras.", anchors: [ANCHOR], mustStrike: true,
    why: "19 no está en el ancla" },
  { text: "El valor está dentro de lo esperado.", anchors: [], mustStrike: true,
    why: "sin ancla, no hay nada que sostenga la frase" },
];

export async function GET() {
  const results = CASES.map((c) => {
    const [sentence] = verify([{ text: c.text, anchors: c.anchors }]);
    const struck = Boolean(sentence.struck);
    return {
      text: c.text,
      why: c.why,
      expected: c.mustStrike ? "tachada" : "sostenida",
      actual: struck ? "tachada" : "sostenida",
      pass: struck === c.mustStrike,
      reason: sentence.struckReason ?? null,
    };
  });
  return NextResponse.json({ pass: results.every((r) => r.pass), results });
}
