import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { costosIndirectos } from '../api/endpoints';
import type { CostoIndirecto } from '../types';

export function useCostosIndirectos() {
  return useQuery<CostoIndirecto[]>({
    queryKey: ['costos-indirectos'],
    queryFn: () => costosIndirectos.list().then((r) => r.data),
    staleTime: 5 * 60 * 1000,
  });
}

export function useCrearCostoIndirecto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { nombre: string; monto: number; tipo: 'FIJO' | 'PORCENTAJE' }) =>
      costosIndirectos.create(data).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['costos-indirectos'] }),
  });
}

export function useEliminarCostoIndirecto() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => costosIndirectos.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['costos-indirectos'] }),
  });
}
