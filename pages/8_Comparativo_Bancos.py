"""Panel comparativo de los 3 bancos principales."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import date, timedelta
from pathlib import Path
import base64
from utils import fetch_data, CARD_CSS

try:
    st.set_page_config(page_title="Comparativo Bancos", page_icon="https://relif.com/favicon.png", layout="wide")
except Exception:
    pass

st.markdown(CARD_CSS, unsafe_allow_html=True)
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
    font-size:0.72rem;font-weight:600;padding:0.25rem 0.6rem;border-radius:999px;
    background:#f1f5f9;border:1px solid #e2e8f0;color:#475569;transition:all 0.15s;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button:hover {
    background:#e2e8f0;color:#0f172a;
}
</style>""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
_logo_path = Path(__file__).parent.parent / "relif-logo-DkXo5dGJ.png"
_logo_b64  = base64.b64encode(_logo_path.read_bytes()).decode() if _logo_path.exists() else ""
_logo_html = (
    f'<img src="data:image/png;base64,{_logo_b64}" style="height:52px;filter:brightness(0) invert(1);opacity:0.95">'
    if _logo_b64 else '<span style="font-size:1.4rem;font-weight:800;color:white">relif</span>'
)
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#1d4ed8 100%);
            border-radius:0 0 20px 20px;padding:2.4rem 2.5rem 2.2rem;
            margin:-1rem -2rem 1.5rem;position:relative;overflow:hidden">
    <div style="position:absolute;top:-30px;right:-30px;width:200px;height:200px;
                background:rgba(255,255,255,0.04);border-radius:50%"></div>
    <div style="position:relative;z-index:1;display:flex;align-items:center;justify-content:space-between">
        <div>
            <div style="display:inline-block;font-size:0.6rem;font-weight:700;text-transform:uppercase;
                        letter-spacing:0.12em;color:#93c5fd;background:rgba(147,197,253,0.15);
                        border:1px solid rgba(147,197,253,0.35);border-radius:999px;
                        padding:0.2rem 0.75rem;margin-bottom:0.6rem">Comparativo</div>
            <div style="font-size:1.6rem;font-weight:800;color:white;letter-spacing:-0.02em">
                Resumen por Banco
            </div>
        </div>
        {_logo_html}
    </div>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:1rem 0 0.5rem'>"
        "<span style='font-size:1.1rem;font-weight:700;color:#f1f5f9'>RELIF</span>"
        "<span style='font-size:0.7rem;color:#64748b;display:block;margin-top:2px'>Analytics</span>"
        "</div><hr style='border-color:#1e293b;margin:0.5rem 0 1rem'>",
        unsafe_allow_html=True,
    )
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Presets de fecha ──────────────────────────────────────────────────────
_today = date.today()
_presets = [
    ("Hoy",      _today,                       _today + timedelta(days=1)),
    ("7 días",   _today - timedelta(days=7),   _today + timedelta(days=1)),
    ("15 días",  _today - timedelta(days=15),  _today + timedelta(days=1)),
    ("Este mes", _today.replace(day=1),         _today + timedelta(days=1)),
    ("30 días",  _today - timedelta(days=30),  _today + timedelta(days=1)),
]
_pb = st.columns(len(_presets))
for i, (lbl, ps, pe) in enumerate(_presets):
    with _pb[i]:
        if st.button(lbl, key=f"preset_{lbl}_comp", use_container_width=True):
            st.session_state["sd_comp"] = ps
            st.session_state["ed_comp"] = pe
            st.rerun()

dc1, dc2 = st.columns(2)
with dc1:
    start_date = st.date_input("Desde", value=_today, key="sd_comp")
with dc2:
    end_date = st.date_input("Hasta", value=_today + timedelta(days=1), key="ed_comp")

delta_days = max((end_date - start_date).days, 1)
if delta_days <= 7:
    prev_start = str(start_date - timedelta(weeks=1))
    prev_end   = str(end_date   - timedelta(weeks=1))
else:
    prev_start = str(start_date - timedelta(days=delta_days))
    prev_end   = str(start_date)

# ── Cargar datos ──────────────────────────────────────────────────────────
try:
    with st.spinner("Cargando datos..."):
        df_dedup      = fetch_data(str(start_date), str(end_date), dedup_clients=True)
        df_dedup_prev = fetch_data(prev_start, prev_end, dedup_clients=True)
        df_all        = fetch_data(str(start_date), str(end_date), dedup_clients=False)
        df_all_prev   = fetch_data(prev_start, prev_end, dedup_clients=False)
except Exception as e:
    st.error(f"Error al cargar datos: {e}")
    st.stop()

def _filter(df, bank):
    if df.empty: return df
    return df[df["bank"] == bank].copy()

def _dedup(df):
    if df.empty: return df
    return df.drop_duplicates(subset=["rut"])

def _no_nulls(df):
    if df.empty or "clientId" not in df.columns: return df
    return df[df["clientId"].notna()]

bci      = _dedup(_filter(df_dedup,      "BCI"))
bci_prev = _dedup(_filter(df_dedup_prev, "BCI"))
bi       = _no_nulls(_filter(df_all,      "Banco Internacional"))
bi_prev  = _no_nulls(_filter(df_all_prev, "Banco Internacional"))
sc       = _dedup(_filter(df_dedup,      "Scotiabank"))
sc_prev  = _dedup(_filter(df_dedup_prev, "Scotiabank"))

# ── Helpers de cálculo ────────────────────────────────────────────────────
def _n(df, status=None):
    if df.empty: return 0
    if status: return int((df["status"] == status).sum())
    return len(df)

def _pct_change(curr, prev):
    if not prev: return None
    return (curr - prev) / prev * 100

def _badge(curr, prev, invert=False):
    p = _pct_change(curr, prev)
    if p is None: return ""
    up = p >= 0
    if invert: up = not up
    color = "#16a34a" if up else "#dc2626"
    arrow = "▲" if p >= 0 else "▼"
    bg    = "#f0fdf4" if up else "#fef2f2"
    return (
        f'<span style="font-size:0.72rem;font-weight:700;color:{color};'
        f'background:{bg};border-radius:999px;padding:0.1rem 0.5rem;'
        f'white-space:nowrap">{arrow} {abs(p):.0f}%</span>'
    )

def _row(label, value, prev, color="#0f172a", fmt=None, invert=False, dash=False):
    if dash:
        val_html = '<span style="color:#cbd5e1;font-size:0.9rem">—</span>'
        badge_html = ""
    else:
        val_str = fmt(value) if fmt else (f"{value:,}".replace(",", "."))
        val_html = f'<span style="font-size:1.4rem;font-weight:800;color:{color};letter-spacing:-0.02em">{val_str}</span>'
        badge_html = _badge(value, prev, invert)
    return (
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'padding:0.7rem 0;border-bottom:1px solid #f1f5f9">'
        f'<span style="font-size:0.78rem;color:#64748b;font-weight:500">{label}</span>'
        f'<div style="display:flex;align-items:center;gap:0.5rem">{val_html}</div>'
        f'</div>'
    )

def _card(badge_label, badge_class, name, subtitle, rows_html, accent):
    badge_styles = {
        "bci": "background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe",
        "bi":  "background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0",
        "sc":  "background:#fef3c7;color:#d97706;border:1px solid #fde68a",
    }
    return f"""
    <div style="background:white;border:1px solid #e2e8f0;border-top:3px solid {accent};
                border-radius:14px;padding:1.4rem 1.4rem 0.6rem;
                box-shadow:0 1px 4px rgba(0,0,0,.05)">
        <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;
                    {badge_styles[badge_class]};display:inline-block;
                    border-radius:999px;padding:0.15rem 0.6rem;margin-bottom:0.6rem">
            {badge_label}
        </div>
        <div style="font-size:1rem;font-weight:800;color:#0f172a;margin-bottom:0.1rem">{name}</div>
        <div style="font-size:0.68rem;color:#94a3b8;text-transform:uppercase;
                    letter-spacing:0.07em;margin-bottom:0.6rem">{subtitle}</div>
        {rows_html}
    </div>"""

# ── Panel ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="display:flex;align-items:center;gap:0.8rem;margin:1.8rem 0 1.2rem">'
    '<span style="font-size:0.65rem;font-weight:700;text-transform:uppercase;'
    'letter-spacing:0.1em;color:#94a3b8;white-space:nowrap">Resumen por banco</span>'
    '<div style="flex:1;height:1px;background:#e2e8f0"></div></div>',
    unsafe_allow_html=True,
)

col_bci, col_bi, col_sc = st.columns(3)

with col_bci:
    t  = _n(bci);       tp = _n(bci_prev)
    e  = _n(bci, "sent_to_bank"); ep = _n(bci_prev, "sent_to_bank")
    r  = _n(bci, "rejected_by_bank"); rp = _n(bci_prev, "rejected_by_bank")
    ta = round(e/t*100) if t else 0; tap = round(ep/tp*100) if tp else 0
    rows = (
        _row("Total Requests",   t,  tp, "#2563eb") +
        _row("Enviados al banco", e,  ep, "#16a34a") +
        _row("Rechazados",        r,  rp, "#dc2626", invert=True) +
        _row("Tasa de envío",    ta, tap, "#d97706", fmt=lambda v: f"{v}%")
    )
    st.markdown(_card("BCI", "bci", "Banco de Crédito e Inversiones", "Flujo con pre-aprobación", rows, "#2563eb"), unsafe_allow_html=True)

with col_bi:
    t  = _n(bi);       tp = _n(bi_prev)
    e  = _n(bi, "sent_to_bank"); ep = _n(bi_prev, "sent_to_bank")
    r  = _n(bi, "rejected_by_bank"); rp = _n(bi_prev, "rejected_by_bank")
    ta = round(e/t*100) if t else 0; tap = round(ep/tp*100) if tp else 0
    rows = (
        _row("Total Requests",   t,  tp, "#2563eb") +
        _row("Enviados al banco", e,  ep, "#16a34a") +
        _row("Rechazados",        r,  rp, "#dc2626", invert=True) +
        _row("Tasa de envío",    ta, tap, "#d97706", fmt=lambda v: f"{v}%")
    )
    st.markdown(_card("Banco Internacional", "bi", "Banco Internacional", "Flujo con pre-aprobación", rows, "#16a34a"), unsafe_allow_html=True)

with col_sc:
    t  = _n(sc); tp = _n(sc_prev)
    rows = (
        _row("Total Requests", t, tp, "#2563eb") +
        _row("Enviados al banco", 0, 0, dash=True) +
        _row("Rechazados",        0, 0, dash=True) +
        _row("Tasa de envío",     0, 0, dash=True)
    )
    st.markdown(_card("Scotiabank", "sc", "Scotiabank", "Solo tracking de requests", rows, "#d97706"), unsafe_allow_html=True)
