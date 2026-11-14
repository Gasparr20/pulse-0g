import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

export interface EvidenceCard {
  id: string;
  kind: "threshold" | "hazard" | "protocol" | "measurement";
  title_es: string;
  summary_es: string;
  quote: string;
  source_label: string;
  url: string;
  retrieved_at: string;
  sha256: string;
  applies_to: string[];
  thresholds?: {
    variable: string;
    phase?: string;
    operator?: string;
    value: number;
    unit?: string;
  };
  license: string;
  verified_by?: string;
  notes?: string;
}

const DIR = path.join(process.cwd(), "evidence", "cards");

let cache: { stamp: number; cards: EvidenceCard[] } | null = null;

/** Cards are read from disk on every request in development, so the partner can
 *  drop a JSON file and see the effect without restarting anything. In a
 *  production build the directory is stamped once. */
export function loadCards(): EvidenceCard[] {
  let stamp = 0;
  try {
    stamp = statSync(DIR).mtimeMs;
  } catch {
    return [];
  }
  if (cache && cache.stamp === stamp && process.env.NODE_ENV === "production") {
    return cache.cards;
  }
  const cards: EvidenceCard[] = [];
  let files: string[] = [];
  try {
    files = readdirSync(DIR);
  } catch {
    return [];
  }
  for (const file of files) {
    if (!file.startsWith("EVD-") || !file.endsWith(".json")) continue;
    try {
      const parsed = JSON.parse(readFileSync(path.join(DIR, file), "utf8"));
      if (parsed && typeof parsed.id === "string") cards.push(parsed as EvidenceCard);
    } catch {
      // A malformed card must not break the dashboard; tools/check_cards.py
      // is the gate that reports it.
    }
  }
  cache = { stamp, cards };
  return cards;
}

/** A threshold card is a citation for the rule that already exists in
 *  config/bands.json. The card is the evidence, the config is the rule, and
 *  tools/check_cards.py refuses a pair where the two disagree. */
export function citationFor(variable: string): EvidenceCard | null {
  const cards = loadCards();
  return (
    cards.find(
      (c) =>
        c.kind === "threshold" &&
        (c.thresholds?.variable === variable || c.applies_to?.includes(variable)),
    ) ?? null
  );
}

export function cardsFor(variable: string): EvidenceCard[] {
  return loadCards().filter(
    (c) => c.applies_to?.includes(variable) || c.thresholds?.variable === variable,
  );
}
