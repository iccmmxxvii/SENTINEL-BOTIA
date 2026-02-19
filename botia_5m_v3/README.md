# BOTIA_5M_V3

Bot paper-trading 5m con arquitectura de 3 capas:
- A) ejecución + seguridad
- B) normalización + edge
- C) copy-trading (solo lectura, stub inicial)

## Quickstart
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m botia5m doctor
python -m botia5m run --paper --max-seconds 600
```

## CLI
- `python -m botia5m doctor`
- `python -m botia5m run --paper`
- `python -m botia5m status`
- `python -m botia5m export --csv data/decisions.csv`

## Monitoreo
- Estado vivo: `STATUS.md`
- Logs JSON: `logs/botia5m.log`
- DB SQLite: `data/botia5m.sqlite`

## Seguridad
- PAPER por defecto.
- LIVE bloqueado salvo `mode.live_enabled=true` + `mode.live_confirmation=CONFIRMO`.
- No imprimir secretos/tokens.
- `.env` y datos en `.gitignore`.

## Troubleshooting
- Import errors: usa `pip install -e .` y ejecuta desde `botia_5m_v3/`.
- Permisos: valida escritura en `data/` y `logs/`.
- Time sync: revisa NTP en el VPS.
- Red inestable: el engine degrada a `NO_TRADE` y reintenta con backoff.
