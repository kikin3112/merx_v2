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
      className={`cv-card p-4 space-y-2 ${onClick ? 'cursor-pointer cv-card-hover' : ''}`}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold cv-text truncate">{title}</p>
          {subtitle && <p className="text-xs cv-muted mt-0.5">{subtitle}</p>}
        </div>
        {badge}
      </div>

      {/* Fields */}
      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
        {fields.map((field, i) => (
          <div key={i}>
            <p className="text-[11px] cv-muted leading-tight">{field.label}</p>
            <p className="text-sm cv-text font-medium">{field.value}</p>
          </div>
        ))}
      </div>

      {/* Actions */}
      {actions && (
        <div className="flex items-center gap-2 pt-1 border-t cv-divider" onClick={(e) => e.stopPropagation()}>
          {actions}
        </div>
      )}
    </div>
  );
}
