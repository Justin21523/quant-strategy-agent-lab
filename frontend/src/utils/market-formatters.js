const priceFormatter = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 4,
});

const integerFormatter = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const compactFormatter = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

export function formatPrice(value) {
  return Number.isFinite(Number(value)) ? priceFormatter.format(Number(value)) : "—";
}

export function formatInteger(value) {
  return Number.isFinite(Number(value)) ? integerFormatter.format(Number(value)) : "—";
}

export function formatCompact(value) {
  return Number.isFinite(Number(value)) ? compactFormatter.format(Number(value)) : "—";
}

export function formatTimestamp(value) {
  if (!value) return "—";
  const parsed = new Date(value);
  return Number.isNaN(parsed.valueOf()) ? value : parsed.toLocaleString();
}
