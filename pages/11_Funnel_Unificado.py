"""Funnel Unificado — Fuente de la verdad de todos los canales BCI."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import pytz
from datetime import date, timedelta, datetime
from dotenv import load_dotenv
from collections import Counter

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

try:
    st.set_page_config(page_title="Funnel BCI", page_icon="🔀", layout="wide")
except Exception:
    pass

import pandas as pd

API_URL   = "https://relif-saas-back-workload-816446680429.southamerica-west1.run.app/admin/db/execute"
TOKEN     = os.getenv("RELIF_JWT_TOKEN", "")
TEST_RUTS = "'19.639.014-6','8.321.933-5','9.808.639-0','20.960.213-K','20.164.933-1','19.689.349-0'"
SHEET_XLSX_URL = "https://docs.google.com/spreadsheets/d/1Pkm4kX6dRRH0_Ar759E3ynKevK69WgTl/export?format=xlsx"

# Mapa mes → columna 0-indexed (igual en todas las hojas)
MONTH_COL = {
    "2026-02": 4, "2026-03": 5, "2026-04": 6, "2026-05": 7,
    "2026-06": 8, "2026-07": 9, "2026-08": 10, "2026-09": 11,
    "2026-10": 12,"2026-11": 13,"2026-12": 14,
}
# Config por canal: hoja y filas (0-indexed)
CANAL_SHEET = {
    "BCI Buk": {
        "sheet": "Consumo 2.0",
        "abren": 8, "wsp": 9, "wsp_label": "Click al simulador",
        "gest": 31, "venta": 33,
    },
    "Cashback": {
        "sheet": "1%",
        "abren": 6, "wsp": 7, "wsp_label": "Van al WhatsApp",
        "gest": 22, "venta": 24,
    },
    "Estanque Copec": {
        "sheet": "Copec",
        "gest": 22, "venta": 24,
    },
}

BCI_BLUE   = "#003DA5"
BCI_GREEN  = "#00A651"
BCI_YELLOW = "#F5A800"
BCI_RED    = "#E4002B"

CANALES = {
    "BCI Buk":        {"colors": ["#cce0ff","#80b3ff","#3386ff","#1A5FD4","#003DA5","#002b78","#001d52","#000e29"], "accent": BCI_BLUE},
    "Cashback":       {"colors": ["#ccf0e0","#80d4ad","#33b87a","#00A651","#007a3d","#005229","#003319","#001a0c"], "accent": BCI_GREEN},
    "Estanque Copec": {"colors": ["#fff3cc","#ffd966","#F5A800","#d4760a","#E4002B","#a80020","#7a0018","#4a0010"], "accent": BCI_RED},
}

STAGE_LABELS = [
    "Llegaron a Relif",
    "Tuvieron conversación",
    "Dieron consentimiento",
    "Pre-evaluados (BOR)",
    "Pre-aprobados BCI",
    "Enviados al banco",
    "En gestión BCI",
    "Venta Plan",
]

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
[data-testid="stAppViewContainer"] { background: #f8fafc; }
[data-testid="stSidebar"] { background: #0f172a !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stDateInput label { color: #94a3b8 !important; font-size: 0.75rem !important; }

/* Date inputs — fondo oscuro, texto claro */
[data-testid="stSidebar"] div[data-testid="stDateInput"] input,
[data-testid="stSidebar"] div[data-testid="stDateInput"] input::placeholder {
    background: #1e293b !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
    color: #cbd5e1 !important;
    font-size: 0.85rem !important;
    -webkit-text-fill-color: #cbd5e1 !important;
}
[data-testid="stSidebar"] div[data-testid="stDateInput"] > div {
    background: #1e293b !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] div[data-testid="stDateInput"] > div:focus-within {
    border-color: rgba(99,102,241,0.6) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}
/* Botón Actualizar */
[data-testid="stSidebar"] div[data-testid="stButton"] button {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    transition: background 0.15s !important;
}
[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {
    background: rgba(255,255,255,0.13) !important;
    border-color: rgba(255,255,255,0.25) !important;
}
div[data-testid="metric-container"] { display: none; }
.block-container { padding-top: 1.5rem !important; }
.kpi { background:white; border-radius:14px; padding:1.2rem 1.4rem;
       box-shadow:0 1px 6px rgba(0,0,0,.06); border:1px solid #e2e8f0; }
.kpi-val { font-size:2rem; font-weight:900; letter-spacing:-0.03em; line-height:1; }
.kpi-lbl { font-size:0.65rem; font-weight:700; text-transform:uppercase;
           letter-spacing:0.09em; color:#94a3b8; margin-bottom:6px; }
.kpi-sub { font-size:0.72rem; color:#64748b; margin-top:5px; }
.rej-card { background:white; border-radius:12px; padding:1rem 1.1rem;
            border:1px solid #e2e8f0; box-shadow:0 1px 4px rgba(0,0,0,.04);
            margin-bottom:0.5rem; }
.section-title { font-size:0.62rem; font-weight:700; text-transform:uppercase;
                 letter-spacing:0.12em; color:#94a3b8; margin:1.4rem 0 0.7rem; }
</style>
""", unsafe_allow_html=True)

