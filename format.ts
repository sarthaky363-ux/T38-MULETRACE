// src/lib/format.ts
const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

/** Single source of truth for percentages. Input is 0-100 unless isRatio. */
export function fmtPct(value: number | string, digits = 1, isRatio = false): string {
  let num: number;
  if (typeof value === "string") {
    num = parseFloat(value.replace(/%+$/, ""));
  } else {
    num = Number(value);
  }
  if (isNaN(num)) return "0.0%";
  const v = isRatio ? num * 100 : num;
  return v.toFixed(digits) + "%";
}

export const fmtINR = (n: number): string => "₹" + inr.format(Math.round(n || 0)); // ₹7,95,000

export function fmtINRCompact(n: number): string { // KPI tiles only
  if (!n) return "₹0";
  if (n >= 1e7) return "₹" + (n / 1e7).toFixed(2) + " Cr";
  if (n >= 1e5) return "₹" + (n / 1e5).toFixed(2) + " Lakh";
  return fmtINR(n);
}

export const fmtMin = (m: number): string => (m || 0).toFixed(1) + " min";
