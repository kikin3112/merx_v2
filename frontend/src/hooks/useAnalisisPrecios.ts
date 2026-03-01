import { useMutation, useQuery } from '@tanstack/react-query';
import { analisisPrecios } from '../api/endpoints';
import type { CVURequest, CVUResponse, EscenariosResponse, SensibilidadResponse, RentabilidadItem, EconomiaEscalaResponse } from '../types';

// Python Decimal fields arrive as strings in JSON — cast all numeric fields here
function normalizeCVU(r: CVUResponse): CVUResponse {
  return {
    ...r,
    costo_variable_unitario: Number(r.costo_variable_unitario),
    margen_contribucion_unitario: Number(r.margen_contribucion_unitario),
    ratio_margen_contribucion: Number(r.ratio_margen_contribucion),
    punto_equilibrio_unidades: Number(r.punto_equilibrio_unidades),
    punto_equilibrio_ingresos: Number(r.punto_equilibrio_ingresos),
    margen_seguridad_unidades: Number(r.margen_seguridad_unidades),
    margen_seguridad_porcentaje: Number(r.margen_seguridad_porcentaje),
    utilidad_esperada: Number(r.utilidad_esperada),
  };
}

function normalizeEscenarios(r: EscenariosResponse): EscenariosResponse {
  return {
    ...r,
    costo_variable_unitario: Number(r.costo_variable_unitario),
    escenarios: r.escenarios.map((e) => ({
      ...e,
      precio: Number(e.precio),
      margen_porcentaje: Number(e.margen_porcentaje),
      margen_contribucion: Number(e.margen_contribucion),
      punto_equilibrio_unidades: Number(e.punto_equilibrio_unidades),
    })),
  };
}

function normalizeSensibilidad(r: SensibilidadResponse): SensibilidadResponse {
  return {
    ...r,
    pe_base_unidades: Number(r.pe_base_unidades),
    pe_base_ingresos: Number(r.pe_base_ingresos),
    utilidad_base: Number(r.utilidad_base),
    resultados: r.resultados.map((res) => ({
      ...res,
      nuevo_pe_unidades: Number(res.nuevo_pe_unidades),
      nuevo_pe_ingresos: Number(res.nuevo_pe_ingresos),
      nueva_utilidad: Number(res.nueva_utilidad),
      impacto_pe_porcentaje: Number(res.impacto_pe_porcentaje),
    })),
  };
}

function normalizeRentabilidad(items: RentabilidadItem[]): RentabilidadItem[] {
  return items.map((item) => ({
    ...item,
    costo_unitario: Number(item.costo_unitario),
    precio_venta: Number(item.precio_venta),
    margen_contribucion: Number(item.margen_contribucion),
    margen_porcentaje: Number(item.margen_porcentaje),
    mc_por_minuto: item.mc_por_minuto != null ? Number(item.mc_por_minuto) : null,
  }));
}

function normalizeEscala(r: EconomiaEscalaResponse): EconomiaEscalaResponse {
  return {
    ...r,
    costo_variable_unitario: Number(r.costo_variable_unitario),
    escala: r.escala.map((e) => ({
      ...e,
      costo_unitario: Number(e.costo_unitario),
      ahorro_vs_lote_1: Number(e.ahorro_vs_lote_1),
    })),
  };
}

export function useAnalisisCVU() {
  return useMutation<CVUResponse, Error, CVURequest>({
    mutationFn: (data) => analisisPrecios.cvu(data).then((r) => normalizeCVU(r.data)),
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
    mutationFn: (data) => analisisPrecios.sensibilidad(data).then((r) => normalizeSensibilidad(r.data)),
  });
}

export function useEscenarios() {
  return useMutation<EscenariosResponse, Error, {
    receta_id: string;
    costos_fijos: number;
    volumen: number;
    precio_mercado_referencia?: number;
  }>({
    mutationFn: (data) => analisisPrecios.escenarios(data).then((r) => normalizeEscenarios(r.data)),
  });
}

export function useComparadorRentabilidad() {
  return useQuery<RentabilidadItem[]>({
    queryKey: ['analisis', 'comparador'],
    queryFn: () => analisisPrecios.comparador().then((r) => normalizeRentabilidad(r.data)),
    staleTime: 2 * 60 * 1000,
  });
}

export function useEconomiaEscala() {
  return useMutation<EconomiaEscalaResponse, Error, {
    receta_id: string;
    costos_fijos_setup: number;
    lotes?: number[];
  }>({
    mutationFn: (data) => analisisPrecios.economiaEscala(data).then((r) => normalizeEscala(r.data)),
  });
}