# ── API ───────────────────────────────────────────────────────────────────
def _api(sql: str):
    """HTTP request puro — sin decorator para que funcione bien desde threads."""
    try:
        r = requests.post(API_URL, json={"userQuery": sql},
                          headers={"Authorization": f"Bearer {TOKEN}",
                                   "Content-Type": "application/json"}, timeout=60)
        if r.status_code == 200:
            return r.json().get("results", [])
        return []
    except Exception:
        return []

# ── Queries ───────────────────────────────────────────────────────────────
def _build_sql(canal: str, s: str, e: str) -> tuple:
    """Devuelve (q_clients, q_bor, q_rej) para un canal y rango de fechas."""
    dt = f'"createdAt" >= {s} AND "createdAt" < {e}'

    if canal == "BCI Buk":
        # BCI Buk: el cliente llega directamente vía BOR (no hay flujo de chat previo),
        # por eso anclamos TODO al BOR.createdAt para que el funnel sea consistente.
        jn = ('LEFT JOIN (SELECT DISTINCT ON (rut) rut, id, "clientMessagesCount", "privacyPolicyAccepted" '
              'FROM "Clients" WHERE "businessUnitId" = 73 ORDER BY rut, "createdAt" DESC) c ON b.rut = c.rut')
        bb = f'b.bank=\'BCI\' AND b."bukId" IS NOT NULL AND b.{dt} AND c.id IS NOT NULL'
    elif canal == "Cashback":
        bc = f'"source"=\'buk-cashback\' AND {dt} AND rut NOT IN ({TEST_RUTS})'
        jn = ('LEFT JOIN (SELECT DISTINCT ON (rut) rut, source FROM "Clients" '
              'ORDER BY rut, "createdAt" DESC) c ON b.rut = c.rut')
        bb = (f'b.bank=\'BCI\' AND b."bukId" IS NULL AND b.{dt} '
              f'AND c.source=\'buk-cashback\' AND b.rut NOT IN ({TEST_RUTS})')
    else:
        srcs = "'buk-estanque','buk-estanque-copec'"
        bc = f'"source" IN ({srcs}) AND {dt} AND rut NOT IN ({TEST_RUTS})'
        jn = ('LEFT JOIN (SELECT DISTINCT ON (rut) rut, source FROM "Clients" '
              'ORDER BY rut, "createdAt" DESC) c ON b.rut = c.rut')
        bb = (f'b.bank=\'BCI\' AND b."bukId" IS NULL AND b.{dt} '
              f'AND c.source IN ({srcs}) AND b.rut NOT IN ({TEST_RUTS})')

    if canal == "BCI Buk":
        # Anclar llegaron/conversación/consentimiento al BOR para consistencia
        q_clients = (
            f'SELECT COUNT(DISTINCT b.rut) as v1, '
            f'COUNT(DISTINCT CASE WHEN c."clientMessagesCount" > 0 THEN b.rut END) as v2, '
            f'COUNT(DISTINCT CASE WHEN c."privacyPolicyAccepted" = true THEN b.rut END) as v3 '
            f'FROM "BankOfferRequests" b {jn} WHERE {bb}'
        )
    else:
        q_clients = (
            f'SELECT COUNT(DISTINCT rut) as v1, '
            f'COUNT(DISTINCT CASE WHEN "clientMessagesCount" > 0 THEN rut END) as v2, '
            f'COUNT(DISTINCT CASE WHEN "privacyPolicyAccepted" = true THEN rut END) as v3 '
            f'FROM "Clients" WHERE {bc}'
        )
    q_bor = (
        f'SELECT COUNT(DISTINCT b.rut) as v4, '
        f'COUNT(DISTINCT CASE WHEN b.status IN (\'pre_approved\',\'sent_to_bank\') THEN b.rut END) as v5, '
        f'COUNT(DISTINCT CASE WHEN b.status=\'sent_to_bank\' THEN b.rut END) as v6, '
        f'COUNT(DISTINCT CASE WHEN b.status=\'rejected_by_bank\' THEN b.rut END) as rej '
        f'FROM "BankOfferRequests" b {jn} WHERE {bb}'
    )
    q_rej = (
        f'SELECT CASE WHEN ("rawBankResponse"::jsonb -> \'cliente\' ->> \'clienteBci\') = \'true\' '
        f'THEN \'Ya es cliente BCI\' '
        f'WHEN "rawBankResponse"::jsonb ->> \'mensaje\' IS NOT NULL '
        f'THEN "rawBankResponse"::jsonb ->> \'mensaje\' '
        f'ELSE \'No pasa filtros de riesgo\' END as categoria, '
        f'COUNT(*) as cnt '
        f'FROM "BankOfferRequests" b {jn} WHERE {bb} AND b.status=\'rejected_by_bank\' '
        f'GROUP BY 1 ORDER BY 2 DESC LIMIT 5'
    )
    return q_clients, q_bor, q_rej


