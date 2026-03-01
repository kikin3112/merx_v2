import { useMutation, useQuery } from '@tanstack/react-query';
import { analisisPrecios } from '../api/endpoints';
import type { CVURequest, CVUResponse, EscenariosResponse, SensibilidadResponse, RentabilidadItem, EconomiaEscalaResponse } from '../types';

export function useAnalisisCVU() {
  return useMutation<CVUResponse, Error, CVURequest>({
    mutationFn: (data) => analisisPrecios.cvu(data).then((r) => r.data),
  });
}

export function useSensibilidad() {
  return useMutation<SensibilidadResponse, Error, {
    receta_id: string;
    precio_venta: number;
    costos_fijos: number;
    volumen_base: number;
    variaciones: Array<{ variable: string; delta_porcentaje: number }>;
  }>({
    mutationFn: (data) => analisisPrecios.sensibilidad(data).then((r) => r.data),
  });
}

export function useEscenarios() {
  return useMutation<EscenariosResponse, Error, {
    receta_id: string;
    costos_fijos: number;
    volumen: number;
    precio_mercado_referencia?: number;
  }>({
    mutationFn: (data) => analisisPrecios.escenarios(data).then((r) => r.data),
  });
}

export function useComparadorRentabilidad() {
  return useQuery<RentabilidadItem[]>({
    queryKey: ['analisis', 'comparador'],
    queryFn: () => analisisPrecios.comparador().then((r) => r.data),
    staleTime: 2 * 60 * 1000,
  });
}

export function useEconomiaEscala() {
  return useMutation<EconomiaEscalaResponse, Error, {
    receta_id: string;
    costos_fijos_setup: number;
    lotes?: number[];
  }>({
    mutationFn: (data) => analisisPrecios.economiaEscala(data).then((r) => r.data),
  });
}
