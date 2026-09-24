"""Simulador de lecturas Hydrix antes de conectar el ESP32.

Por defecto solo imprime el payload. Usa --send para publicar en Supabase.
Configura las credenciales con variables de entorno; nunca las escribas aquí.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import time
import urllib.error
import urllib.request


DEFAULT_URL = "https://neuifbdkjdumudhgxupv.supabase.co"
SEQUENCE_BASE = 9_001_000_000_000_000


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def build_payload(sensor_id: str, token: str, sequence: int, interval_ms: int, pulses: int) -> dict[str, object]:
    if not sensor_id or sensor_id == "UUID_DEL_SENSOR":
        raise ValueError("Falta HYDRIX_SENSOR_ID")
    if not token or token == "TOKEN_DEL_SENSOR":
        raise ValueError("Falta HYDRIX_DEVICE_TOKEN")
    if interval_ms <= 0 or pulses < 0:
        raise ValueError("interval_ms debe ser positivo y pulses no puede ser negativo")
    return {"p_sensor_id": sensor_id, "p_token": token, "p_secuencia": sequence, "p_intervalo_ms": interval_ms, "p_pulsos": pulses}


def post_reading(url: str, key: str, payload: dict[str, object], timeout: float) -> tuple[int, str]:
    if not key:
        raise ValueError("Falta HYDRIX_PUBLISHABLE_KEY")
    endpoint = url.rstrip("/") + "/rest/v1/rpc/registrar_lectura_esp32"
    request = urllib.request.Request(endpoint, data=json.dumps(payload).encode(), method="POST", headers={"apikey": key, "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera lecturas de prueba para Hydrix")
    parser.add_argument("--send", action="store_true", help="publica en Supabase; sin esto solo simula")
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--flow", type=float, default=None, help="flujo fijo en L/min")
    parser.add_argument("--pulses", type=int, default=None, help="pulsos fijos por intervalo")
    parser.add_argument("--interval-ms", type=int, default=15000)
    parser.add_argument("--pulses-per-liter", type=float, default=450.0)
    parser.add_argument("--sequence", type=int, default=SEQUENCE_BASE + 1)
    args = parser.parse_args()
    if args.count < 1 or args.delay < 0 or args.pulses_per_liter <= 0:
        parser.error("count debe ser >= 1, delay >= 0 y pulses-per-liter > 0")

    sensor_id, token = env("HYDRIX_SENSOR_ID"), env("HYDRIX_DEVICE_TOKEN")
    url, key = env("HYDRIX_SUPABASE_URL", DEFAULT_URL), env("HYDRIX_PUBLISHABLE_KEY")
    rng = random.Random(42)
    for index in range(args.count):
        flow = args.flow if args.flow is not None else max(0.0, 2.0 + rng.uniform(-0.35, 0.35))
        pulses = args.pulses if args.pulses is not None else round(flow * args.interval_ms / 60000 * args.pulses_per_liter)
        payload = build_payload(sensor_id, token, args.sequence + index, args.interval_ms, pulses)
        print(json.dumps({**payload, "p_token": "[oculto]"}, ensure_ascii=False))
        if args.send:
            try:
                status, response = post_reading(url, key, payload, timeout=15)
                print(f"Supabase: HTTP {status} {response[:300]}")
                if status < 200 or status >= 300:
                    return 1
            except (OSError, ValueError) as error:
                print(f"Error de envío: {error}")
                return 1
        if index + 1 < args.count:
            time.sleep(args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())