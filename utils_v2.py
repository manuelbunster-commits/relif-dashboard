"""Funciones compartidas entre páginas del dashboard — versión v2 (diseño mejorado)."""

import os
from datetime import date, timedelta, datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()

RELIF_EXECUTE_URL = (
    "https://relif-saas-back-workload-816446680429.southamerica-west1.run.app"
    "/admin/db/execute"
)

STATUS_COLORS = {
    "rejected_by_bank": "#ef4444",
    "sent_to_bank":     "#22c55e",
    "created":          "#3b82f6",
}

STATUS_LABELS = {
    "rejected_by_bank": "Rechazada",
    "sent_to_bank":     "Enviada",
    "created":          "Creada",
}

SCROLL_ANIM = """
<style>
.scroll-animate {
    opacity: 0;
    transform: translateY(28px);
    transition: opacity 0.55s ease-out, transform 0.55s ease-out;
}
.scroll-animate.in-view {
    opacity: 1;
    transform: translateY(0);
}
</style>
<script>
(function() {
    const SEL = [
        '[data-testid="stPlotlyChart"]',
        '[data-testid="stDataFrame"]',
        '[data-testid="stDataFrameResizable"]',
    ].join(',');

    const io = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.classList.add('in-view');
                io.unobserve(e.target);
            }
        });
    }, { threshold: 0.05, rootMargin: '0px 0px -30px 0px' });

    function attach(el) {
        if (el.dataset.scrollBound) return;
        el.dataset.scrollBound = '1';
        el.classList.add('scroll-animate');
        io.observe(el);
    }

    // Observe elements added dynamically by Streamlit
    const mo = new MutationObserver(() => {
        document.querySelectorAll(SEL).forEach(attach);
    });

    setTimeout(() => {
        document.querySelectorAll(SEL).forEach(attach);
        mo.observe(document.body, { childList: true, subtree: true });
    }, 300);
})();
</script>
"""

CARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.block-container {
    padding-top: 1.8rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    animation: pageLoad 0.5s ease-out;
}
@keyframes pageLoad {
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Métricas nativas ── */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.04);
}
[data-testid="metric-container"] label {
    font-size: 0.7rem !important;
    color: #94a3b8 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border: none !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #3b82f6, #2563eb) !important;
    transform: translateY(-1px) !important;
}

