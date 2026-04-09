"""Página Funnel BCI × Buk."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from utils import CARD_CSS

# set_page_config lo maneja BCI_App.py cuando se carga via st.navigation()
try:
    st.set_page_config(page_title="Funnel BCI", page_icon="https://relif.com/favicon.png", layout="wide")
except Exception:
    pass

# ── Constantes ───────────────────────────────────────────────────────
SHEET_ID  = "1Pkm4kX6dRRH0_Ar759E3ynKevK69WgTl"
GID       = "815440498"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

MONTHS = ["feb-26", "mar-26", "abr-26", "may-26", "jun-26",
          "jul-26", "ago-26", "sept-26", "oct-26", "nov-26", "dic-26"]

REAL_COL = {
    "feb-26": 9, "mar-26": 10, "abr-26": 11, "may-26": 13,
    "jun-26": 14, "jul-26": 15, "ago-26": 16, "sept-26": 17,
    "oct-26": 18, "nov-26": 19, "dic-26": 20,
}
PPTO_COL = {
    "feb-26": 23, "mar-26": 24, "abr-26": 25, "may-26": 27,
    "jun-26": 28, "jul-26": 29, "ago-26": 30, "sept-26": 31,
    "oct-26": 32, "nov-26": 33, "dic-26": 34,
}

# KPIs contextuales (sobre el funnel)
COUNTERS = [
    {"kpi": "MAU Buk (usuarios activos mensuales), #",               "label": "MAU Buk",         "icon": "👥", "color": "#1e3a8a"},
    {"kpi": "Tenants (comercios, RUT empresa) con llave abierta, #", "label": "Tenants Activos", "icon": "🏢", "color": "#1d4ed8"},
]

# Etapas del funnel (desde Simulador Crédito)
STAGES = [
    {"kpi": "Entran al simulador de Créditos by Buk, en Buk, %",    "label": "Simulador Crédito",   "color": "#3b82f6"},
    {"kpi": "RUTs con consentimiento a Buk, #",                      "label": "RUTs Consentimiento", "color": "#0ea5e9"},
    {"kpi": "Leads totales crédito Bci, #",                          "label": "Leads Totales BCI",   "color": "#22c55e"},
    {"kpi": "Leads derivados post FDR, #",                           "label": "Leads Derivados FDR", "color": "#16a34a"},
    {"kpi": "Recibidos en Bci, #",                                   "label": "Recibidos en BCI",    "color": "#15803d"},
    {"kpi": "Gestionados, #",                                        "label": "Gestionados",         "color": "#f59e0b"},
    {"kpi": "Aceptas, #",                                            "label": "Aceptas",             "color": "#ea580c"},
    {"kpi": "Venta, # acum",                                         "label": "Venta",               "color": "#dc2626"},
]

ANIM_CSS = """
<style>
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-card { opacity: 0; animation: fadeSlideUp 0.4s ease forwards; }
[data-testid="stSidebarCollapsedControl"] {
    width:48px!important;height:48px!important;
    background:linear-gradient(135deg,#0f172a,#1e293b)!important;
    border-radius:0 12px 12px 0!important;display:flex!important;
    align-items:center!important;justify-content:center!important;
    box-shadow:3px 0 12px rgba(0,0,0,.2)!important;border:none!important;
    top:18px!important;cursor:pointer!important;
}
[data-testid="stSidebarCollapsedControl"] svg{display:none!important}
[data-testid="stSidebarCollapsedControl"]::after{
    content:"R";color:#f1f5f9;font-family:'Inter',sans-serif;
    font-size:20px;font-weight:800;
}
</style>
"""


# ── Helpers ──────────────────────────────────────────────────────────
def _section_header(title: str):
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:0.8rem;margin:1.8rem 0 1rem">'
        f'<span style="font-size:0.65rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.1em;color:#94a3b8;white-space:nowrap">{title}</span>'
        f'<div style="flex:1;height:1px;background:#e2e8f0"></div></div>',
        unsafe_allow_html=True,
    )


def _parse(v):
    if pd.isna(v) or str(v).strip() in ("", "-", "N/A", "n/a", "confirmar jueves"):
        return None
    try:
        s = str(v).strip().replace("%", "").replace(" ", "")
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(".", "")
        return float(s)
    except Exception:
        return None


def _fmt(v, dash="—"):
    if v is None or v == 0:
        return dash
    return f"{v:,.0f}"


@st.cache_data(ttl=300, show_spinner=False)
def _load_sheet() -> pd.DataFrame:
    try:
        return pd.read_csv(SHEET_URL, header=None)
    except Exception:
        return pd.DataFrame()


def _row_for(df: pd.DataFrame, kpi: str):
    mask = df.iloc[:, 8].astype(str).str.strip() == kpi
    rows = df[mask]
    return rows.iloc[0] if not rows.empty else None


def _all_months_data(df: pd.DataFrame) -> dict:
    """Devuelve {month: {kpi: real_value}} para todos los meses."""
    result = {}
    for m in MONTHS:
        rc = REAL_COL[m]
        month_data = {}
        for stage in STAGES:
            row = _row_for(df, stage["kpi"])
            month_data[stage["kpi"]] = _parse(row.iloc[rc]) if row is not None else None
        result[m] = month_data
    return result


def _counter_data(df: pd.DataFrame) -> dict:
    """Devuelve {month: [val, val]} para los counters."""
    result = {}
    for m in MONTHS:
        rc = REAL_COL[m]
        vals = []
        for c in COUNTERS:
            row = _row_for(df, c["kpi"])
            vals.append(_parse(row.iloc[rc]) if row is not None else None)
        result[m] = vals
    return result


# ── Layout ───────────────────────────────────────────────────────────
st.markdown(CARD_CSS + ANIM_CSS, unsafe_allow_html=True)

# ── Header banner (igual al dashboard principal) ──
import base64
from pathlib import Path
_logo_path = Path(__file__).parent.parent / "relif-logo-DkXo5dGJ.png"
_logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode() if _logo_path.exists() else ""
_logo_html = (
    f'<img src="data:image/png;base64,{_logo_b64}" style="height:52px;filter:brightness(0) invert(1);opacity:0.95">'
    if _logo_b64 else '<span style="font-size:1.4rem;font-weight:800;color:white;letter-spacing:0.05em">relif</span>'
)
st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#1d4ed8 100%);
            border-radius:0 0 20px 20px;padding:2.4rem 2.5rem 2.2rem;
            margin:-1rem -2rem 1.5rem;position:relative;overflow:hidden">
    <div style="position:absolute;top:-30px;right:-30px;width:200px;height:200px;
                background:rgba(255,255,255,0.04);border-radius:50%"></div>
    <div style="position:absolute;bottom:-50px;right:80px;width:130px;height:130px;
                background:rgba(255,255,255,0.03);border-radius:50%"></div>
    <div style="position:relative;z-index:1;display:flex;align-items:center;justify-content:flex-end">
        {_logo_html}
    </div>
</div>""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown(
        "<div style='text-align:center;padding:1rem 0 0.5rem'>"
        "<span style='font-size:1.1rem;font-weight:700;color:#f1f5f9;letter-spacing:0.05em'>RELIF</span>"
        "<span style='font-size:0.7rem;color:#64748b;display:block;margin-top:2px'>Dashboard</span>"
        "</div><hr style='border-color:#1e293b;margin:0.5rem 0 1rem'>",
        unsafe_allow_html=True,
    )
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)

    from datetime import date
    _en_to_es = {
        "Jan": "ene-26", "Feb": "feb-26", "Mar": "mar-26", "Apr": "abr-26",
        "May": "may-26", "Jun": "jun-26", "Jul": "jul-26", "Aug": "ago-26",
        "Sep": "sept-26", "Oct": "oct-26", "Nov": "nov-26", "Dec": "dic-26",
    }
    _current_month = _en_to_es.get(date.today().strftime("%b"), MONTHS[0])
    _default_idx   = MONTHS.index(_current_month) if _current_month in MONTHS else 0
    sel_month = st.selectbox("Mes del funnel", MONTHS, index=_default_idx)

# Cargar datos
with st.spinner("Cargando datos del sheet..."):
    df_sheet = _load_sheet()

all_data     = _all_months_data(df_sheet)
counter_vals = _counter_data(df_sheet)

# Meses que tienen al menos un dato real
active_months = [m for m in MONTHS if any(v for v in all_data[m].values())]

# ── Conteos contextuales ──────────────────────────────────────────────
_section_header("Contexto de plataforma")

# Tomar el mes más reciente con dato para cada counter
_cnt_cols = st.columns(len(COUNTERS))
for col, c, ci in zip(_cnt_cols, COUNTERS, range(len(COUNTERS))):
    # último mes con valor
    val = None
    last_m = None
    for m in reversed(MONTHS):
        v = counter_vals[m][ci]
        if v:
            val = v; last_m = m; break
    _val_str = f"{val:,.0f}" if val else "—"
    with col:
        st.markdown(
            f'<div style="background:white;border:1px solid #e2e8f0;border-top:3px solid {c["color"]};'
            f'border-radius:12px;padding:1.1rem 1.3rem;box-shadow:0 1px 4px rgba(0,0,0,.05)">'
            f'<div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.08em;color:#94a3b8;margin-bottom:0.4rem">{c["icon"]} {c["label"]}</div>'
            f'<div style="font-size:1.9rem;font-weight:800;color:#0f172a;letter-spacing:-0.03em"'
            + (f' data-counter="{int(val)}"' if val else '') +
            f'>{_val_str}</div>'
            f'<div style="font-size:0.72rem;color:#64748b;margin-top:0.2rem">'
            + (f'último dato: {last_m}' if last_m else 'sin datos') +
            '</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Tabla real por mes ────────────────────────────────────────────────
_section_header("Real por mes")

if active_months:
    # Construir tabla
    rows_table = []
    for stage in STAGES:
        row = {"Etapa": stage["label"]}
        for m in active_months:
            row[m] = all_data[m][stage["kpi"]]
        rows_table.append(row)

    df_table = pd.DataFrame(rows_table).set_index("Etapa")

    # Heatmap HTML: más oscuro = más alto
    def _cell(val, max_val, color_hex):
        if val is None or val == 0:
            return '<td style="padding:0.5rem 0.9rem;color:#cbd5e1;text-align:right;font-size:0.84rem">—</td>'
        intensity = min(val / max_val, 1) if max_val else 0
        alpha     = 0.08 + intensity * 0.30
        return (
            f'<td style="padding:0.5rem 0.9rem;text-align:right;font-size:0.88rem;font-weight:600;'
            f'background:rgba({int(color_hex[1:3],16)},{int(color_hex[3:5],16)},{int(color_hex[5:7],16)},{alpha:.2f})">'
            f'{val:,.0f}</td>'
        )

    header_cells = "".join(
        f'<th style="padding:0.5rem 0.9rem;text-align:right;font-size:0.72rem;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.06em;color:#64748b;white-space:nowrap">{m}</th>'
        for m in active_months
    )

    body_rows = ""
    for stage in STAGES:
        vals_row = [all_data[m][stage["kpi"]] for m in active_months]
        max_v    = max((v for v in vals_row if v), default=1)
        cells    = "".join(_cell(v, max_v, stage["color"]) for v in vals_row)
        body_rows += (
            f'<tr>'
            f'<td style="padding:0.5rem 0.9rem;font-size:0.85rem;color:#374151;font-weight:500;'
            f'border-left:3px solid {stage["color"]};white-space:nowrap">{stage["label"]}</td>'
            f'{cells}</tr>'
        )

    st.markdown(
        '<div style="overflow-x:auto;background:white;border:1px solid #e2e8f0;border-radius:12px;'
        'box-shadow:0 1px 4px rgba(0,0,0,.05);padding:0.2rem 0">'
        '<table style="width:100%;border-collapse:collapse">'
        f'<thead><tr><th style="padding:0.5rem 0.9rem;text-align:left;font-size:0.72rem;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:0.06em;color:#64748b">Etapa</th>{header_cells}</tr></thead>'
        f'<tbody>{body_rows}</tbody>'
        '</table></div>',
        unsafe_allow_html=True,
    )
else:
    st.info("No hay datos reales aún en el sheet.")

# ── Funnel del mes seleccionado ───────────────────────────────────────
_section_header(f"Funnel de conversión — {sel_month}")

_month_vals  = [all_data[sel_month][s["kpi"]] for s in STAGES]
_month_pptos = []
for s in STAGES:
    row = _row_for(df_sheet, s["kpi"])
    _month_pptos.append(_parse(row.iloc[PPTO_COL[sel_month]]) if row is not None else None)

vals  = [v if v else 0 for v in _month_vals]
pptos = [v if v else 0 for v in _month_pptos]
labels = [s["label"] for s in STAGES]
colors = [s["color"] for s in STAGES]

funnel_col, detail_col = st.columns([3, 2])

with funnel_col:
    max_val = max((v for v in vals if v), default=1)

    texts, hovers = [], []
    for i, (stage, val) in enumerate(zip(STAGES, vals)):
        drop = ""
        if i > 0 and vals[i-1] and val:
            p = val / vals[i-1] * 100
            drop = f"  ↓{p:.0f}%"
        texts.append(f"<b>{val:,.0f}</b>{drop}" if val else "")
        ppto_txt = f"<br>Presupuesto: {pptos[i]:,.0f}" if pptos[i] else ""
        hovers.append(f"<b>{stage['label']}</b><br>Real: {val:,.0f}{ppto_txt}<extra></extra>")

    fig = go.Figure(data=[go.Bar(
        x=[0]*len(labels), y=labels, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[""]*len(labels), textposition="outside",
        textfont=dict(family="Inter", size=11, color="#374151"),
        hovertemplate=hovers, showlegend=False, width=0.65,
    )])
    fig.frames = [go.Frame(
        data=[go.Bar(x=vals, y=labels, text=texts,
                     marker=dict(color=colors, line=dict(width=0)))],
        name="loaded",
    )]
    fig.update_layout(
        updatemenus=[dict(
            type="buttons", visible=False, x=-2, y=-2,
            buttons=[dict(label="go", method="animate",
                          args=[["loaded"], {
                              "frame": {"duration": 900, "redraw": True},
                              "transition": {"duration": 900, "easing": "cubic-in-out"},
                              "mode": "immediate",
                          }])],
        )],
    )
    for i, ppto in enumerate(pptos):
        if ppto:
            y_pos = len(STAGES) - 1 - i
            fig.add_shape(type="line", x0=ppto, x1=ppto,
                          y0=y_pos-0.38, y1=y_pos+0.38,
                          line=dict(color="#cbd5e1", width=2, dash="dot"))
    fig.update_layout(
        height=420, margin=dict(t=10, b=10, l=170, r=200),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[0, max_val*1.6]),
        yaxis=dict(showgrid=False, tickfont=dict(family="Inter", size=11.5, color="#374151"),
                   categoryorder="array", categoryarray=labels[::-1]),
        font=dict(family="Inter"), bargap=0.28,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        '<div style="display:flex;gap:2rem;justify-content:center;margin-top:-0.5rem">'
        '<span style="font-size:0.74rem;color:#64748b">&#9632; Barra = Real &nbsp;|&nbsp; ↓% = caída vs paso anterior</span>'
        '<span style="font-size:0.74rem;color:#94a3b8">-- = Presupuesto</span></div>',
        unsafe_allow_html=True,
    )

with detail_col:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    for i, stage in enumerate(STAGES):
        real = vals[i]
        ppto = pptos[i]
        conv_html = ""
        if i > 0 and vals[i-1] and real:
            pct = real / vals[i-1] * 100
            c   = "#22c55e" if pct >= 60 else "#f59e0b" if pct >= 30 else "#ef4444"
            conv_html = f'<span style="font-size:0.72rem;font-weight:700;color:{c}">↓ {pct:.0f}% del anterior</span>'
        cumpl_html = ""
        if ppto and real:
            c2   = real / ppto * 100
            col2 = "#22c55e" if c2 >= 80 else "#f59e0b" if c2 >= 50 else "#ef4444"
            cumpl_html = f'<span style="font-size:0.7rem;color:{col2}">{c2:.0f}% del ppto</span>'

        val_str      = f"{real:,.0f}" if real else "—"
        counter_attr = f'data-counter="{real:.0f}"' if real else ""
        delay        = i * 0.07

        st.markdown(
            f'<div class="fade-card" style="display:flex;align-items:center;gap:0.8rem;'
            f'padding:0.55rem 0.9rem;background:white;border:1px solid #e2e8f0;'
            f'border-left:3px solid {stage["color"]};border-radius:10px;'
            f'margin-bottom:0.3rem;box-shadow:0 1px 3px rgba(0,0,0,.04);'
            f'animation-delay:{delay:.2f}s">'
            f'<div style="flex:1">'
            f'<div style="font-size:0.65rem;color:#94a3b8;font-weight:700;'
            f'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:1px">{stage["label"]}</div>'
            f'<div style="font-size:1.1rem;font-weight:700;color:#0f172a" {counter_attr}>{val_str}</div>'
            f'</div>'
            f'<div style="text-align:right;line-height:1.6">{conv_html}<br>{cumpl_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ── Conclusiones ──────────────────────────────────────────────────────
drops = [(1 - vals[i]/vals[i-1])*100 if vals[i] and vals[i-1] else None
         for i in range(1, len(vals))]
drops_named = [(d, STAGES[i]["label"], STAGES[i+1]["label"])
               for i, d in enumerate(drops) if d is not None]

if drops_named:
    _section_header("Conclusiones")
    drops_named.sort(reverse=True)
    overall = vals[-1]/vals[0]*100 if vals[0] and vals[-1] else 0
    insights = [
        f"Mayor caída: <b>{drops_named[0][1]}</b> → <b>{drops_named[0][2]}</b> "
        f"con <b>{drops_named[0][0]:.1f}%</b> de drop",
        f"Conversión total (Simulador → Venta): <b>{overall:.3f}%</b>",
    ]
    if pptos[-1] and vals[-1]:
        c = vals[-1]/pptos[-1]*100
        s = "🟢" if c >= 80 else "🟡" if c >= 50 else "🔴"
        insights.append(f"Ventas al <b>{c:.0f}%</b> del presupuesto {s}")

    items_html = "".join(f"<li style='margin-bottom:0.4rem'>{i}</li>" for i in insights)
    st.markdown(
        '<div class="fade-card" style="background:white;border:1px solid #e2e8f0;'
        'border-left:4px solid #8b5cf6;border-radius:14px;padding:1rem 1.4rem;'
        'box-shadow:0 1px 4px rgba(0,0,0,.05);animation-delay:0.3s">'
        '<p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;'
        'letter-spacing:0.1em;color:#94a3b8;margin:0 0 0.5rem">💡 Conclusiones</p>'
        f'<ul style="margin:0;padding-left:1.2rem;color:#374151;font-size:0.88rem;line-height:1.9">'
        f'{items_html}</ul></div>',
        unsafe_allow_html=True,
    )

# ── Animaciones JS ─────────────────────────────────────────────────────
components.html("""
<script>
(function(){
    function run(){
        var doc = window.parent.document;
        doc.querySelectorAll('[data-counter]').forEach(function(el){
            if(el.dataset.animated) return;
            el.dataset.animated='1';
            var target=parseFloat(el.getAttribute('data-counter'));
            var start=null;
            function step(ts){
                if(!start) start=ts;
                var t=Math.min((ts-start)/900,1);
                var e=1-Math.pow(1-t,3);
                el.textContent=Math.round(target*e).toLocaleString('es-CL');
                if(t<1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        });
        var Plotly=window.parent.Plotly;
        var plots=doc.querySelectorAll('.js-plotly-plot');
        if(Plotly&&plots.length>0){
            Plotly.animate(plots[0],['loaded'],{
                transition:{duration:900,easing:'cubic-in-out'},
                frame:{duration:900,redraw:true},mode:'immediate'
            });
        }
    }
    setTimeout(run,400);
})();
</script>
""", height=0)
