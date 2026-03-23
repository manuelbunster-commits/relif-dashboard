"""Página Funnel BCI × Buk."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from utils import CARD_CSS

st.set_page_config(page_title="Funnel BCI", page_icon="https://relif.com/favicon.png", layout="wide")

# ── Constantes ───────────────────────────────────────────────────────
SHEET_ID  = "1dtpkt9O1OxBe93-IS7gGtV5yd9zObiwv"
GID       = "1581819693"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

MONTHS = ["feb-26","mar-26","abr-26","may-26","jun-26",
          "jul-26","ago-26","sep-26","oct-26","nov-26","dic-26"]

STAGES = [
    {"kpi": "Usuarios ingresan Home, #",                       "label": "Usuarios Home",       "color": "#1d4ed8", "type": "#"},
    {"kpi": "Consultas API usuario (FDR, CCT, oferta), #",     "label": "Consultas API",        "color": "#2563eb", "type": "#"},
    {"kpi": "RUTs con consentimiento a Buk, #",                "label": "RUTs Consentimiento",  "color": "#3b82f6", "type": "#"},
    {"kpi": "Visualización de oferta Bci en Buk, %",           "label": "Visualización Oferta", "color": "#60a5fa", "type": "%"},
    {"kpi": "Ingresos en la oferta Bci en Buk, %",             "label": "Ingresos Oferta",      "color": "#93c5fd", "type": "%"},
    {"kpi": "Leads totales recibidos, #",                      "label": "Leads Totales",        "color": "#22c55e", "type": "#"},
    {"kpi": "Leads de calidad · API leads y seguimiento, #",   "label": "Leads Calidad",        "color": "#16a34a", "type": "#"},
    {"kpi": "Venta, #",                                        "label": "Venta",                "color": "#15803d", "type": "#"},
]

# Datos de ejemplo (se usan cuando el sheet está vacío)
MOCK_REAL = {
    "feb-26": [12000, 9800, 5400, 65, 55, 650, 280, 42],
    "mar-26": [13500, 11000, 6200, 68, 58, 780, 330, 55],
    "abr-26": [15000, 12500, 7100, 70, 60, 950, 410, 72],
}
MOCK_PPTO = [18000, 15000, 9000, 70, 60, 1200, 500, 100]

ANIM_CSS = """
<style>
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(18px); }
    to   { opacity: 1; transform: translateY(0); }
}
.fade-card {
    opacity: 0;
    animation: fadeSlideUp 0.45s ease forwards;
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
    if pd.isna(v) or str(v).strip() in ("", "-"):
        return None
    try:
        return float(str(v).strip().replace(",", "").replace("%", ""))
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner=False)
def _load_sheet() -> pd.DataFrame:
    try:
        return pd.read_csv(SHEET_URL, header=None)
    except Exception:
        return pd.DataFrame()


def _get_values(df: pd.DataFrame, month: str):
    """Devuelve (real[], ppto[]) para el mes dado. None si no hay datos."""
    if df.empty:
        return None, None
    m_idx    = MONTHS.index(month)
    real_col = 7  + m_idx
    ppto_col = 20 + m_idx
    reals, pptos = [], []
    for stage in STAGES:
        mask = df.iloc[:, 6].astype(str).str.strip() == stage["kpi"]
        rows = df[mask]
        if rows.empty:
            reals.append(None); pptos.append(None)
        else:
            row = rows.iloc[0]
            reals.append(_parse(row.iloc[real_col]))
            pptos.append(_parse(row.iloc[ppto_col]))
    return reals, pptos


def _to_abs(values):
    """Convierte etapas de % a valores absolutos usando el stage # anterior."""
    result, prev = [], None
    for stage, val in zip(STAGES, values):
        if val is None:
            result.append(None); continue
        if stage["type"] == "%":
            result.append(prev * val / 100 if prev else val)
        else:
            result.append(val)
            prev = val
    return result


# ── Layout ───────────────────────────────────────────────────────────
st.markdown(CARD_CSS + ANIM_CSS, unsafe_allow_html=True)

