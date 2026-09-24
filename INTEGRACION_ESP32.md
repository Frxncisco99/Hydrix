# Integración Hydrix con ESP32

## Orden de prueba

1. Ejecuta el SQL de Hydrix en Supabase y registra el sensor desde el dashboard.
2. Guarda el `sensor_id` y el token una sola vez. No los publiques en GitHub.
3. Configura las variables y ejecuta el simulador en modo seco:

```powershell
$env:HYDRIX_SENSOR_ID="uuid-del-sensor"
$env:HYDRIX_DEVICE_TOKEN="token-del-sensor"
python simulator.py --count 5 --flow 2.4
```

4. Si los payloads son correctos, prueba contra Supabase con `--send`:

```powershell
$env:HYDRIX_PUBLISHABLE_KEY="sb_publishable_..."
python simulator.py --send --count 10 --flow 2.4 --delay 2
```

El simulador usa el mismo RPC que el firmware: `registrar_lectura_esp32`, con
`p_sensor_id`, `p_token`, `p_secuencia`, `p_intervalo_ms` y `p_pulsos`. Nunca
imprime el token completo.

## Sensor de flujo

El ESP32 debe contar pulsos en una interrupción, calcular `pulsos` desde la
última transmisión y conservar `p_secuencia` en NVS. La conversión es:

```text
litros = pulsos / pulsos_por_litro
flujo_l_min = litros * 60000 / intervalo_ms
```

Calibra `pulsos_por_litro` midiendo un volumen conocido. El valor `450` del
simulador es únicamente un valor inicial de prueba.

## Servo y válvula

El dashboard no mueve el servo directamente. Crea un comando en
`solicitar_comando_valvula_hydrix`; el firmware debe leer los comandos
pendientes, mover el servo, confirmar físicamente el estado y actualizar la
válvula. La posición segura al arrancar debe ser cerrada, con límite mecánico y
sin alimentar el servo desde el pin de 3.3 V del ESP32.

Antes de conectar agua, prueba el servo sin presión y verifica que abrir/cerrar
no bloquee el mecanismo. Una lectura de flujo no debe cerrar la válvula sin una
regla de alerta confirmada por la base de datos.

## Contrato de producción

- Wi-Fi: solo 2.4 GHz.
- HTTPS: validar certificado; nunca usar `setInsecure()`.
- Reintentos: reenviar la misma secuencia hasta recibir HTTP 2xx.
- No incrementar la secuencia al reintentar.
- No subir credenciales, tokens ni claves `service_role` al repositorio.