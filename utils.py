"""Funciones compartidas entre páginas del dashboard."""

import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

RELIF_AUTH_URL = "https://relif-saas-back-yb2ukoflca-tl.a.run.app/auth"
RELIF_EXECUTE_URL = (
    "https://relif-saas-back-workload-816446680429.southamerica-west1.run.app"
    "/admin/db/execute"
)

STATUS_COLORS = {
    "rejected_by_bank": "#e74c3c",
    "sent_to_bank":     "#f39c12",
    "created":          "#3498db",
}


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
    df["date"] = df["createdAt"].dt.date
    return df


def render_dashboard(bank_filter: str = None):
    """Renderiza el dashboard completo. Si bank_filter está definido, filtra por banco."""

    st.markdown(
        "<style>.block-container{padding-top:1.5rem}</style>",
        unsafe_allow_html=True,
    )

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

    with st.sidebar:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    dc1, dc2 = st.columns(2)
    with dc1:
        start_date = st.date_input("Desde", value=date.today() - timedelta(days=10))
    with dc2:
        end_date = st.date_input("Hasta", value=date.today() + timedelta(days=1))

    with st.spinner("Cargando datos desde Relif..."):
        df_raw = fetch_data(str(start_date), str(end_date))

    if df_raw.empty:
        st.warning("No hay datos para el período seleccionado.")
        return

    if bank_filter:
        df_raw = df_raw[df_raw["bank"] == bank_filter]
        if df_raw.empty:
            st.warning(f"No hay datos para {bank_filter} en el período seleccionado.")
            return

    m1, m2, m3, pie_col = st.columns([1, 1, 1, 2])
    with m1:
        st.metric("Total requests", len(df_raw))
    with m2:
        st.metric("Rechazadas", (df_raw["status"] == "rejected_by_bank").sum())
    with m3:
        st.metric("Enviadas al banco", (df_raw["status"] == "sent_to_bank").sum())
    with pie_col:
        sc = df_raw["status"].value_counts().reset_index()
        sc.columns = ["status", "count"]
        fig_pie = px.pie(
            sc, names="status", values="count",
            color="status", color_discrete_map=STATUS_COLORS, hole=0.35,
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent")
        fig_pie.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=220)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    st.markdown("**Resumen**")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.caption("Por banco")
        st.dataframe(
            df_raw.groupby("bank").size().reset_index(name="Count")
            .sort_values("Count", ascending=False),
            hide_index=True, use_container_width=True, height=160,
        )
    with t2:
        st.caption("Por status")
        st.dataframe(
            df_raw.groupby("status").size().reset_index(name="Count")
            .sort_values("Count", ascending=False),
            hide_index=True, use_container_width=True, height=160,
        )
    with t3:
        st.caption("Por RUT (top 10)")
        st.dataframe(
            df_raw.groupby("rut").size().reset_index(name="Count")
            .sort_values("Count", ascending=False).head(10),
            hide_index=True, use_container_width=True, height=160,
        )

    st.divider()

    st.markdown("**Detalle de registros**")
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

    st.dataframe(
        df_f[["id","bukLeadId","bank","status","rut","createdAt","updatedAt"]]
        .sort_values("createdAt", ascending=False),
        hide_index=True, use_container_width=True, height=300,
    )

    st.divider()

    st.markdown("**Análisis temporal**")

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

    st.caption("Requests por día")
    by_day = df_g.groupby("date").size().reset_index(name="Count")
    fig_bar_day = px.bar(by_day, x="date", y="Count",
                         color_discrete_sequence=["#3498db"])
    fig_bar_day.update_layout(margin=dict(t=10, b=10), height=260, xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_bar_day, use_container_width=True)

    st.caption("Por banco y status (%)")
    by_bs = df_raw.groupby(["bank","status"]).size().reset_index(name="count")
    totals = by_bs.groupby("bank")["count"].transform("sum")
    by_bs["pct"] = by_bs["count"] / totals
    fig_bar = px.bar(
        by_bs, x="pct", y="bank", color="status", orientation="h",
        color_discrete_map=STATUS_COLORS, barmode="stack",
    )
    fig_bar.update_layout(margin=dict(t=10, b=10), height=260,
                          xaxis_tickformat=".0%", xaxis_title="", yaxis_title="")
    st.plotly_chart(fig_bar, use_container_width=True)
