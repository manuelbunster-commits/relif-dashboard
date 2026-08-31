"""Track 2 BCI — flujo nuevo, créditos by Buk (verificación de employment)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
from datetime import date, timedelta
from utils import fetch_track2_data, CARD_CSS

st.set_page_config(page_title="Track 2 BCI", page_icon="🏗️", layout="wide")
st.markdown(CARD_CSS, unsafe_allow_html=True)

with st.sidebar:
    if st.button("🔄 Actualizar", use_container_width=True, key="t2_refresh"):
        st.cache_data.clear()
        st.rerun()

PRECIO_CONSULTA = 30   # CLP por cada consulta, exitosa o no
BONO_EXITO      = 350  # CLP adicionales por cada respuesta exitosa (success = True)


def _clp(n: float) -> str:
    return f"${n:,.0f}".replace(",", ".")


def _section_header(title: str, icon: str = ""):
    icon_html = f'<span style="font-size:0.9rem;line-height:1">{icon}</span>' if icon else ""
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.7rem;margin:2rem 0 1rem">
        {icon_html}
        <span style="font-size:0.72rem;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.1em;color:#64748b;white-space:nowrap">{title}</span>
        <div style="flex:1;height:1px;background:linear-gradient(90deg,#e2e8f0,transparent)"></div>
    </div>""", unsafe_allow_html=True)


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#1d4ed8 100%);
            border-radius:16px;padding:2rem 2.5rem;margin-bottom:1.8rem;
            position:relative;overflow:hidden">
    <div style="position:absolute;top:-30px;right:-30px;width:200px;height:200px;
                background:rgba(255,255,255,0.04);border-radius:50%"></div>
    <div style="position:relative;z-index:1">
        <div style="font-size:1.6rem;line-height:1.4;font-weight:800;color:white;letter-spacing:-0.02em">
            Track 2 BCI — Créditos by Buk
        </div>
        <div style="font-size:0.85rem;line-height:1.4;color:#94a3b8;margin-top:0.3rem">
            Verificación de employment (ApiRequests)
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Fecha ────────────────────────────────────────────────────────────────────
today = date.today()
_presets = [
    ("Hoy",       today,                       today + timedelta(days=1)),
    ("7 días",    today - timedelta(days=7),   today + timedelta(days=1)),
    ("15 días",   today - timedelta(days=15),  today + timedelta(days=1)),
    ("Desde lanzamiento", date(2026, 8, 19),   today + timedelta(days=1)),
]
st.markdown("""<style>
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="secondary"] {
    font-size:0.72rem;font-weight:600;padding:0.25rem 0.6rem;border-radius:999px;
    background:#f1f5f9;border:1px solid #e2e8f0;color:#475569;transition:all 0.15s;
}
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button[kind="secondary"]:hover {
    background:#e2e8f0;color:#0f172a;border-color:#cbd5e1;
}
</style>""", unsafe_allow_html=True)

pb = st.columns(len(_presets))
for i, (lbl, ps, pe) in enumerate(_presets):
    with pb[i]:
        if st.button(lbl, key=f"preset_t2_{lbl}", use_container_width=True):
            st.session_state["t2_start"] = ps
            st.session_state["t2_end"]   = pe
            st.rerun()

dc1, dc2 = st.columns(2)
with dc1:
    start = st.date_input("Desde", value=st.session_state.get("t2_start", date(2026, 8, 19)), key="t2_start")
with dc2:
    end   = st.date_input("Hasta", value=st.session_state.get("t2_end",   today + timedelta(days=1)),  key="t2_end")

# ── Datos ────────────────────────────────────────────────────────────────────
with st.spinner("Cargando..."):
    df = fetch_track2_data(str(start), str(end))

if df.empty:
    st.info("Sin datos para este período.")
    st.stop()