# Header
st.markdown(
    '<div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.5rem">'
    '<img src="https://raw.githubusercontent.com/manuelbunster-commits/relif-dashboard/main/bci_logo.png" width="80">'
    '<h1 style="margin:0;font-weight:700;font-size:1.8rem;color:#0f172a;letter-spacing:-0.02em">Funnel BCI × Buk</h1>'
    '</div>',
    unsafe_allow_html=True,
)

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
    sel_month  = st.selectbox("Mes", MONTHS, index=0)
    usar_mock  = st.toggle("📊 Datos de ejemplo", value=True)

# Cargar sheet
with st.spinner("Cargando datos..."):
    df_sheet = _load_sheet()

real_raw, ppto_raw = _get_values(df_sheet, sel_month)
has_real = real_raw and any(v not in (None, 0) for v in real_raw)

if usar_mock or not has_real:
    real_raw = MOCK_REAL.get(sel_month, MOCK_REAL["feb-26"])
    ppto_raw = MOCK_PPTO
    st.markdown(
        '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-left:4px solid #3b82f6;'
        'border-radius:10px;padding:0.7rem 1.2rem;margin-bottom:1rem;font-size:0.83rem;color:#1e40af">'
        '📊 Mostrando datos de ejemplo — cuando el sheet tenga datos reales, desactiva el toggle</div>',
        unsafe_allow_html=True,
    )

real_abs = _to_abs(real_raw)
ppto_abs = _to_abs(ppto_raw)

labels = [s["label"] for s in STAGES]
colors = [s["color"] for s in STAGES]

# ── Funnel + detalle ─────────────────────────────────────────────────
_section_header("Funnel de conversión — " + sel_month)

funnel_col, detail_col = st.columns([3, 2])

with funnel_col:
    max_val = max((v for v in real_abs if v), default=1)
    vals    = [v if v is not None else 0 for v in real_abs]

    # Textos finales (mostrados al terminar la animación)
    texts = []
    for i, (stage, val) in enumerate(zip(STAGES, real_abs)):
        if val is None:
            texts.append(""); continue
        label_val = f"{real_raw[i]}%" if stage["type"] == "%" else f"{val:,.0f}"
        pct_txt   = ""
        if i > 0 and real_abs[i - 1]:
            p = val / real_abs[i - 1] * 100
            pct_txt = f"  ↓{p:.0f}%"
        texts.append(f"<b>{label_val}</b>{pct_txt}")

    hovers = []
    for i, stage in enumerate(STAGES):
        label_val = f"{real_raw[i]}%" if stage["type"] == "%" else f"{vals[i]:,.0f}"
        ppto_txt  = f"<br>Presupuesto: {ppto_abs[i]:,.0f}" if ppto_abs and ppto_abs[i] else ""
        hovers.append(f"<b>{stage['label']}</b><br>Real: {label_val}{ppto_txt}<extra></extra>")

    # Estado inicial: barras en 0
    fig = go.Figure(data=[go.Bar(
        x=[0] * len(labels),
        y=labels,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[""] * len(labels),
        textposition="outside",
        textfont=dict(family="Inter", size=11.5, color="#374151"),
        hovertemplate=hovers,
        showlegend=False,
        width=0.7,
    )])

    # Frame final: barras en sus valores reales
    fig.frames = [go.Frame(
        data=[go.Bar(
            x=vals,
            y=labels,
            text=texts,
            marker=dict(color=colors, line=dict(width=0)),
        )],
        name="loaded",
    )]

    # Botón oculto para disparar la animación por JS
    fig.update_layout(
        updatemenus=[dict(
            type="buttons", visible=False, x=-2, y=-2,
            buttons=[dict(
                label="go", method="animate",
                args=[["loaded"], {
                    "frame": {"duration": 900, "redraw": True},
                    "transition": {"duration": 900, "easing": "cubic-in-out"},
                    "mode": "immediate",
                }],
            )],
        )],
    )

    # Líneas punteadas de presupuesto (aparecen sin animar)
    for i, ppto in enumerate(ppto_abs):
        if ppto:
            y_pos = len(STAGES) - 1 - i
            fig.add_shape(
                type="line",
                x0=ppto, x1=ppto,
                y0=y_pos - 0.4, y1=y_pos + 0.4,
                line=dict(color="#cbd5e1", width=2, dash="dot"),
            )

    fig.update_layout(
        height=440,
        margin=dict(t=10, b=10, l=150, r=180),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, range=[0, max_val * 1.55]),
        yaxis=dict(
            showgrid=False,
            tickfont=dict(family="Inter", size=12, color="#374151"),
            categoryorder="array",
            categoryarray=labels[::-1],
        ),
        font=dict(family="Inter"),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(
        '<div style="display:flex;gap:2rem;justify-content:center;margin-top:-0.5rem">'
        '<span style="font-size:0.74rem;color:#64748b">&#9632; Barra = Real &nbsp;|&nbsp; <b>N</b> = valor &nbsp;|&nbsp; ↓% = caída vs paso anterior</span>'
        '<span style="font-size:0.74rem;color:#94a3b8">-- = Presupuesto</span>'
        '</div>',
        unsafe_allow_html=True,
    )

