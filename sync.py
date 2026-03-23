"""
Relif → Google Sheets daily sync
Corre la query de ayer en Relif y reemplaza la data en el Sheet configurado.
"""

import json
import os
import sys
from datetime import datetime, timezone

import gspread
import requests
from google.oauth2.service_account import Credentials

# ── Configuración ──────────────────────────────────────────────────────────────

RELIF_AUTH_URL = "https://relif-saas-back-yb2ukoflca-tl.a.run.app/auth"
RELIF_EXECUTE_URL = (
    "https://relif-saas-back-workload-816446680429.southamerica-west1.run.app"
    "/admin/db/execute"
)

SPREADSHEET_ID = "1VBJylnONuS0rNFJZ_UAbiGiy_TgR8N9WK6cYtMM580E"
SHEET_GID = 290261131

SQL_QUERY = """
SELECT *
FROM "BankOfferRequests"
WHERE "createdAt" >= CURRENT_DATE - INTERVAL '1 day'
  AND "createdAt" < CURRENT_DATE
"""

GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ── Auth Relif ─────────────────────────────────────────────────────────────────

def get_token() -> str:
    """
    Obtiene un JWT de Relif.
    Intenta login con email+contraseña; si falla, usa RELIF_JWT_TOKEN como fallback.
    """
    email = os.environ.get("RELIF_EMAIL", "")
    password = os.environ.get("RELIF_PASSWORD", "")

    if email and password:
        try:
            resp = requests.post(
                RELIF_AUTH_URL,
                json={"email": email, "password": password},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            # El campo puede llamarse distinto según el backend
            token = (
                data.get("accessToken")
                or data.get("access_token")
                or data.get("token")
                or data.get("jwt")
            )
            if token:
                print("  ✓ Login exitoso con email/contraseña")
                return token
        except Exception as exc:
            print(f"  ⚠ Login fallido ({exc}), usando token de respaldo...")

    # Fallback: token almacenado manualmente
    token = os.environ.get("RELIF_JWT_TOKEN", "")
    if token:
        print("  ✓ Usando RELIF_JWT_TOKEN almacenado")
        return token

    raise RuntimeError(
        "No se pudo obtener token. "
        "Configura RELIF_EMAIL + RELIF_PASSWORD o RELIF_JWT_TOKEN."
    )


# ── Query Relif ────────────────────────────────────────────────────────────────

def run_query(token: str) -> list:
    """Ejecuta la SQL query en el endpoint de Relif y devuelve los resultados."""
    resp = requests.post(
        RELIF_EXECUTE_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"userQuery": SQL_QUERY.strip()},
        timeout=60,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results


# ── Procesamiento ──────────────────────────────────────────────────────────────

def flatten(record: dict) -> dict:
    """
    Aplana un registro. El campo statusHistory (lista anidada) se desglosa
    en columnas separadas para facilitar el análisis en Looker Studio.
    """
    history = record.get("statusHistory", [])
    events = [h for h in history if "event" in h]
    last = events[-1] if events else {}

    return {
        "id":               record.get("id"),
        "leadId":           record.get("leadId"),
        "bukLeadId":        record.get("bukLeadId"),
        "bank":             record.get("bank"),
        "status":           record.get("status"),
        "rut":              record.get("rut"),
        "sentToBankAt":     record.get("sentToBankAt"),
        "createdAt":        record.get("createdAt"),
        "updatedAt":        record.get("updatedAt"),
        "statusSteps":      len(history),
        "lastEvent":        last.get("event"),
        "lastEventAt":      last.get("triggeredAt"),
        "lastEventBy":      last.get("triggeredBy"),
    }


# ── Google Sheets ──────────────────────────────────────────────────────────────

def get_worksheet():
    """Devuelve el objeto worksheet apuntando a la hoja correcta por gid."""
    creds_raw = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    if not creds_raw:
        raise RuntimeError("Falta la variable GOOGLE_CREDENTIALS_JSON")

    creds_dict = json.loads(creds_raw)
    creds = Credentials.from_service_account_info(creds_dict, scopes=GOOGLE_SCOPES)
    gc = gspread.authorize(creds)

    spreadsheet = gc.open_by_key(SPREADSHEET_ID)

    for ws in spreadsheet.worksheets():
        if ws.id == SHEET_GID:
            return ws

    raise RuntimeError(f"No se encontró la hoja con gid={SHEET_GID}")


def update_sheet(records: list) -> None:
    """Borra el contenido del Sheet y lo reemplaza con los nuevos datos."""
    ws = get_worksheet()

    if not records:
        print("  ⚠ No hay registros para el período consultado — Sheet no modificado.")
        return

    rows = [flatten(r) for r in records]
    headers = list(rows[0].keys())
    data = [headers] + [[row.get(h) for h in headers] for row in rows]

    ws.clear()
    ws.update(data, value_input_option="USER_ENTERED")
    print(f"  ✓ Sheet actualizado: {len(rows)} filas + encabezados")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"=== Relif Sync — {ts} ===")

    print("1/3  Autenticando en Relif...")
    token = get_token()

    print("2/3  Ejecutando query...")
    results = run_query(token)
    print(f"     → {len(results)} registro(s) obtenido(s)")

    print("3/3  Actualizando Google Sheet...")
    update_sheet(results)

    print("=== ✅ Sync completado ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\n❌ Error: {exc}", file=sys.stderr)
        sys.exit(1)
