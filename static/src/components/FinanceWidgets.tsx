import { type ReactNode, useEffect, useRef, useState } from 'react';
import { AlertCircle, Loader2 } from 'lucide-react';

function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T | undefined>(undefined);

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}

export function MetricCard({
  label,
  value,
  note,
  integer = false,
  loading = false,
  highlightOnChange = true,
}: {
  label: string;
  value: number | null | undefined;
  note: string;
  integer?: boolean;
  loading?: boolean;
  highlightOnChange?: boolean;
}) {
  const prevValue = usePrevious(value);
  const [flash, setFlash] = useState(false);

  useEffect(() => {
    if (highlightOnChange && prevValue !== undefined && value !== prevValue && !loading) {
      setFlash(true);
      const timer = window.setTimeout(() => setFlash(false), 1200);
      return () => window.clearTimeout(timer);
    }

    return undefined;
  }, [value, prevValue, loading, highlightOnChange]);

  const displayValue =
    value === null || value === undefined || Number.isNaN(value)
      ? 'N/A'
      : integer
        ? Math.round(value).toString()
        : value.toFixed(4);

  return (
    <div className="dash-card flex flex-col justify-between rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm font-medium text-slate-500">{label}</div>
      <div className="mt-3">
        {loading ? (
          <div className="h-8 w-24 animate-pulse rounded bg-slate-200" />
        ) : (
          <div className={`inline-block text-2xl font-bold text-slate-900 ${flash ? 'data-flash-active' : ''}`}>
            {displayValue}
          </div>
        )}
      </div>
      <div className="mt-2 text-xs leading-tight text-slate-400">{note}</div>
    </div>
  );
}

export function ChartCard({
  title,
  note,
  children,
  heightClass,
  loading = false,
}: {
  title: string;
  note: string;
  children: ReactNode;
  heightClass: string;
  loading?: boolean;
}) {
  return (
    <div className="dash-card rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-800">{title}</h3>
        {loading ? <Loader2 className="h-4 w-4 animate-spin text-blue-500" /> : null}
      </div>
      <p className="mt-1 text-sm text-slate-500">{note}</p>
      <div className={`relative mt-5 w-full ${heightClass}`}>
        {loading ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg bg-white/60 backdrop-blur-sm">
            <div className="flex flex-col items-center text-blue-600">
              <Loader2 className="mb-2 h-8 w-8 animate-spin" />
              <span className="text-sm font-medium">Computing...</span>
            </div>
          </div>
        ) : null}
        {children}
      </div>
    </div>
  );
}

export function StatusBadge({
  status,
  text,
}: {
  status: 'live' | 'fallback' | 'error' | 'loading' | 'offline';
  text: string;
}) {
  const styles = {
    live: 'border-emerald-200 bg-emerald-100 text-emerald-700',
    fallback: 'border-amber-200 bg-amber-100 text-amber-700',
    error: 'border-rose-200 bg-rose-100 text-rose-700',
    loading: 'border-blue-200 bg-blue-100 text-blue-700',
    offline: 'border-slate-200 bg-slate-100 text-slate-700',
  } as const;

  const dots = {
    live: (
      <span className="relative mr-1.5 flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
      </span>
    ),
    fallback: <span className="mr-1.5 h-2 w-2 rounded-full bg-amber-500" />,
    error: <span className="mr-1.5 h-2 w-2 rounded-full bg-rose-500" />,
    loading: <Loader2 className="mr-1.5 h-3 w-3 animate-spin" />,
    offline: <span className="mr-1.5 h-2 w-2 rounded-full bg-slate-400" />,
  } as const;

  return (
    <div className={`flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${styles[status]}`}>
      {dots[status]}
      {text}
    </div>
  );
}

export function ErrorPanel({ error }: { error: string | null }) {
  if (!error) {
    return null;
  }

  return (
    <div className="mt-4 flex items-start gap-3 rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
      <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
      <div>
        <p className="font-semibold text-rose-900">Operation Failed</p>
        <p className="mt-1">{error}</p>
      </div>
    </div>
  );
}