hr { border: none !important; border-top: 1px solid #e2e8f0 !important; margin: 1.5rem 0 !important; }

/* ── KPI Cards ── */
.kpi-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-left: 4px solid #3b82f6;
    border-radius: 14px;
    padding: 1.1rem 1.3rem 0.6rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.kpi-card.green  { border-left-color: #22c55e; }
.kpi-card.red    { border-left-color: #ef4444; }
.kpi-card.blue   { border-left-color: #3b82f6; }
.kpi-card.purple { border-left-color: #8b5cf6; }
.kpi-label { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; color: #94a3b8; margin-bottom: 0.2rem; }
.kpi-value {
    font-size: 2rem; font-weight: 700; color: #0f172a; line-height: 1.1;
    animation: countUp 0.6s ease-out;
}
@keyframes countUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeSlideUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.kpi-delta { font-size: 0.75rem; font-weight: 500; margin-top: 0.2rem; }
.kpi-delta.up      { color: #22c55e; }
.kpi-delta.down    { color: #ef4444; }
.kpi-delta.neutral { color: #94a3b8; }

/* ── Alert banner ── */
.alert-banner {
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-left: 4px solid #ef4444;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 1rem;
    font-size: 0.85rem;
    color: #991b1b;
    font-weight: 500;
}
.alert-banner.warning {
    background: #fffbeb;
    border-color: #fde68a;
    border-left-color: #f59e0b;
    color: #92400e;
}

.last-updated { font-size: 0.72rem; color: #94a3b8; text-align: right; margin-bottom: 1rem; }

h1 {
    font-weight: 700 !important;
    font-size: 1.8rem !important;
    color: #0f172a !important;
    letter-spacing: -0.02em !important;
}
</style>
"""


@st.cache_data(ttl=3600, show_spinner=False)
def get_token() -> str:
    token = os.environ.get("RELIF_JWT_TOKEN", "")
    if token:
        return token
    st.error("Configura RELIF_JWT_TOKEN en el archivo .env")
    st.stop()


@st.cache_data(ttl=300, show_spinner=False)
def fetch_data(start: str, end: str) -> pd.DataFrame:
    token = get_token()
    query = f"""
        SELECT *
        FROM "BankOfferRequests"
        WHERE "createdAt" >= '{start}'
          AND "createdAt" <  '{end}'
    """
    resp = requests.post(
        RELIF_EXECUTE_URL,
        headers={"Authorization": f"Bearer {token}"},
        json={"userQuery": query.strip()},
        timeout=60,
    )
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        return pd.DataFrame()

    rows = []
    for r in results:
        rows.append({
            "id":        r.get("id"),
            "bukLeadId": r.get("bukLeadId"),
            "bank":      r.get("bank"),
            "status":    r.get("status"),
            "rut":       r.get("rut"),
            "createdAt": r.get("createdAt"),
            "updatedAt": r.get("updatedAt"),
        })

    df = pd.DataFrame(rows)
    df["createdAt"] = pd.to_datetime(df["createdAt"], utc=True).dt.tz_convert("America/Santiago")
    df["updatedAt"] = pd.to_datetime(df["updatedAt"], utc=True).dt.tz_convert("America/Santiago")
    df["date"]    = df["createdAt"].dt.date
    df["hour"]    = df["createdAt"].dt.hour
    df["weekday"] = df["createdAt"].dt.day_name()
    return df


def _trend_arrow(pct: float) -> str:
    if pct > 0:
        return f'<span class="kpi-delta up">↑ {pct:.0f}% vs período anterior</span>'
    elif pct < 0:
        return f'<span class="kpi-delta down">↓ {abs(pct):.0f}% vs período anterior</span>'
    return '<span class="kpi-delta neutral">— igual que período anterior</span>'


def _pct_change(curr, prev):
    if prev == 0:
        return 0
    return round((curr - prev) / prev * 100)


def _section_header(title: str):
    """Separador estilizado con línea horizontal y título a la izquierda."""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.8rem;margin:1.8rem 0 1rem">
        <span style="font-size:0.65rem;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.1em;color:#94a3b8;white-space:nowrap">{title}</span>
        <div style="flex:1;height:1px;background:#e2e8f0"></div>
    </div>""", unsafe_allow_html=True)


def _style_status(df: pd.DataFrame):
    """Colorea filas de la tabla según el status."""
    bg_map = {
        "rejected_by_bank": "#fef2f2",
        "sent_to_bank":     "#f0fdf4",
        "created":          "#eff6ff",
    }
    def row_bg(row):
        bg = bg_map.get(row.get("status", ""), "")
        return [f"background-color:{bg}" if bg else "" for _ in row]
    return df.style.apply(row_bg, axis=1)


def render_dashboard(bank_filter: str = None):
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    st.markdown(SCROLL_ANIM, unsafe_allow_html=True)

    # ── Sidebar ──
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
        comparar          = st.toggle("⚖️ Modo comparación", value=False)
        alerta_threshold  = st.slider("🚨 Alerta rechazo >", 0, 100, 60, step=5, format="%d%%")

    # ── Header ──
    if bank_filter == "BCI":
        col_logo, col_title = st.columns([0.3, 5])
        with col_logo:
            st.image("https://raw.githubusercontent.com/manuelbunster-commits/relif-dashboard/main/bci_logo.png", width=80)
        with col_title:
            st.title(bank_filter)
    elif bank_filter:
        st.title(f"🏦 {bank_filter}")
    else:
        st.title("🏦 Consolidado")

    subtitle_ph = st.empty()  # subtítulo con período + conteo

    # ── Filtros de fecha ──
    dc1, dc2 = st.columns(2)
    with dc1:
        start_date = st.date_input("Desde", value=date.today() - timedelta(days=10))
    with dc2:
        end_date = st.date_input("Hasta", value=date.today() + timedelta(days=1))

    delta_days = max((end_date - start_date).days, 1)
    # Si el rango es ≤ 7 días, comparar contra la misma ventana de la semana anterior
    # Si es > 7 días, comparar contra el período inmediatamente anterior de igual duración
    if delta_days <= 7:
        prev_start = str(start_date - timedelta(weeks=1))
        prev_end   = str(end_date   - timedelta(weeks=1))
    else:
        prev_start = str(start_date - timedelta(days=delta_days))
        prev_end   = str(start_date)

    with st.spinner("Cargando datos..."):
        df_raw  = fetch_data(str(start_date), str(end_date))
        df_prev = fetch_data(prev_start, prev_end)

    now_cl = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.markdown(f'<p class="last-updated">Actualizado: {now_cl}</p>', unsafe_allow_html=True)

    if df_raw.empty:
        st.warning("No hay datos para el período seleccionado.")
        return

    if bank_filter:
        df_raw  = df_raw[df_raw["bank"] == bank_filter]
        df_prev = df_prev[df_prev["bank"] == bank_filter] if not df_prev.empty else df_prev
        if df_raw.empty:
            st.warning(f"No hay datos para {bank_filter} en el período seleccionado.")
            return

    # ── Métricas ──
    total_curr = len(df_raw)
    total_prev = len(df_prev) if not df_prev.empty else 0
    env_curr   = int((df_raw["status"] == "sent_to_bank").sum())
    env_prev   = int((df_prev["status"] == "sent_to_bank").sum()) if not df_prev.empty else 0
    rec_curr   = int((df_raw["status"] == "rejected_by_bank").sum())
    rec_prev   = int((df_prev["status"] == "rejected_by_bank").sum()) if not df_prev.empty else 0
    tasa       = round(env_curr / total_curr * 100) if total_curr else 0
    tasa_prev  = round(env_prev / total_prev * 100) if total_prev else 0

    pct_total = _pct_change(total_curr, total_prev)
    pct_env   = _pct_change(env_curr, env_prev)
    pct_rec   = _pct_change(rec_curr, rec_prev)

    by_day_spark = df_raw.groupby("date").size().reset_index(name="n").set_index("date")["n"]

    # ── Rellenar placeholders ──
    subtitle_ph.markdown(
        f'<p style="color:#64748b;font-size:0.9rem;margin:-0.5rem 0 1.2rem;'
        f'padding-bottom:0.6rem;border-bottom:1px solid #f1f5f9">'
        f'📅 {start_date} → {end_date} &nbsp;·&nbsp; '
        f'<b style="color:#0f172a">{total_curr}</b> registros</p>',
        unsafe_allow_html=True,
    )


    # ── Alertas ──
    pct_rec_actual = round(rec_curr / total_curr * 100) if total_curr else 0
    if pct_rec_actual >= alerta_threshold:
        st.markdown(
            f'<div class="alert-banner">🚨 Tasa de rechazo en <b>{pct_rec_actual}%</b> — supera el umbral configurado de {alerta_threshold}%</div>',
            unsafe_allow_html=True,
        )
    elif pct_rec_actual >= alerta_threshold - 10:
        st.markdown(
            f'<div class="alert-banner warning">⚠️ Tasa de rechazo en <b>{pct_rec_actual}%</b> — acercándose al umbral de {alerta_threshold}%</div>',
            unsafe_allow_html=True,
        )

    # ── KPI Cards ──
    k1, k2, k3, k4 = st.columns(4)
    env_spark = df_raw[df_raw["status"] == "sent_to_bank"].groupby("date").size().reindex(by_day_spark.index, fill_value=0)
    rec_spark = df_raw[df_raw["status"] == "rejected_by_bank"].groupby("date").size().reindex(by_day_spark.index, fill_value=0)

    with k1:
        st.markdown(f"""
        <div class="kpi-card blue" style="animation:fadeSlideUp 0.45s ease forwards;animation-delay:0s;opacity:0">
            <div class="kpi-label">Total Requests</div>
            <div class="kpi-value" data-counter="{total_curr}">{total_curr}</div>
            {_trend_arrow(pct_total)}
        </div>""", unsafe_allow_html=True)
    with k2:
        color = "green" if tasa >= 50 else "red"
        st.markdown(f"""
        <div class="kpi-card {color}" style="animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.1s;opacity:0">
            <div class="kpi-label">Tasa de Aprobación</div>
            <div class="kpi-value" data-counter="{tasa}" data-suffix="%">{tasa}%</div>
            {_trend_arrow(_pct_change(tasa, tasa_prev))}
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class="kpi-card green" style="animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.2s;opacity:0">
            <div class="kpi-label">Enviadas al banco</div>
            <div class="kpi-value" data-counter="{env_curr}">{env_curr}</div>
            {_trend_arrow(pct_env)}
        </div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
        <div class="kpi-card red" style="animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.3s;opacity:0">
            <div class="kpi-label">Rechazadas</div>
            <div class="kpi-value" data-counter="{rec_curr}">{rec_curr}</div>
            {_trend_arrow(-pct_rec)}
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Modo comparación ──
    if comparar and not df_prev.empty:
        _section_header("Comparación de períodos")
        c1, c2 = st.columns(2)
        with c1:
            st.caption(f"📅 {start_date} → {end_date}")
            st.metric("Total", total_curr)
            st.metric("Enviadas", env_curr)
            st.metric("Rechazadas", rec_curr)
        with c2:
            st.caption(f"📅 {prev_start} → {prev_end}")
            st.metric("Total", total_prev)
            st.metric("Enviadas", env_prev)
            st.metric("Rechazadas", rec_prev)

    # ── Gauge ──
    _, gauge_col, _ = st.columns([1, 2, 1])
    with gauge_col:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=tasa,
            domain={"x": [0, 1], "y": [0, 1]},
            delta={"reference": tasa_prev, "suffix": "%", "valueformat": ".0f"},
            number={"suffix": "%", "font": {"size": 40, "family": "Inter"}, "valueformat": ".0f"},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8"},
                "bar": {"color": "#22c55e" if tasa >= 50 else "#ef4444", "thickness": 0.25},
                "bgcolor": "white",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40],  "color": "#fef2f2"},
                    {"range": [40, 60], "color": "#fffbeb"},
                    {"range": [60, 100], "color": "#f0fdf4"},
                ],
                "threshold": {"line": {"color": "#0f172a", "width": 2}, "thickness": 0.75, "value": 50},
            },
            title={"text": "Tasa de Aprobación", "font": {"size": 14, "family": "Inter", "color": "#94a3b8"}},
        ))
        fig_gauge.update_layout(
            height=280, margin=dict(t=40, b=20, l=60, r=60),
            paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter"),
        )
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    # ── 2. Actividad reciente ──
    _section_header("Actividad reciente")
    ultimos = df_raw.sort_values("createdAt", ascending=False).head(5)
    for _, row in ultimos.iterrows():
        status = row["status"]
        color  = STATUS_COLORS.get(status, "#94a3b8")
        label  = STATUS_LABELS.get(status, status)
        hora   = row["createdAt"].strftime("%d/%m %H:%M")
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:1rem;padding:0.6rem 1rem;
                    background:white;border:1px solid #e2e8f0;border-radius:10px;
                    margin-bottom:0.4rem;box-shadow:0 1px 3px rgba(0,0,0,0.04)">
            <span style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0;display:inline-block"></span>
            <span style="font-size:0.82rem;color:#0f172a;font-weight:600;flex:1">{row['rut']}</span>
            <span style="font-size:0.78rem;color:#64748b">{row['bank']}</span>
            <span style="font-size:0.75rem;font-weight:600;color:{color};background:{color}18;padding:2px 10px;border-radius:999px">{label}</span>
            <span style="font-size:0.75rem;color:#94a3b8;min-width:80px;text-align:right">{hora}</span>
        </div>
        """, unsafe_allow_html=True)

    # ── 3. Análisis temporal ──
    _section_header("Análisis temporal")
    gb1, gb2 = st.columns(2)
    with gb1:
        banks2 = ["Todos"] + sorted(df_raw["bank"].dropna().unique().tolist())
        sel_b2 = st.selectbox("Banco ", banks2, key=f"gb_{bank_filter}")
    with gb2:
        stats2 = ["Todos"] + sorted(df_raw["status"].dropna().unique().tolist())
        sel_s2 = st.selectbox("Status ", stats2, key=f"gs_{bank_filter}")

    df_g = df_raw.copy()
    if sel_b2 != "Todos": df_g = df_g[df_g["bank"]   == sel_b2]
    if sel_s2 != "Todos": df_g = df_g[df_g["status"] == sel_s2]

    st.caption("Requests por día + tendencia")
    by_day = df_g.groupby("date").size().reset_index(name="Count")
    by_day["Tendencia"] = by_day["Count"].rolling(window=3, min_periods=1).mean()

    fig_combo = go.Figure()
    fig_combo.add_trace(go.Bar(x=by_day["date"], y=by_day["Count"], name="Por día", marker_color="#3b82f6", marker_line_width=0))
    fig_combo.add_trace(go.Scatter(x=by_day["date"], y=by_day["Tendencia"], name="Tendencia (3d)", line=dict(color="#8b5cf6", width=2.5, dash="dot")))
    fig_combo.update_layout(
        margin=dict(t=10, b=10), height=280, xaxis_title="", yaxis_title="",
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#f1f5f9", zeroline=False),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, font=dict(size=11)),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_combo, use_container_width=True)

    st.caption("Por banco y status (%)")
    by_bs = df_raw.groupby(["bank", "status"]).size().reset_index(name="count")
    totals = by_bs.groupby("bank")["count"].transform("sum")
    by_bs["pct"] = by_bs["count"] / totals
    by_bs["status_label"] = by_bs["status"].map(STATUS_LABELS).fillna(by_bs["status"])
    fig_bar = px.bar(
        by_bs, x="pct", y="bank", color="status_label", orientation="h",
        color_discrete_map={v: STATUS_COLORS[k] for k, v in STATUS_LABELS.items()}, barmode="stack",
    )
    fig_bar.update_traces(marker_line_width=0)
    fig_bar.update_layout(
        margin=dict(t=10, b=10), height=260, xaxis_tickformat=".0%", xaxis_title="", yaxis_title="",
        plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#f1f5f9", zeroline=False), yaxis=dict(showgrid=False),
        legend_title="", font=dict(family="Inter"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── 4. Resumen ──
    _section_header("Resumen")
    t1, t2, pie_col = st.columns(3)
    with t1:
        st.caption("Por banco")
        st.dataframe(
            df_raw.groupby("bank").size().reset_index(name="Count").sort_values("Count", ascending=False),
            hide_index=True, use_container_width=True, height=160,
        )
    with t2:
        st.caption("Por status")
        st.dataframe(
            df_raw.groupby("status").size().reset_index(name="Count").sort_values("Count", ascending=False),
            hide_index=True, use_container_width=True, height=160,
        )
    with pie_col:
        st.caption("Distribución por status")
        sc = df_raw["status"].value_counts().reset_index()
        sc.columns = ["status", "count"]
        sc["label"] = sc["status"].map(STATUS_LABELS).fillna(sc["status"])
        fig_pie = px.pie(
            sc, names="label", values="count", color="label",
            color_discrete_map={v: STATUS_COLORS[k] for k, v in STATUS_LABELS.items()},
            hole=0.55,
        )
        fig_pie.update_traces(
            textposition="outside",
            textinfo="percent+label",
            textfont=dict(size=11, family="Inter"),
            marker=dict(line=dict(color="white", width=2)),
        )
        fig_pie.update_layout(
            margin=dict(t=10, b=10, l=10, r=10), height=160,
            showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter"),
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    # ── 5. Heatmap ──
    _section_header("Heatmap — requests por hora y día")
    WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    WEEKDAY_ES    = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    heat = df_raw.groupby(["weekday", "hour"]).size().reset_index(name="count")
    heat_pivot = heat.pivot(index="weekday", columns="hour", values="count").reindex(WEEKDAY_ORDER).fillna(0)
    heat_pivot.index = WEEKDAY_ES
    heat_pivot = heat_pivot.loc[:, (heat_pivot > 0).any(axis=0)]

    peak_dia_idx = heat_pivot.sum(axis=1).idxmax()
    peak_hora    = heat_pivot.sum(axis=0).idxmax()

    fig_heat = px.imshow(
        heat_pivot,
        labels=dict(x="Hora del día", y="", color="Requests"),
        color_continuous_scale=[[0, "#f0f9ff"], [0.5, "#3b82f6"], [1, "#1d4ed8"]],
        aspect="auto", text_auto=True,
    )
    fig_heat.update_traces(textfont=dict(size=11, family="Inter"))
    fig_heat.update_layout(
        height=280, margin=dict(t=10, b=10, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
        xaxis=dict(tickmode="linear", tick0=heat_pivot.columns[0], dtick=1),
        font=dict(family="Inter"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    # Conclusiones
    hora_by     = heat.groupby("hour")["count"].sum()
    dia_by      = heat.groupby("weekday")["count"].sum()
    dia_peak_es = WEEKDAY_ES[WEEKDAY_ORDER.index(dia_by.idxmax())]
    dia_bajo_es = WEEKDAY_ES[WEEKDAY_ORDER.index(dia_by.idxmin())]
    horario_tot = heat["count"].sum()
    pct_of      = round(heat[heat["hour"].between(9, 18)]["count"].sum() / horario_tot * 100) if horario_tot else 0
    pct_manana  = round(heat[heat["hour"].between(9, 13)]["count"].sum() / horario_tot * 100) if horario_tot else 0
    pct_tarde   = round(heat[heat["hour"].between(14, 18)]["count"].sum() / horario_tot * 100) if horario_tot else 0
    bloque_peak = "mañana (9–13h)" if pct_manana >= pct_tarde else "tarde (14–18h)"
    top2_horas  = hora_by.nlargest(2).index.tolist()
    top3_pct    = round(hora_by.nlargest(3).sum() / horario_tot * 100) if horario_tot else 0
    pct_fds     = round(heat[heat["weekday"].isin(["Saturday", "Sunday"])]["count"].sum() / horario_tot * 100) if horario_tot else 0

    insights = [
        f"El día más activo es <b>{dia_peak_es}</b> y el menos activo es <b>{dia_bajo_es}</b>",
        f"Las horas peak son las <b>{top2_horas[0]}:00 y {top2_horas[1]}:00 hrs</b> — concentran el <b>{top3_pct}%</b> del tráfico",
        f"El <b>{pct_of}%</b> llega en horario de oficina, con mayor carga en la <b>{bloque_peak}</b>",
        f"El fin de semana representa solo el <b>{pct_fds}%</b> del total — operación esencialmente laboral",
    ]
    items_html = "".join(f"<li>{i}</li>" for i in insights)
    st.markdown(f"""
    <div style="background:white;border:1px solid #e2e8f0;border-left:4px solid #8b5cf6;
                border-radius:14px;padding:1rem 1.4rem;margin-top:0.5rem;
                box-shadow:0 1px 4px rgba(0,0,0,0.05)">
        <p style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;
                  color:#94a3b8;margin:0 0 0.6rem">💡 Conclusiones</p>
        <ul style="margin:0;padding-left:1.2rem;color:#374151;font-size:0.88rem;line-height:1.9">{items_html}</ul>
    </div>""", unsafe_allow_html=True)

    # ── Contador animado en KPI cards ──
    components.html("""
<script>
(function () {
    function run() {
        window.parent.document.querySelectorAll('[data-counter]').forEach(function (el) {
            if (el.dataset.animated) return;
            el.dataset.animated = '1';
            var target = parseFloat(el.getAttribute('data-counter'));
            var suffix = el.getAttribute('data-suffix') || '';
            var start  = null;
            function step(ts) {
                if (!start) start = ts;
                var t    = Math.min((ts - start) / 900, 1);
                var ease = 1 - Math.pow(1 - t, 3);
                el.textContent = Math.round(target * ease).toLocaleString('es-CL') + suffix;
                if (t < 1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        });
    }
    setTimeout(run, 400);
})();
</script>
""", height=0)

    # ── 6. Detalle de registros ──
    _section_header("Detalle de registros")
    f1, f2, f3 = st.columns(3)
    with f1:
        banks = ["Todos"] + sorted(df_raw["bank"].dropna().unique().tolist())
        sel_bank = st.selectbox("Banco", banks, key=f"fb_{bank_filter}")
    with f2:
        stats = ["Todos"] + sorted(df_raw["status"].dropna().unique().tolist())
        sel_status = st.selectbox("Status", stats, key=f"fs_{bank_filter}")
    with f3:
        ruts = ["Todos"] + sorted(df_raw["rut"].dropna().unique().tolist())
        sel_rut = st.selectbox("RUT", ruts, key=f"fr_{bank_filter}")

    df_f = df_raw.copy()
    if sel_bank   != "Todos": df_f = df_f[df_f["bank"]   == sel_bank]
    if sel_status != "Todos": df_f = df_f[df_f["status"] == sel_status]
    if sel_rut    != "Todos": df_f = df_f[df_f["rut"]    == sel_rut]

    df_display = df_f[["id", "bukLeadId", "bank", "status", "rut", "createdAt", "updatedAt"]].sort_values("createdAt", ascending=False)
    st.dataframe(
        _style_status(df_display),
        hide_index=True, use_container_width=True, height=300,
    )
