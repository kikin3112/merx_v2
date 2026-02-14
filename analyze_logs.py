#!/usr/bin/env python3
"""
Script de análisis de logs para Chandelier ERP/POS.

Uso:
    python analyze_logs.py --errors           # Mostrar todos los errores
    python analyze_logs.py --slow 1000        # Requests >1000ms
    python analyze_logs.py --endpoint /pos    # Filtrar por endpoint
    python analyze_logs.py --user <user_id>  # Filtrar por usuario
    python analyze_logs.py --today            # Solo logs de hoy
    python analyze_logs.py --stats            # Estadísticas generales
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import List, Dict, Any
import argparse


def read_logs(log_file: Path = Path("logs/app.log")) -> List[Dict[str, Any]]:
    """Lee y parsea el archivo de logs JSON."""
    logs = []
    if not log_file.exists():
        print(f"❌ Archivo de logs no encontrado: {log_file}")
        return logs

    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                log = json.loads(line.strip())
                logs.append(log)
            except json.JSONDecodeError:
                continue  # Ignorar líneas malformadas

    return logs


def filter_logs(
    logs: List[Dict],
    errors_only: bool = False,
    min_duration: int = 0,
    endpoint: str = None,
    user_id: str = None,
    today_only: bool = False
) -> List[Dict]:
    """Filtra logs según criterios."""
    filtered = logs

    if errors_only:
        filtered = [l for l in filtered if l.get('level') in ('ERROR', 'CRITICAL')]

    if min_duration > 0:
        filtered = [l for l in filtered if l.get('duration_ms', 0) > min_duration]

    if endpoint:
        filtered = [l for l in filtered if endpoint in l.get('path', '')]

    if user_id:
        filtered = [l for l in filtered if user_id in str(l.get('user_id', ''))]

    if today_only:
        today = datetime.now().date()
        filtered = [
            l for l in filtered
            if l.get('timestamp') and
               datetime.fromisoformat(l['timestamp'].replace('Z', '+00:00')).date() == today
        ]

    return filtered


def show_errors(logs: List[Dict]):
    """Muestra todos los errores de forma legible."""
    errors = filter_logs(logs, errors_only=True)

    if not errors:
        print("✅ No se encontraron errores")
        return

    print(f"\n🔴 ERRORES ENCONTRADOS: {len(errors)}\n")
    print("=" * 80)

    for i, log in enumerate(errors[-20:], 1):  # Últimos 20 errores
        timestamp = log.get('timestamp', 'N/A')[:19]
        message = log.get('message', 'Sin mensaje')
        path = log.get('path', 'N/A')
        request_id = log.get('request_id', 'N/A')[:8]

        print(f"\n[{i}] {timestamp} | Request: {request_id}")
        print(f"    Path: {path}")
        print(f"    Message: {message}")

        if 'exception' in log:
            exc_lines = log['exception'].split('\n')[:3]  # Primeras 3 líneas
            print(f"    Exception: {exc_lines[0]}")

    print("\n" + "=" * 80)


def show_slow_requests(logs: List[Dict], threshold: int):
    """Muestra requests lentos."""
    slow = filter_logs(logs, min_duration=threshold)

    if not slow:
        print(f"✅ No hay requests >{threshold}ms")
        return

    print(f"\n🐌 REQUESTS LENTOS (>{threshold}ms): {len(slow)}\n")
    print("=" * 80)

    # Ordenar por duración descendente
    slow_sorted = sorted(slow, key=lambda x: x.get('duration_ms', 0), reverse=True)

    for i, log in enumerate(slow_sorted[:20], 1):  # Top 20
        duration = log.get('duration_ms', 0)
        path = log.get('path', 'N/A')
        method = log.get('method', 'N/A')
        timestamp = log.get('timestamp', 'N/A')[:19]

        print(f"[{i}] {duration:,.0f}ms | {method:6} {path}")
        print(f"    Timestamp: {timestamp}")

    print("\n" + "=" * 80)


def show_stats(logs: List[Dict]):
    """Muestra estadísticas generales."""
    if not logs:
        print("❌ No hay logs para analizar")
        return

    print("\n📊 ESTADÍSTICAS GENERALES\n")
    print("=" * 80)

    # Total de logs
    print(f"Total de logs: {len(logs):,}")

    # Por nivel
    levels = Counter(log.get('level') for log in logs)
    print(f"\nPor nivel:")
    for level, count in levels.most_common():
        print(f"  {level:10}: {count:,}")

    # Endpoints más llamados
    paths = [log.get('path') for log in logs if log.get('path')]
    if paths:
        path_counter = Counter(paths)
        print(f"\nEndpoints más llamados (Top 10):")
        for path, count in path_counter.most_common(10):
            print(f"  {count:5} | {path}")

    # Duración promedio de requests
    durations = [log.get('duration_ms') for log in logs if log.get('duration_ms')]
    if durations:
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        print(f"\nDuración de requests:")
        print(f"  Promedio: {avg_duration:.2f}ms")
        print(f"  Máximo:   {max_duration:.2f}ms")

    # Usuarios únicos
    users = {log.get('user_id') for log in logs if log.get('user_id')}
    print(f"\nUsuarios únicos: {len(users)}")

    # Requests por día (últimos 7 días)
    requests_by_day = defaultdict(int)
    for log in logs:
        if log.get('timestamp'):
            try:
                date = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00')).date()
                requests_by_day[date] += 1
            except:
                pass

    if requests_by_day:
        print(f"\nRequests por día (últimos 7):")
        for date in sorted(requests_by_day.keys())[-7:]:
            print(f"  {date}: {requests_by_day[date]:,}")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Analizador de logs para Chandelier ERP/POS",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--errors', action='store_true', help='Mostrar solo errores')
    parser.add_argument('--slow', type=int, metavar='MS', help='Mostrar requests lentos (>MS milisegundos)')
    parser.add_argument('--endpoint', type=str, help='Filtrar por endpoint (ej: /pos)')
    parser.add_argument('--user', type=str, help='Filtrar por user_id')
    parser.add_argument('--today', action='store_true', help='Solo logs de hoy')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas generales')
    parser.add_argument('--file', type=str, default='logs/app.log', help='Archivo de logs (default: logs/app.log)')

    args = parser.parse_args()

    # Leer logs
    log_file = Path(args.file)
    logs = read_logs(log_file)

    if not logs:
        print(f"❌ No se encontraron logs en {log_file}")
        sys.exit(1)

    print(f"✅ Leídos {len(logs):,} logs de {log_file}")

    # Aplicar filtros generales
    if args.endpoint or args.user or args.today:
        logs = filter_logs(
            logs,
            endpoint=args.endpoint,
            user_id=args.user,
            today_only=args.today
        )
        print(f"📋 {len(logs):,} logs después de filtrar")

    # Ejecutar comandos
    if args.errors:
        show_errors(logs)
    elif args.slow:
        show_slow_requests(logs, args.slow)
    elif args.stats:
        show_stats(logs)
    else:
        # Por defecto, mostrar stats
        show_stats(logs)


if __name__ == '__main__':
    main()
