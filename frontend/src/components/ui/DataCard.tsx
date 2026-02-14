interface Field {
  label: string;
  value: React.ReactNode;
}

interface Props {
  title: string;
  subtitle?: string;
  badge?: React.ReactNode;
  fields: Field[];
  actions?: React.ReactNode;
  onClick?: () => void;
}

export default function DataCard({ title, subtitle, badge, fields, actions, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border border-gray-200 p-4 space-y-2 ${
        onClick ? 'cursor-pointer active:bg-gray-50 transition-colors' : ''
      }`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-gray-900 truncate">{title}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        {badge}
      </div>

      {/* Fields */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
        {fields.map((field, i) => (
          <div key={i}>
            <p className="text-[11px] text-gray-400 leading-tight">{field.label}</p>
            <p className="text-sm text-gray-700 font-medium">{field.value}</p>
          </div>
        ))}
      </div>

      {/* Actions */}
      {actions && (
        <div className="flex items-center gap-2 pt-1 border-t border-gray-100" onClick={(e) => e.stopPropagation()}>
          {actions}
        </div>
      )}
    </div>
  );
}
