export type CM = { tp: number; fp: number; fn: number; tn: number };

export function metrics({ tp, fp, fn, tn }: CM) {
  const precision   = tp / Math.max(1, tp + fp);
  const recall      = tp / Math.max(1, tp + fn);
  const f1          = (2 * precision * recall) / Math.max(1e-9, precision + recall);
  const specificity = tn / Math.max(1, tn + fp);
  return { precision, recall, f1, specificity, totalPositives: tp + fn };
}

/** Wilson score interval. For 0 failures in n trials, lo = n / (n + z^2). */
export function wilson(successes: number, n: number, z = 1.96) {
  if (n === 0) return { lo: 0, hi: 1 };
  const p = successes / n, z2 = z * z, d = 1 + z2 / n;
  const centre = (p + z2 / (2 * n)) / d;
  const half = (z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / d;
  return { lo: Math.max(0, centre - half), hi: Math.min(1, centre + half) };
}