# ── Métricas base ────────────────────────────────────────────────────────────
total     = len(df)
n_success = int(df["success"].sum())
pct_ok    = round(n_success / total * 100) if total else 0
n_404     = int((df["statusCode"] == 404).sum())
n_500     = int((df["statusCode"] == 500).sum())
pct_404   = round(n_404 / total * 100) if total else 0
pct_500   = round(n_500 / total * 100) if total else 0

n_fail            = total - n_success
ingreso_consultas = n_fail * PRECIO_CONSULTA
ingreso_exitos    = n_success * BONO_EXITO
ingreso_total     = ingreso_consultas + ingreso_exitos

# ── KPI cards — operación ────────────────────────────────────────────────────
_section_header("Operación", "📡")
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""
    <div class="kpi-card blue" style="min-height:126px;animation:fadeSlideUp 0.45s ease forwards;animation-delay:0s;opacity:0">
        <span class="kpi-icon">📋</span>
        <div class="kpi-label">Total consultas (N)</div>
        <div class="kpi-value" data-counter="{total}">{total}</div>
        <span class="kpi-delta neutral">{start} → {end}</span>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""
    <div class="kpi-card green" style="min-height:126px;animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.1s;opacity:0">
        <span class="kpi-icon">🏆</span>
        <div class="kpi-label">Winrate</div>
        <div class="kpi-value" data-counter="{pct_ok}" data-suffix="%">{pct_ok}%</div>
        <span class="kpi-delta neutral">{n_success:,} / {total:,} exitosas</span>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""
    <div class="kpi-card amber" style="min-height:126px;animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.2s;opacity:0">
        <span class="kpi-icon">🔍</span>
        <div class="kpi-label">Empleado no encontrado</div>
        <div class="kpi-value" data-counter="{n_404}">{n_404}</div>
        <span class="kpi-delta neutral">{pct_404}% del total</span>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""
    <div class="kpi-card red" style="min-height:126px;animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.3s;opacity:0">
        <span class="kpi-icon">⚠️</span>
        <div class="kpi-label">Errores (500)</div>
        <div class="kpi-value" data-counter="{n_500}">{n_500}</div>
        <span class="kpi-delta neutral">{pct_500}% del total</span>
    </div>""", unsafe_allow_html=True)

# ── KPI cards — monetario ────────────────────────────────────────────────────
_section_header("Conteo monetario", "💰")
m1, m2, m3 = st.columns([1, 1, 1.2])
with m1:
    st.markdown(f"""
    <div class="kpi-card purple" style="min-height:126px;animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.4s;opacity:0">
        <span class="kpi-icon">💵</span>
        <div class="kpi-label">Ingreso por consultas fallidas</div>
        <div class="kpi-value">${'{:,}'.format(ingreso_consultas).replace(',', '.')}</div>
        <span class="kpi-delta neutral">{n_fail:,} × $30</span>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="kpi-card green" style="min-height:126px;animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.5s;opacity:0">
        <span class="kpi-icon">🎯</span>
        <div class="kpi-label">Ingreso por éxitos</div>
        <div class="kpi-value">${'{:,}'.format(ingreso_exitos).replace(',', '.')}</div>
        <span class="kpi-delta neutral">{n_success:,} × $350</span>
    </div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0f172a 0%,#1e3a5f 60%,#1d4ed8 100%);
                border-radius:16px;padding:1.3rem 1.4rem 1rem;position:relative;overflow:hidden;
                box-shadow:0 4px 20px rgba(29,78,216,0.25);min-height:126px;
                animation:fadeSlideUp 0.45s ease forwards;animation-delay:0.6s;opacity:0">
        <div style="position:absolute;top:-30px;right:-30px;width:140px;height:140px;
                    background:rgba(255,255,255,0.06);border-radius:50%"></div>
        <span class="kpi-icon">💰</span>
        <div class="kpi-label" style="color:#cbd5e1">Ingreso total estimado</div>
        <div class="kpi-value" style="color:white">${'{:,}'.format(ingreso_total).replace(',', '.')}</div>
        <span class="kpi-delta" style="color:#93c5fd">consultas + bono de éxito</span>
    </div>""", unsafe_allow_html=True)

# ── Contador animado ─────────────────────────────────────────────────────────
components.html("""
<script>
(function () {
    var _runId = Date.now();
    function run() {
        window.parent.document.querySelectorAll('[data-counter]').forEach(function (el) {
            if (el.dataset.runId === String(_runId)) return;
            el.dataset.runId = String(_runId);
            var target = parseFloat(el.getAttribute('data-counter'));
            var suffix = el.getAttribute('data-suffix') || '';
            var start  = null;
            var duration = 800;
            function step(ts) {
                if (!start) start = ts;
                var t    = Math.min((ts - start) / duration, 1);
                var ease = 1 - Math.pow(1 - t, 3);
                el.textContent = Math.round(target * ease).toLocaleString('es-CL') + suffix;
                if (t < 1) requestAnimationFrame(step);
                else el.textContent = target.toLocaleString('es-CL') + suffix;
            }
            requestAnimationFrame(step);
        });
    }
    setTimeout(run, 300);
})();
</script>
""", height=0)

# ── Gráfico 1: evolución diaria success vs fail ─────────────────────────────
_section_header("Evolución diaria", "📈")

daily = (
    df.groupby(["date", "success"])
    .size()
    .reset_index(name="n")
)

fig = go.Figure()
fig.add_trace(go.Bar(
    name="Éxito",
    x=daily[daily["success"] == True]["date"],
    y=daily[daily["success"] == True]["n"],
    marker_color="#22c55e",
    marker_line_width=0,
))
fig.add_trace(go.Bar(
    name="Fallida",
    x=daily[daily["success"] == False]["date"],
    y=daily[daily["success"] == False]["n"],
    marker_color="#ef4444",
    marker_line_width=0,
))
fig.update_layout(
    barmode="stack",
    bargap=0.25,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=20, b=20, l=0, r=0),
    height=340,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    xaxis=dict(title="", type="date", dtick=86400000.0, tickformat="%d %b", showgrid=False),
    yaxis=dict(title="Consultas", gridcolor="#f1f5f9", zeroline=False),
    font=dict(family="Inter, sans-serif", size=13, color="#334155"),
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)

# ── Gráfico: consultas acumuladas ────────────────────────────────────────────
_section_header("Consultas acumuladas", "📊")

cum = df.groupby("date").size().reset_index(name="n").sort_values("date")
cum["acumulado"] = cum["n"].cumsum()

fig_cum = go.Figure()
fig_cum.add_trace(go.Scatter(
    x=cum["date"],
    y=cum["acumulado"],
    mode="lines+markers",
    line=dict(color="#2563eb", width=2.5),
    marker=dict(size=7, color="#2563eb"),
    fill="tozeroy",
    fillcolor="rgba(37,99,235,0.08)",
    hovertemplate="%{x|%d %b}<br><b>%{y:,}</b> consultas acumuladas<extra></extra>",
))
fig_cum.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=20, b=20, l=0, r=0),
    height=300,
    showlegend=False,
    xaxis=dict(title="", type="date", dtick=86400000.0, tickformat="%d %b", showgrid=False),
    yaxis=dict(title="Consultas acumuladas", gridcolor="#f1f5f9", zeroline=False),
    font=dict(family="Inter, sans-serif", size=13, color="#334155"),
    hovermode="x unified",
)
st.plotly_chart(fig_cum, use_container_width=True)

# ── Heat map: patrón semanal (Lunes-Domingo × hora) ─────────────────────────
_section_header("Patrón semanal", "🔥")
st.caption("Promedio de consultas por día de la semana y hora, a lo largo de todo el período seleccionado.")

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

df["hour"]    = df["createdAt"].dt.hour
df["weekday"] = df["createdAt"].dt.weekday  # 0=lunes

heat = df.groupby(["date", "weekday", "hour"]).size().reset_index(name="n")
pattern = (
    heat.groupby(["weekday", "hour"])["n"].mean()
    .reset_index()
    .pivot(index="weekday", columns="hour", values="n")
    .reindex(index=range(7), columns=range(24), fill_value=0)
    .round(1)
)

fig_heat = go.Figure(data=go.Heatmap(
    z=pattern.values,
    x=[f"{h:02d}h" for h in pattern.columns],
    y=DIAS_ES,
    colorscale=[[0, "#eff6ff"], [1, "#1d4ed8"]],
    xgap=2,
    ygap=2,
    hovertemplate="%{y} · %{x}<br><b>%{z}</b> consultas promedio<extra></extra>",
    colorbar=dict(title="Promedio", thickness=14, outlinewidth=0),
))
fig_heat.update_layout(
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(t=20, b=20, l=0, r=0),
    height=260,
    xaxis=dict(title="", showgrid=False, dtick=1),
    yaxis=dict(title="", showgrid=False, autorange="reversed"),
    font=dict(family="Inter, sans-serif", size=12, color="#334155"),
)
st.plotly_chart(fig_heat, use_container_width=True)

# ── Gráfico 2: motivos de falla ──────────────────────────────────────────────
_section_header("Motivos de falla", "🧭")

fail_df = df[~df["success"]]

if fail_df.empty:
    st.success("Sin fallas en el período seleccionado.")
else:
    reasons = (
        fail_df.groupby("error")
        .agg(n=("id", "count"), statusCode=("statusCode", "max"))
        .reset_index()
        .sort_values("n", ascending=True)
    )
    n_fail_total = len(fail_df)
    reasons["pct"] = (reasons["n"] / n_fail_total * 100).round(1)
    colors = ["#ef4444" if sc >= 500 else "#f59e0b" for sc in reasons["statusCode"]]

    top = reasons.iloc[-1]
    st.caption(
        f"**{top['pct']}%** de las consultas fallidas son por "
        f"**\"{top['error']}\"** — {'un error de sistema' if top['statusCode'] >= 500 else 'una respuesta de negocio (no es un error técnico)'}."
    )

    fig2 = go.Figure()
    fig2.add_trace(go.Bar(
        x=reasons["n"],
        y=reasons["error"],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{n:,} · {p}%" for n, p in zip(reasons["n"], reasons["pct"])],
        textposition="outside",
        cliponaxis=False,
        hovertemplate="%{y}<br><b>%{x:,}</b> consultas<extra></extra>",
    ))
    fig2.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=20, b=20, l=0, r=80),
        height=max(200, 56 * len(reasons)),
        showlegend=False,
        xaxis=dict(title="Consultas fallidas", gridcolor="#f1f5f9", zeroline=False),
        yaxis=dict(title="", showgrid=False, automargin=True),
        font=dict(family="Inter, sans-serif", size=13, color="#334155"),
    )
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("🟠 Respuesta de negocio (4xx) · 🔴 Error de sistema (5xx)")

    # ── Detalle: RUTs con "Upstream unknown error" ──────────────────────────
    upstream_errors = fail_df[fail_df["error"] == "Upstream unknown error"].sort_values("createdAt", ascending=False)
    if not upstream_errors.empty:
        _section_header(f"RUTs con \"Upstream unknown error\" ({len(upstream_errors)})", "🛠️")
        rows_html = "".join(
            f'<tr><td>{r.rut}</td><td>{r.createdAt.strftime("%d-%m-%Y %H:%M")}</td><td>{r.statusCode}</td></tr>'
            for r in upstream_errors.itertuples()
        )
        st.markdown(f"""
        <table class="detail-table">
            <thead><tr><th>RUT</th><th>Fecha</th><th>Status</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)
