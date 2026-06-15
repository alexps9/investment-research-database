'use client';
import { useState, useCallback } from 'react';
import { Download, CheckSquare, X } from 'lucide-react';
import { useLang } from '@/lib/i18n';

/** Reusable row-selection state keyed by id. */
export function useRowSelection() {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggle = useCallback((id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  const setAll = useCallback((ids: string[], on: boolean) => {
    setSelected(on ? new Set(ids) : new Set());
  }, []);

  const clear = useCallback(() => setSelected(new Set()), []);

  return { selected, toggle, setAll, clear };
}

export function Checkbox({
  checked,
  onChange,
  indeterminate,
}: {
  checked: boolean;
  onChange: () => void;
  indeterminate?: boolean;
}) {
  return (
    <input
      type="checkbox"
      checked={checked}
      ref={(el) => {
        if (el) el.indeterminate = !!indeterminate && !checked;
      }}
      onChange={onChange}
      onClick={(e) => e.stopPropagation()}
      className="h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500"
    />
  );
}

/** Export toolbar: shows selection count, export-selected and export-all buttons. */
export function ExportBar({
  count,
  onExportSelected,
  onExportAll,
  onClear,
}: {
  count: number;
  onExportSelected: () => void;
  onExportAll: () => void;
  onClear: () => void;
}) {
  const { t } = useLang();
  return (
    <div className="flex items-center gap-2">
      {count > 0 && (
        <>
          <span className="text-xs font-medium text-gray-500">
            {t('select.count').replace('{n}', String(count))}
          </span>
          <button
            onClick={onClear}
            className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs text-gray-400 hover:text-gray-600"
            title={t('select.clear')}
          >
            <X size={13} />
          </button>
          <button
            onClick={onExportSelected}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
          >
            <Download size={15} /> {t('action.export_selected')}
          </button>
        </>
      )}
      <button
        onClick={onExportAll}
        className="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
      >
        <CheckSquare size={15} /> {t('action.export_all')}
      </button>
    </div>
  );
}
