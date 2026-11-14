"use client";

import type { Band, ZoneView } from "@/lib/types";

const BAND_TEXT: Record<Band, string> = {
  green: "en rango",
  amber: "requiere atención",
  red: "requiere acción",
  no_data: "sin medición",
};

export function bandText(band: Band): string {
  return BAND_TEXT[band];
}

export default function BodyMap({
  zones,
  selected,
  onSelect,
}: {
  zones: ZoneView[];
  selected: string;
  onSelect: (id: string) => void;
}) {
  const zone = (id: string) => zones.find((z) => z.id === id);

  const props = (id: string) => {
    const z = zone(id);
    return {
      className: "region",
      role: "button" as const,
      tabIndex: 0,
      "data-band": z?.band ?? "no_data",
      "data-state": z?.state ?? "no_data",
      "data-selected": selected === id,
      "aria-label": `${z?.label ?? id}: ${bandText(z?.band ?? "no_data")}`,
      onClick: () => onSelect(id),
      onKeyDown: (e: React.KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(id);
        }
      },
    };
  };

  return (
    <svg
      className="body-svg"
      viewBox="0 0 200 400"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Mapa corporal de indicadores medidos"
    >
      {/* legs: hips, both legs, both feet */}
      <g {...props("legs")}>
        <rect x="82" y="165" width="36" height="30" rx="10" />
        <rect x="82" y="191" width="16" height="178" rx="8" />
        <rect x="102" y="191" width="16" height="178" rx="8" />
        <rect x="72" y="367" width="24" height="11" rx="5" />
        <rect x="104" y="367" width="24" height="11" rx="5" />
      </g>

      {/* thorax */}
      <g {...props("thorax")}>
        <path d="M 70 104 C 70 94 79 88 90 88 L 110 88 C 121 88 130 94 130 104 L 128 146 C 128 158 122 165 114 167 L 86 167 C 78 165 72 158 72 146 Z" />
      </g>

      {/* arms: the measurement site */}
      <g {...props("arm")}>
        <rect x="131" y="96" width="13" height="112" rx="6.5" transform="rotate(7 137.5 96)" />
        <rect x="56" y="96" width="13" height="112" rx="6.5" transform="rotate(-7 62.5 96)" />
      </g>

      {/* head */}
      <g {...props("head")}>
        <rect x="92" y="76" width="16" height="14" rx="5" />
        <circle cx="100" cy="54" r="24" />
      </g>

      {/* eyes: last, so they sit above the head */}
      <g {...props("eyes")}>
        <ellipse cx="92" cy="50" rx="4.2" ry="2.8" />
        <ellipse cx="108" cy="50" rx="4.2" ry="2.8" />
      </g>
    </svg>
  );
}