def _assemble(canal: str, rc: dict, rb: dict, rr: list) -> dict:
    vals = [
        int(rc.get("v1") or 0), int(rc.get("v2") or 0), int(rc.get("v3") or 0),
        int(rb.get("v4") or 0), int(rb.get("v5") or 0), int(rb.get("v6") or 0),
    ]
    return {
        "values":   vals,
        "rejected": int(rb.get("rej") or 0),
        "rej_cats": {row["categoria"]: int(row["cnt"]) for row in rr},
    }

# ── Buk sheets ───────────────────────────────────────────────────────────
def load_buk_sheets() -> dict:
    """Devuelve dict sheet_name → DataFrame con todas las hojas del xlsx."""
    try:
        import io, openpyxl
        r = requests.get(SHEET_XLSX_URL, timeout=30)
        wb = openpyxl.load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
        return {
            name: pd.DataFrame([list(row) for row in wb[name].iter_rows(values_only=True)])
            for name in wb.sheetnames
        }
    except Exception:
        return {}

def _parse_val(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    try:
        s = str(v).strip().replace("%","").replace("$","").replace(" ","")
        s = s.replace(".","").replace(",",".") if "," in s else s.replace(".","")
        return int(float(s))
    except Exception:
        return None

def get_buk_values(sheets: dict, canal: str, start: date, end: date):
    """Retorna dict con abren/whatsapp/gestionados/ventas para el canal, o None si no hay datos."""
    cfg = CANAL_SHEET.get(canal)
    if not cfg:
        return None
    df = sheets.get(cfg["sheet"], pd.DataFrame())
    if df.empty:
        return None
    result = {"abren": 0, "whatsapp": 0, "gestionados": 0, "ventas": 0}
    d = start
    while d <= end:
        key = d.strftime("%Y-%m")
        col = MONTH_COL.get(key)
        if col is not None and col < df.shape[1]:
            if "abren" in cfg:
                va = _parse_val(df.iloc[cfg["abren"], col])
                vw = _parse_val(df.iloc[cfg["wsp"],   col])
                if va: result["abren"]    += va
                if vw: result["whatsapp"] += vw
            vg = _parse_val(df.iloc[cfg["gest"],  col])
            vv = _parse_val(df.iloc[cfg["venta"], col])
            if vg: result["gestionados"] += vg
            if vv: result["ventas"]      += vv
        d = (d.replace(day=1) + timedelta(days=32)).replace(day=1)
    if result["abren"] == 0 and result["gestionados"] == 0 and result["ventas"] == 0:
        return None
    return result

def render_buk_banner(buk, relif_top: int, canal: str, accent: str = BCI_BLUE):
    """Banner completo pre-funnel para vista de canal único."""
    if not buk or not buk.get("abren"):
        return
    cfg       = CANAL_SHEET.get(canal, {})
    wsp_label = cfg.get("wsp_label", "Van al WhatsApp")
    abren     = buk.get("abren") or 0
    wsp       = buk.get("whatsapp") or 0
    conv_pct  = round(relif_top / abren * 100, 1) if abren else None
    conv_html = (
        f'<span style="background:#fff3cd;color:#92400e;font-size:0.78rem;font-weight:700;'
        f'padding:3px 12px;border-radius:99px">→ {conv_pct}% llegó a Relif</span>'
    ) if conv_pct else ""

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#001f5c,{accent});border-radius:16px;
                padding:1.4rem 2rem;margin-bottom:0.6rem;
                display:flex;align-items:center;gap:2rem;flex-wrap:wrap">
      <div style="color:rgba(255,255,255,0.45);font-size:0.6rem;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.12em;min-width:56px;line-height:1.5">
        Pre-Relif<br>Buk
      </div>
      <div style="flex:1;display:flex;gap:2.5rem;flex-wrap:wrap;align-items:center">
        <div>
          <div style="color:rgba(255,255,255,0.5);font-size:0.62rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.08em">Abren beneficio en Buk</div>
          <div style="color:white;font-size:2rem;font-weight:900;letter-spacing:-0.03em">{abren:,}</div>
        </div>
        <div style="color:rgba(255,255,255,0.35);font-size:1.4rem;font-weight:300">→</div>
        <div>
          <div style="color:rgba(255,255,255,0.5);font-size:0.62rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.08em">{wsp_label}</div>
          <div style="color:white;font-size:2rem;font-weight:900;letter-spacing:-0.03em">{wsp:,}</div>
        </div>
        <div style="color:rgba(255,255,255,0.35);font-size:1.4rem;font-weight:300">→</div>
        <div>
          <div style="color:rgba(255,255,255,0.5);font-size:0.62rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.08em">Llegan a Relif</div>
          <div style="color:{BCI_YELLOW};font-size:2rem;font-weight:900;letter-spacing:-0.03em">{relif_top:,}</div>
        </div>
      </div>
      <div>{conv_html}</div>
    </div>
    <div style="text-align:center;color:#cbd5e1;font-size:1rem;margin-bottom:0.3rem">↓</div>
    """, unsafe_allow_html=True)

def render_buk_card(buk, relif_top: int, canal: str, accent: str):
    """Card compacta pre-funnel para la vista de todos los canales."""
    cfg       = CANAL_SHEET.get(canal, {})
    wsp_label = cfg.get("wsp_label", "Van al WhatsApp")

    CARD_H = "148px"

    if not buk or not buk.get("abren"):
        st.markdown(f"""
        <div style="background:{accent}12;border:1.5px dashed {accent}40;border-radius:14px;
                    height:{CARD_H};display:flex;flex-direction:column;align-items:center;
                    justify-content:center;text-align:center;margin-bottom:0.5rem">
          <div style="color:{accent};font-size:0.62rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.1em;margin-bottom:6px">{canal}</div>
          <div style="color:#94a3b8;font-size:0.75rem">Sin datos pre-Relif en Buk</div>
        </div>
        <div style="text-align:center;color:#cbd5e1;font-size:0.9rem;margin-bottom:0.3rem">↓</div>
        """, unsafe_allow_html=True)
        return

    abren    = buk.get("abren") or 0
    wsp      = buk.get("whatsapp") or 0
    conv_pct = round(relif_top / abren * 100, 1) if abren else None
    conv_str = f"{conv_pct}% llegó" if conv_pct else ""

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#001f5c,{accent});border-radius:14px;
                height:{CARD_H};padding:1.1rem 1.2rem;margin-bottom:0.5rem;
                display:flex;flex-direction:column;justify-content:space-between">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="color:rgba(255,255,255,0.45);font-size:0.6rem;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.1em">Pre-Relif · Buk</div>
        {"" if not conv_str else f'<span style="background:#fff3cd;color:#92400e;font-size:0.68rem;font-weight:700;padding:2px 8px;border-radius:99px">&#8594; {conv_str}</span>'}
      </div>
      <div style="display:grid;grid-template-columns:1fr auto 1fr auto 1fr;align-items:center;gap:4px">
        <div style="text-align:center">
          <div style="color:rgba(255,255,255,0.45);font-size:0.55rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.07em;margin-bottom:3px">Abren</div>
          <div style="color:white;font-size:1.25rem;font-weight:900;letter-spacing:-0.02em">{abren:,}</div>
        </div>
        <div style="color:rgba(255,255,255,0.3);font-size:1rem;text-align:center">&#8594;</div>
        <div style="text-align:center">
          <div style="color:rgba(255,255,255,0.45);font-size:0.55rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.07em;margin-bottom:3px">{wsp_label}</div>
          <div style="color:white;font-size:1.25rem;font-weight:900;letter-spacing:-0.02em">{wsp:,}</div>
        </div>
        <div style="color:rgba(255,255,255,0.3);font-size:1rem;text-align:center">&#8594;</div>
        <div style="text-align:center">
          <div style="color:rgba(255,255,255,0.45);font-size:0.55rem;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.07em;margin-bottom:3px">Relif</div>
          <div style="color:{BCI_YELLOW};font-size:1.25rem;font-weight:900;letter-spacing:-0.02em">{relif_top:,}</div>
        </div>
      </div>
    </div>
    <div style="text-align:center;color:#cbd5e1;font-size:0.9rem;margin-bottom:0.3rem">↓</div>
    """, unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1.2rem 0 0.8rem;text-align:center'>
      <div style='font-size:1.4rem;font-weight:900;color:white;letter-spacing:0.02em'>relif</div>
      <div style='font-size:0.6rem;color:#475569;font-weight:700;letter-spacing:0.14em;
                  text-transform:uppercase;margin-top:3px'>FUNNEL · ANALYTICS</div>
    </div>
    <hr style='border-color:#1e293b;margin:0 0 1.2rem'>
    """, unsafe_allow_html=True)

    canales_opts = list(CANALES.keys())

    _CHIP_COLORS = {
        "BCI Buk":        BCI_BLUE,
        "Cashback":       BCI_GREEN,
        "Estanque Copec": BCI_RED,
    }

    st.markdown("""
    <style>
    /* Chips de canal en sidebar */
    [data-testid="stSidebar"] .canal-chip-row {
        display: flex; flex-direction: column; gap: 6px; margin-bottom: 4px;
    }
    [data-testid="stSidebar"] div[data-testid="stCheckbox"] {
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        padding: 8px 12px;
        border: 1px solid rgba(255,255,255,0.08);
        transition: background 0.15s;
    }
    [data-testid="stSidebar"] div[data-testid="stCheckbox"]:has(input:checked) {
        background: rgba(255,255,255,0.12);
        border-color: rgba(255,255,255,0.2);
    }
    [data-testid="stSidebar"] div[data-testid="stCheckbox"] label {
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        color: #e2e8f0 !important;
        cursor: pointer;
    }
    [data-testid="stSidebar"] div[data-testid="stCheckbox"] input[type="checkbox"] {
        accent-color: #3b82f6;
        width: 15px; height: 15px;
    }
    </style>
    <div style="font-size:0.68rem;font-weight:700;color:#475569;text-transform:uppercase;
                letter-spacing:0.12em;margin-bottom:10px">Canales</div>
    """, unsafe_allow_html=True)

    canales_sel = []
    for _c in canales_opts:
        _color = _CHIP_COLORS[_c]
        _dot   = f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{_color};margin-right:6px;vertical-align:middle"></span>'
        _default = st.session_state.get(f"_sel_{_c}", True)
        _checked = st.checkbox(_c, value=_default, key=f"_chk_{_c}")
        st.session_state[f"_sel_{_c}"] = _checked
        if _checked:
            canales_sel.append(_c)

    hoy    = date.today()
    inicio = st.date_input("Desde", value=date(hoy.year, hoy.month, 1))
    fin    = st.date_input("Hasta", value=hoy)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar", use_container_width=True):
        st.session_state.pop("_funnel_cache", None); st.rerun()

# ── Header ────────────────────────────────────────────────────────────────
canales_vis = canales_sel if canales_sel else canales_opts
n_vis = len(canales_vis)

_vista_label = (
    canales_vis[0] if n_vis == 1
    else " vs ".join(canales_vis) if n_vis == 2
    else "Todos los canales"
)
periodo = f"{inicio.strftime('%d %b %Y')} → {fin.strftime('%d %b %Y')}"
st.markdown(f"""
<div style="background:linear-gradient(135deg,#001f5c 0%,#003DA5 60%,#1A5FD4 100%);
            border-radius:18px;padding:2rem 2.5rem;margin-bottom:1.8rem;
            display:flex;align-items:center;justify-content:space-between">
  <div>
    <div style="color:white;font-size:1.7rem;font-weight:900;letter-spacing:-0.02em">
      Funnel BCI · {_vista_label}
    </div>
    <div style="color:#93c5fd;font-size:0.85rem;margin-top:5px;font-weight:500">
      Fuente de la verdad &nbsp;·&nbsp; {periodo}
    </div>
  </div>
  <div style="color:#475569;font-size:0.78rem;text-align:right;line-height:1.9">
    <div style="color:#64748b;font-size:0.62rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.1em">Vista activa</div>
    <div style="color:white;font-size:1rem;font-weight:700">{_vista_label}</div>
  </div>
</div>
""", unsafe_allow_html=True)

if n_vis == 0:
    st.info("Selecciona al menos un canal en el sidebar.")
    st.stop()

# ── Carga ─────────────────────────────────────────────────────────────────
import time as _time
start_str = str(inicio)
end_str   = str(fin + timedelta(days=1))

_cache_key = f"{','.join(canales_vis)}|{start_str}|{end_str}"
_cached    = st.session_state.get("_funnel_cache", {}).get(_cache_key)

if _cached and _time.time() - _cached["ts"] < 300:
    all_data   = _cached["all_data"]
    buk_sheets = _cached["buk_sheets"]
else:
    with st.spinner("Cargando datos…"):
        _tz  = pytz.timezone("America/Santiago")
        _fmt = "%Y-%m-%dT%H:%M:%SZ"
        s_ts = "'" + _tz.localize(datetime.strptime(start_str, "%Y-%m-%d")).astimezone(pytz.utc).strftime(_fmt) + "'"
        e_ts = "'" + _tz.localize(datetime.strptime(end_str,   "%Y-%m-%d")).astimezone(pytz.utc).strftime(_fmt) + "'"

        sql_tasks = {}
        for c in canales_vis:
            qc, qb, qr = _build_sql(c, s_ts, e_ts)
            sql_tasks[(c, "c")] = qc
            sql_tasks[(c, "b")] = qb
            sql_tasks[(c, "r")] = qr

        # Sheet en background; queries API secuenciales para no saturar el servidor
        from concurrent.futures import ThreadPoolExecutor
        import threading as _threading
        _sheets_box = {}
        _sheet_thread = _threading.Thread(target=lambda: _sheets_box.update(load_buk_sheets() or {}))
        _sheet_thread.start()

        raw = {key: _api(sql) for key, sql in sql_tasks.items()}

        _sheet_thread.join()
        buk_sheets = _sheets_box

        all_data = {
            c: _assemble(
                c,
                (raw[(c, "c")] or [{}])[0],
                (raw[(c, "b")] or [{}])[0],
                raw[(c, "r")] or [],
            )
            for c in canales_vis
        }

        for c in canales_vis:
            all_data[c]["sheet_vals"] = get_buk_values(buk_sheets, c, inicio, fin)

        cache = st.session_state.get("_funnel_cache", {})
        cache[_cache_key] = {"all_data": all_data, "buk_sheets": buk_sheets, "ts": _time.time()}
        st.session_state["_funnel_cache"] = cache

# ── Helpers ───────────────────────────────────────────────────────────────
def make_funnel_html(canal: str, data: dict, compact: bool = False) -> str:
    cfg    = CANALES[canal]
    sv     = data.get("sheet_vals") or {}
    vals   = data["values"] + [sv.get("gestionados") or 0, sv.get("ventas") or 0]
    colors = cfg["colors"]
    top    = vals[0] or 1
    h_bar  = 34 if compact else 44
    lbl_w  = 108 if compact else 148
    fsize  = "0.63rem" if compact else "0.72rem"
    nsize  = "0.8rem"  if compact else "0.88rem"

    rows = []
    for i, (label, val, color) in enumerate(zip(STAGE_LABELS, vals, colors)):
        pct_total = round(val / top * 100)
        bar_w     = min(max(pct_total, 3 if val > 0 else 0), 100)

        # Drop connector row — siempre con la misma altura para espaciado uniforme
        if i > 0:
            if vals[i - 1] > 0:
                drop = round((1 - val / vals[i - 1]) * 100)
                dc   = "#ef4444" if drop > 40 else "#f59e0b" if drop > 15 else "#10b981"
                inner = (
                    '<div style="width:1px;height:11px;background:#dde1e7"></div>'
                    '<span style="font-size:0.57rem;font-weight:700;color:' + dc + ';letter-spacing:0.04em">'
                    '&darr;&nbsp;' + str(drop) + '%</span>'
                )
            else:
                inner = '<div style="height:13px"></div>'
            rows.append(
                '<div style="display:flex;align-items:center;gap:4px;padding:1px 0;'
                'margin-left:' + str(lbl_w + 10) + 'px">' + inner + '</div>'
            )

        inside = bar_w >= 16
        pct_badge = (
            '<span style="font-size:0.6rem;opacity:0.75;margin-left:4px">' + str(pct_total) + '%</span>'
        ) if i > 0 else ''

        if inside:
            lbl_html = (
                '<div style="width:' + str(lbl_w) + 'px;text-align:right;font-size:' + fsize + ';'
                'font-weight:600;color:#64748b;flex-shrink:0;padding-right:6px;line-height:1.3">'
                + label + '</div>'
            )
            txt_color = cfg["accent"] if i == 0 else "white"
            bar_inner = (
                '<div style="padding-left:10px;color:' + txt_color + ';white-space:nowrap">'
                '<span style="font-weight:900;font-size:' + nsize + '">' + f'{val:,}' + '</span>'
                + pct_badge + '</div>'
            )
        else:
            lbl_html = (
                '<div style="width:' + str(lbl_w) + 'px;text-align:right;font-size:' + fsize + ';'
                'font-weight:600;color:#64748b;flex-shrink:0;padding-right:6px;line-height:1.25">'
                + label + '<br>'
                '<span style="color:#1e293b;font-weight:900;font-size:' + nsize + '">'
                + f'{val:,}' + '</span>' + pct_badge + '</div>'
            )
            bar_inner = ''

        gap = "2px" if compact else "3px"
        rows.append(
            '<div style="display:flex;align-items:center;gap:8px;margin:' + gap + ' 0">'
            + lbl_html
            + '<div style="flex:1;height:' + str(h_bar) + 'px;background:#f1f5f9;border-radius:8px;overflow:hidden">'
            '<div style="width:' + str(bar_w) + '%;height:100%;background:' + color + ';border-radius:8px;'
            'display:flex;align-items:center;box-shadow:inset 0 -2px 0 rgba(0,0,0,0.07)">'
            + bar_inner
            + '</div></div></div>'
        )

    return '<div style="padding:6px 0 8px">' + ''.join(rows) + '</div>'

def kpi_card(label: str, val: int, color: str, sub: str = "") -> str:
    return f"""
    <div class="kpi" style="border-top:3px solid {color}">
      <div class="kpi-lbl">{label}</div>
      <div class="kpi-val" style="color:{color}">{val:,}</div>
      <div class="kpi-sub">{sub}</div>
    </div>"""

def rej_breakdown(data: dict, accent: str):
    cats  = data["rej_cats"]
    total = sum(cats.values()) or 1
    icons = {"Ya es cliente BCI":"👤","No pasa filtros de riesgo":"⚠️","Sin datos":"❓"}
    st.markdown('<div class="section-title">Motivos de rechazo</div>', unsafe_allow_html=True)
    for cat, c in cats.items():
        pct = round(c/total*100)
        icon = icons.get(cat, "📌")
        bar  = max(pct, 3)
        st.markdown(f"""
        <div class="rej-card">
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px">
            <span style="font-size:0.78rem;font-weight:600;color:#374151">{icon} {cat}</span>
            <span style="font-size:1.1rem;font-weight:800;color:#0f172a">{c:,}
              <span style="font-size:0.68rem;font-weight:500;color:#94a3b8">&nbsp;{pct}%</span>
            </span>
          </div>
          <div style="height:4px;background:#f1f5f9;border-radius:99px">
            <div style="height:4px;width:{bar}%;background:{accent};border-radius:99px;opacity:0.7"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Split pasan / no pasan
    pasan    = data["values"][4]
    no_pasan = data["rejected"]
    total_bor = pasan + no_pasan
    p_pct  = round(pasan/total_bor*100) if total_bor else 0
    np_pct = 100 - p_pct
    st.markdown('<div class="section-title">Pre-evaluación BCI</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display:flex;gap:8px">
      <div style="flex:1;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;
                  padding:1rem;text-align:center">
        <div style="font-size:1.6rem;font-weight:900;color:#15803d">{pasan:,}</div>
        <div style="font-size:0.7rem;font-weight:700;color:#166534;margin-top:2px">
          Pasan ✓ · {p_pct}%</div>
      </div>
      <div style="flex:1;background:#fef2f2;border:1px solid #fecaca;border-radius:12px;
                  padding:1rem;text-align:center">
        <div style="font-size:1.6rem;font-weight:900;color:#dc2626">{no_pasan:,}</div>
        <div style="font-size:0.7rem;font-weight:700;color:#991b1b;margin-top:2px">
          No pasan ✗ · {np_pct}%</div>
      </div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# HELPER: tabla comparativa (reutilizable en vista 2 y 3 canales)
# ══════════════════════════════════════════════════════════════════════════
def render_tabla_comparativa(canales: list):
    st.markdown("---")
    _sheet_keys = ["gestionados", "ventas"]
    rows = []
    for i, label in enumerate(STAGE_LABELS):
        row = {"Etapa": label}
        for canal in canales:
            d    = all_data[canal]
            val  = d["values"][i] if i < 6 else (d.get("sheet_vals") or {}).get(_sheet_keys[i - 6]) or 0
            base = d["values"][0]
            pct  = f" ({round(val/base*100)}%)" if base and i > 0 else ""
            row[canal] = f"{val:,}{pct}"
        rows.append(row)
    df_tabla = pd.DataFrame(rows).set_index("Etapa")

    t_col, btn_col = st.columns([6, 1])
    with t_col:
        st.markdown('<div class="section-title">Tabla comparativa</div>', unsafe_allow_html=True)
    with btn_col:
        csv = df_tabla.to_csv(encoding="utf-8")
        st.download_button(
            label="⬇ CSV",
            data=csv,
            file_name=f"funnel_bci_{periodo.replace(' ', '').replace('→','-')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    st.dataframe(df_tabla, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════
# VISTA: canal único
# ══════════════════════════════════════════════════════════════════════════
if n_vis == 1:
    canal  = canales_vis[0]
    data   = all_data[canal]
    vals   = data["values"]
    cfg    = CANALES[canal]
    accent = cfg["accent"]
    top    = vals[0] or 1

    # — KPI cards —
    conv_total = round(vals[5]/top*100, 1) if top else 0
    sv_data    = data.get("sheet_vals") or {}
    ventas_val = sv_data.get("ventas") or 0
    c1, c2, c3, c4 = st.columns(4)
    for col, label, val, color, sub in [
        (c1, "Llegaron a Relif",      vals[0],    accent,    f"Período: {periodo}"),
        (c2, "Dieron consentimiento", vals[2],    "#0891b2", f"{round(vals[2]/top*100)}% del total"),
        (c3, "Enviados al banco",     vals[5],    "#059669", f"Conversión: {conv_total}%"),
        (c4, "Venta Plan",            ventas_val, "#7c3aed", "Fuente: planilla"),
    ]:
        with col:
            st.markdown(kpi_card(label, val, color, sub), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # — Banner Buk pre-funnel —
    render_buk_banner(data.get("sheet_vals"), vals[0], canal, accent)

    # — Funnel + panel derecho —
    f_col, r_col = st.columns([3, 1], gap="large")

    with f_col:
        st.markdown(
            '<div style="background:white;border-radius:16px;padding:1.4rem 1.6rem 1rem;'
            'border:1px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,.05)">'
            + make_funnel_html(canal, data) + '</div>',
            unsafe_allow_html=True,
        )

    with r_col:
        st.markdown(f"""
        <div style="background:{accent};border-radius:14px;padding:1.3rem;text-align:center;margin-bottom:1rem">
          <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                      letter-spacing:0.12em;color:rgba(255,255,255,0.65)">Conversión total</div>
          <div style="font-size:2.8rem;font-weight:900;color:white;letter-spacing:-0.04em;
                      line-height:1.1">{conv_total}%</div>
          <div style="font-size:0.72rem;color:rgba(255,255,255,0.65);margin-top:2px">
            Llegaron → Enviados</div>
        </div>""", unsafe_allow_html=True)
        rej_breakdown(data, accent)


# ══════════════════════════════════════════════════════════════════════════
# VISTA: comparación 2 canales
# ══════════════════════════════════════════════════════════════════════════
elif n_vis == 2:
    # — KPI resumen —
    k_cols = st.columns(2)
    for col, canal in zip(k_cols, canales_vis):
        d = all_data[canal]; v = d["values"]; cfg = CANALES[canal]
        top_c = v[0] or 1
        conv  = round(v[5]/top_c*100, 1)
        sv    = d.get("sheet_vals") or {}
        ventas_val = sv.get("ventas") or 0
        with col:
            st.markdown(f"""
            <div class="kpi" style="border-top:4px solid {cfg['accent']}">
              <div class="kpi-lbl">{canal}</div>
              <div class="kpi-val" style="color:{cfg['accent']}">{v[0]:,}</div>
              <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px">
                <div style="text-align:center">
                  <div style="font-size:0.6rem;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.07em">Pre-eval.</div>
                  <div style="font-size:1.1rem;font-weight:800;color:#0f172a">{v[3]:,}</div>
                </div>
                <div style="text-align:center">
                  <div style="font-size:0.6rem;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.07em">Enviados</div>
                  <div style="font-size:1.1rem;font-weight:800;color:#059669">{v[5]:,}</div>
                </div>
                <div style="text-align:center">
                  <div style="font-size:0.6rem;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.07em">Conversión</div>
                  <div style="font-size:1.1rem;font-weight:800;color:{'#059669' if conv>=5 else '#d97706'}">{conv}%</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # — Buk cards —
    b_cols = st.columns(2, gap="medium")
    for b_col, c in zip(b_cols, canales_vis):
        with b_col:
            render_buk_card(all_data[c].get("sheet_vals"), all_data[c]["values"][0], c, CANALES[c]["accent"])

    # — 2 funnels lado a lado —
    f_cols = st.columns(2, gap="large")
    for col, canal in zip(f_cols, canales_vis):
        with col:
            cfg  = CANALES[canal]
            v    = all_data[canal]["values"]
            conv = round(v[5] / v[0] * 100, 1) if v[0] else 0
            conv_color = "#059669" if conv >= 5 else "#d97706"
            header = (
                '<div style="background:white;border-radius:16px;padding:1.3rem 1.4rem 0.8rem;'
                'border:1px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,.05)">'
                '<div style="display:flex;justify-content:space-between;align-items:center;'
                'margin-bottom:0.9rem;padding-bottom:0.6rem;border-bottom:3px solid '
                + cfg["accent"] + '30">'
                '<span style="font-size:0.9rem;font-weight:800;color:' + cfg["accent"] + '">'
                + canal + '</span>'
                '<span style="font-size:0.75rem;font-weight:700;color:' + conv_color + '">'
                + str(conv) + '% conv.</span></div>'
            )
            st.markdown(
                header + make_funnel_html(canal, all_data[canal], compact=True) + '</div>',
                unsafe_allow_html=True,
            )

    render_tabla_comparativa(canales_vis)


# ══════════════════════════════════════════════════════════════════════════
# VISTA: todos los canales (3)
# ══════════════════════════════════════════════════════════════════════════
else:
    # — KPI resumen —
    k_cols = st.columns(len(canales_vis))
    for col, canal in zip(k_cols, canales_vis):
        d = all_data[canal]; v = d["values"]; cfg = CANALES[canal]
        conv = round(v[5]/v[0]*100, 1) if v[0] else 0
        with col:
            st.markdown(f"""
            <div class="kpi" style="border-top:3px solid {cfg['accent']}">
              <div class="kpi-lbl">{canal}</div>
              <div class="kpi-val" style="color:{cfg['accent']}">{v[0]:,}</div>
              <div style="display:flex;justify-content:space-between;margin-top:10px">
                <span style="font-size:0.78rem;color:#374151"><b>{v[3]:,}</b> pre-eval.</span>
                <span style="font-size:0.78rem;font-weight:700;
                             color:{'#059669' if conv>=5 else '#d97706'}">{conv}% conv.</span>
              </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # — Buk cards —
    b_cols = st.columns(len(canales_vis), gap="medium")
    for b_col, c in zip(b_cols, canales_vis):
        with b_col:
            render_buk_card(all_data[c].get("sheet_vals"), all_data[c]["values"][0], c, CANALES[c]["accent"])

    # — Funnels lado a lado —
    f_cols = st.columns(len(canales_vis), gap="medium")
    for col, canal in zip(f_cols, canales_vis):
        with col:
            cfg  = CANALES[canal]
            v    = all_data[canal]["values"]
            conv = round(v[5] / v[0] * 100, 1) if v[0] else 0
            conv_color = "#059669" if conv >= 5 else "#d97706"
            header = (
                '<div style="background:white;border-radius:16px;padding:1.1rem 1rem 0.8rem;'
                'border:1px solid #e2e8f0;box-shadow:0 1px 6px rgba(0,0,0,.05)">'
                '<div style="display:flex;justify-content:space-between;align-items:center;'
                'margin-bottom:0.7rem;padding-bottom:0.5rem;border-bottom:2px solid '
                + cfg["accent"] + '28">'
                '<span style="font-size:0.82rem;font-weight:800;color:' + cfg["accent"] + '">'
                + canal + '</span>'
                '<span style="font-size:0.7rem;font-weight:700;color:' + conv_color + '">'
                + str(conv) + '% conv.</span></div>'
            )
            st.markdown(
                header + make_funnel_html(canal, all_data[canal], compact=True) + '</div>',
                unsafe_allow_html=True,
            )

    render_tabla_comparativa(canales_vis)
