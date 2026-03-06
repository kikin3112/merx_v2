import { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { tenants } from '../../api/endpoints';
import { useAuthStore } from '../../stores/authStore';

export default function MarcaTab() {
  const { tenantId } = useAuthStore();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: tenant, isLoading } = useQuery({
    queryKey: ['tenant-me', tenantId],
    queryFn: () => tenants.getMe(tenantId!).then(r => r.data),
    enabled: !!tenantId,
  });

  const [primaryColor, setPrimaryColor] = useState<string>('');
  const [secondaryColor, setSecondaryColor] = useState<string>('');

  // Initialize pickers from loaded tenant data (once)
  useEffect(() => {
    if (tenant) {
      setPrimaryColor(tenant.color_primario);
      setSecondaryColor(tenant.color_secundario);
    }
  }, [tenant]);

  const logoMutation = useMutation({
    mutationFn: (file: File) => tenants.uploadLogoMe(file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tenant-me'] }),
  });

  const colorMutation = useMutation({
    mutationFn: (data: { color_primario: string; color_secundario: string }) =>
      tenants.updateMe(data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tenant-me'] }),
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      alert('Solo JPG y PNG permitidos');
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      alert('Maximo 2MB');
      return;
    }
    logoMutation.mutate(file);
  };

  const handleSaveColors = () => {
    if (!primaryColor || !secondaryColor) return;
    colorMutation.mutate({ color_primario: primaryColor, color_secundario: secondaryColor });
  };

  // Preview uses local state — updates in real time as picker changes
  const previewPrimary = primaryColor || tenant?.color_primario || '#1976D2';

  if (isLoading) return <div className="cv-card p-8 cv-muted text-center">Cargando...</div>;

  return (
    <div className="space-y-6 max-w-lg">

      {/* Logo section */}
      <div className="cv-card p-6 space-y-4">
        <h2 className="cv-section-label">Logo</h2>
        {tenant?.url_logo && (
          <p className="text-xs cv-muted">Logo activo: {tenant.url_logo}</p>
        )}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/png,image/jpeg"
          className="hidden"
          onChange={handleFileChange}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={logoMutation.isPending}
          className="cv-btn cv-btn-secondary"
        >
          {logoMutation.isPending ? 'Subiendo...' : 'Subir logo (JPG/PNG, max 2MB)'}
        </button>
        {logoMutation.isSuccess && (
          <p className="text-xs" style={{ color: 'var(--cv-positive)' }}>Logo actualizado</p>
        )}
        {logoMutation.isError && (
          <p className="text-xs" style={{ color: 'var(--cv-negative)' }}>Error al subir logo</p>
        )}
      </div>

      {/* Color pickers */}
      <div className="cv-card p-6 space-y-4">
        <h2 className="cv-section-label">Colores de marca</h2>
        <div className="flex flex-col gap-3">
          <label className="flex items-center gap-3">
            <span className="text-sm cv-text w-32">Color primario</span>
            <input
              type="color"
              value={primaryColor || tenant?.color_primario || '#1976D2'}
              onChange={e => setPrimaryColor(e.target.value)}
              className="w-10 h-10 rounded cursor-pointer border-0"
            />
            <span className="text-xs cv-muted font-mono">
              {primaryColor || tenant?.color_primario || '#1976D2'}
            </span>
          </label>
          <label className="flex items-center gap-3">
            <span className="text-sm cv-text w-32">Color secundario</span>
            <input
              type="color"
              value={secondaryColor || tenant?.color_secundario || '#424242'}
              onChange={e => setSecondaryColor(e.target.value)}
              className="w-10 h-10 rounded cursor-pointer border-0"
            />
            <span className="text-xs cv-muted font-mono">
              {secondaryColor || tenant?.color_secundario || '#424242'}
            </span>
          </label>
        </div>
        <button
          onClick={handleSaveColors}
          disabled={colorMutation.isPending || (!primaryColor && !secondaryColor)}
          className="cv-btn cv-btn-primary"
        >
          {colorMutation.isPending ? 'Guardando...' : 'Guardar colores'}
        </button>
        {colorMutation.isSuccess && (
          <p className="text-xs" style={{ color: 'var(--cv-positive)' }}>Colores guardados</p>
        )}
      </div>

      {/* PDF Header preview */}
      <div className="cv-card p-6 space-y-3">
        <h2 className="cv-section-label">Preview encabezado PDF</h2>
        <div
          className="rounded p-4 flex items-center justify-between"
          style={{ backgroundColor: previewPrimary }}
        >
          <div>
            <p className="text-white font-semibold text-sm">
              {tenant?.nombre || 'Mi Empresa'}
            </p>
            <p className="text-white text-xs opacity-80">NIT / FACTURA</p>
          </div>
          <div
            className="w-10 h-10 rounded bg-white/20 flex items-center justify-center text-white text-xs"
          >
            LOGO
          </div>
        </div>
        <p className="text-xs cv-muted">
          Asi se vera el encabezado en facturas y cotizaciones PDF
        </p>
      </div>

    </div>
  );
}
