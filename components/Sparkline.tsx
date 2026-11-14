import type { Band, SeriesPoint } from "@/lib/types";

/** Draws the series exactly as recorded: a missing sample is a break in the
 *  line, never an interpolated segment. */
export default function Sparkline({
  series,
  band,
  height = 46,
}: {
  series: SeriesPoint[];
  band: Band;
  height?: number;
}) {
  const width = 300;
  const pad = 6;
  const values = series
    .map((p) => p.value)
    .filter((v): v is number => v !== null);

  if (values.length === 0) {
    return (
      <p className="indicator-reason" style={{ marginTop: 10 }}>
        Sin muestras registradas en esta serie.
      </p>
    );
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const x = (i: number) =>
    pad + (series.length <= 1 ? 0 : (i / (series.length - 1)) * (width - pad * 2));
  const y = (v: number) =>
    height - pad - ((v - min) / span) * (height - pad * 2);

  const segments: Array<{ points: string; single: [number, number] | null }> = [];
  let current: Array<[number, number]> = [];
  const flush = () => {
    if (current.length === 0) return;
    if (current.length === 1) {
      segments.push({ points: "", single: current[0] });
    } else {
      segments.push({
        points: current.map(([cx, cy]) => `${cx},${cy}`).join(" "),
        single: null,
      });
    }
    current = [];
  };
  series.forEach((p, i) => {
    if (p.value === null) {
      flush();
    } else {
      current.push([x(i), y(p.value)]);
    }
  });
  flush();

  const gapIndexes = series
    .map((p, i) => (p.value === null ? i : -1))
    .filter((i) => i >= 0);

  return (
    <svg
      className="spark"
      data-band={band}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      role="img"
      aria-label={`Serie de ${series.length} muestras, ${values.length} con valor`}
    >
      {gapIndexes.map((i) => (
        <line
          key={`gap-${i}`}
          className="gap"
          x1={x(i)}
          y1={pad}
          x2={x(i)}
          y2={height - pad}
        />
      ))}
      {segments.map((s, i) =>
        s.single ? (
          <circle key={`p-${i}`} cx={s.single[0]} cy={s.single[1]} r={2.4} />
        ) : (
          <polyline key={`l-${i}`} points={s.points} />
        ),
      )}
    </svg>
  );
}