with detail_col:
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    for i, (stage, real, ppto) in enumerate(zip(STAGES, real_abs, ppto_abs)):
        # Conversión vs etapa anterior
        conv_html = ""
        if i > 0 and real_abs[i-1] and real:
            pct = real / real_abs[i-1] * 100
            c   = "#22c55e" if pct >= 60 else "#f59e0b" if pct >= 30 else "#ef4444"
            conv_html = f'<span style="font-size:0.72rem;font-weight:700;color:{c}">↓ {pct:.0f}% del paso anterior</span>'

        # Cumplimiento vs presupuesto
        cumpl_html = ""
        if ppto and real:
            c2   = real / ppto * 100
            col2 = "#22c55e" if c2 >= 80 else "#f59e0b" if c2 >= 50 else "#ef4444"
            cumpl_html = f'<span style="font-size:0.7rem;color:{col2}">{c2:.0f}% del presupuesto</span>'

        # Valor a mostrar + atributos para el contador
        if stage["type"] == "%" and i < len(real_raw):
            val_str      = f"{real_raw[i]}%"
            counter_attr = ""  # porcentajes no se animan
        elif real is not None:
            val_str      = f"{real:,.0f}"
            counter_attr = f'data-counter="{real:.0f}"'
        else:
            val_str      = "—"
            counter_attr = ""

        delay = i * 0.08  # escalonado: 0s, 0.08s, 0.16s …

        st.markdown(f"""
        <div class="fade-card" style="display:flex;align-items:center;gap:0.8rem;
                    padding:0.6rem 0.9rem;background:white;border:1px solid #e2e8f0;
                    border-left:3px solid {stage['color']};border-radius:10px;
                    margin-bottom:0.35rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);
                    animation-delay:{delay:.2f}s">
            <div style="flex:1">
                <div style="font-size:0.67rem;color:#94a3b8;font-weight:700;
                            text-transform:uppercase;letter-spacing:0.05em;margin-bottom:1px">
                    {stage['label']}
                </div>
                <div style="font-size:1.15rem;font-weight:700;color:#0f172a"
                     {counter_attr}>{val_str}</div>
            </div>
            <div style="text-align:right;line-height:1.6">
                {conv_html}<br>{cumpl_html}
            </div>
        </div>""", unsafe_allow_html=True)

# ── Conversión entre pasos (barras) ──────────────────────────────────
_section_header("Tasa de conversión entre pasos")

conv_labels, conv_vals, conv_colors = [], [], []
for i in range(1, len(real_abs)):
    if real_abs[i] and real_abs[i-1] and real_abs[i-1] > 0:
        pct = real_abs[i] / real_abs[i-1] * 100
        conv_labels.append(f"{STAGES[i-1]['label']} → {STAGES[i]['label']}")
        conv_vals.append(round(pct, 1))
        conv_colors.append("#22c55e" if pct >= 60 else "#f59e0b" if pct >= 30 else "#ef4444")

