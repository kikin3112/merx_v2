import { useCallback, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { socia as sociaApi } from '../../api/endpoints';
import type { SociaProgreso } from '../../types';

export function useSociaGamification() {
  const queryClient = useQueryClient();
  const [newLogros, setNewLogros] = useState<string[]>([]);

  const { data: progreso } = useQuery<SociaProgreso>({
    queryKey: ['socia', 'progreso'],
    queryFn: () => sociaApi.progreso().then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });

  const { mutate: registrarLogro } = useMutation({
    mutationFn: (logro_id: string) => sociaApi.registrarLogro(logro_id).then((r) => r.data),
    onSuccess: (_: unknown, logro_id: string) => {
      setNewLogros((prev) => (prev.includes(logro_id) ? prev : [...prev, logro_id]));
      queryClient.invalidateQueries({ queryKey: ['socia', 'progreso'] });
    },
  });

  const desbloquear = useCallback(
    (logro_id: string) => {
      if (!progreso?.logros.includes(logro_id)) {
        registrarLogro(logro_id);
      }
    },
    [progreso, registrarLogro]
  );

  const dismissLogro = useCallback((logro_id: string) => {
    setNewLogros((prev) => prev.filter((id) => id !== logro_id));
  }, []);

  const tieneLogro = useCallback(
    (logro_id: string) => progreso?.logros.includes(logro_id) ?? false,
    [progreso]
  );

  return {
    progreso,
    newLogros,
    desbloquear,
    dismissLogro,
    tieneLogro,
  };
}
