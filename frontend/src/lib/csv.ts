// Client-side CSV export. Works on a fully static site (no backend round-trip),
// so we can export exactly the rows the user selected.

export interface CsvColumn<T> {
  key: string;
  header: string;
  /** Optional value accessor; defaults to row[key]. */
  get?: (row: T) => unknown;
}

function escapeCell(value: unknown): string {
  if (value === null || value === undefined) return '';
  let s: string;
  if (Array.isArray(value)) s = value.join('; ');
  else if (typeof value === 'object') s = JSON.stringify(value);
  else s = String(value);
  // Quote if it contains comma, quote, or newline.
  if (/[",\n\r]/.test(s)) {
    s = `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

export function rowsToCsv<T>(rows: T[], columns: CsvColumn<T>[]): string {
  const head = columns.map((c) => escapeCell(c.header)).join(',');
  const body = rows
    .map((row) =>
      columns
        .map((c) => escapeCell(c.get ? c.get(row) : (row as Record<string, unknown>)[c.key]))
        .join(','),
    )
    .join('\r\n');
  return `${head}\r\n${body}`;
}

/** Build a CSV from rows/columns and trigger a browser download (UTF-8 BOM for Excel). */
export function downloadCsv<T>(rows: T[], columns: CsvColumn<T>[], filenamePrefix: string): void {
  const csv = rowsToCsv(rows, columns);
  const blob = new Blob(['\ufeff', csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const ts = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '').replace(/-/g, '');
  const a = document.createElement('a');
  a.href = url;
  a.download = `${filenamePrefix}_${ts}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