if conv_labels:
    fig_conv = go.Figure(go.Bar(
        x=conv_labels,
        y=conv_vals,
        marker_color=conv_colors,
        marker_line_width=0,
        text=[f"{v}%" for v in conv_vals],
        textposition="outside",
        textfont=dict(family="Inter", size=12),
    ))
    fig_conv.add_hline(y=50, line_dash="dot", line_color="#94a3b8", line_width=1.5,
                       annotation_text="50%", annotation_font_size=11)
    fig_conv.update_layout(
        height=280, margin=dict(t=30, b=10, l=0, r=0),
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, max(conv_vals) * 1.25], gridcolor="#f1f5f9",
                   ticksuffix="%", zeroline=False),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_conv, use_container_width=True, config={"displayModeBar": False})

# ── Insights ─────────────────────────────────────────────────────────
_section_header("Conclusiones")

drops = []
for i in range(1, len(real_abs)):
    if real_abs[i] and real_abs[i-1] and real_abs[i-1] > 0:
        d = (1 - real_abs[i] / real_abs[i-1]) * 100
        drops.append((d, STAGES[i-1]["label"], STAGES[i]["label"]))

drops.sort(reverse=True)
overall_conv = real_abs[-1] / real_abs[0] * 100 if real_abs[0] and real_abs[-1] else 0

insights = []
if drops:
    insights.append(
        f"El mayor drop ocurre entre <b>{drops[0][1]}</b> → <b>{drops[0][2]}</b> "
        f"con un <b>{drops[0][0]:.0f}% de caída</b> — es el cuello de botella principal del funnel"
    )
if drops:
    best = sorted(drops)[0]
    insights.append(
        f"El paso más eficiente es <b>{best[1]}</b> → <b>{best[2]}</b> "
        f"con solo un <b>{best[0]:.0f}% de caída</b>"
    )
insights.append(
    f"La conversión total del funnel (Home → Venta) es de <b>{overall_conv:.3f}%</b> "
    f"— por cada 1.000 usuarios que entran, {overall_conv * 10:.1f} terminan en venta"
)

if ppto_abs and real_abs and ppto_abs[-1] and real_abs[-1]:
    cumpl_venta = real_abs[-1] / ppto_abs[-1] * 100
    cumpl_col   = "verde" if cumpl_venta >= 80 else "amarillo" if cumpl_venta >= 50 else "rojo"
    insights.append(
        f"Las ventas están al <b>{cumpl_venta:.0f}%</b> del presupuesto mensual "
        f"— semáforo <b>{cumpl_col}</b>"
    )

items_html = "".join(f"<li style='margin-bottom:0.5rem'>{i}</li>" for i in insights)
st.markdown(f"""
<div class="fade-card" style="background:white;border:1px solid #e2e8f0;
            border-left:4px solid #8b5cf6;border-radius:14px;padding:1rem 1.4rem;
            box-shadow:0 1px 4px rgba(0,0,0,0.05);animation-delay:0.3s">
    <p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;
              color:#94a3b8;margin:0 0 0.6rem">💡 Conclusiones</p>
    <ul style="margin:0;padding-left:1.2rem;color:#374151;font-size:0.88rem;line-height:1.9">
        {items_html}
    </ul>
</div>""", unsafe_allow_html=True)

# ── Animaciones JS (contador + barras Plotly) ─────────────────────────
components.html("""
<script>
(function () {
    function run() {
        var doc = window.parent.document;

        // 1. Contador animado en las cards
        doc.querySelectorAll('[data-counter]').forEach(function (el) {
            if (el.dataset.animated) return;
            el.dataset.animated = '1';
            var target = parseFloat(el.getAttribute('data-counter'));
            var start  = null;
            function step(ts) {
                if (!start) start = ts;
                var t    = Math.min((ts - start) / 1000, 1);
                var ease = 1 - Math.pow(1 - t, 3);
                el.textContent = Math.round(target * ease).toLocaleString('es-CL');
                if (t < 1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        });

        // 2. Animar barras del funnel (primer gráfico Plotly)
        var Plotly = window.parent.Plotly;
        var plots  = doc.querySelectorAll('.js-plotly-plot');
        if (Plotly && plots.length > 0) {
            Plotly.animate(plots[0], ['loaded'], {
                transition: { duration: 900, easing: 'cubic-in-out' },
                frame:      { duration: 900, redraw: true },
                mode:       'immediate',
            });
        }
    }
    setTimeout(run, 400);
})();
</script>
""", height=0)
