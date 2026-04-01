"""Página BCI."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import render_dashboard

st.set_page_config(page_title="BCI", page_icon="https://raw.githubusercontent.com/manuelbunster-commits/relif-dashboard/main/bci_logo.png", layout="wide")

# ── Protección con contraseña ──
_PASSWORD = st.secrets.get("BCI_PASSWORD", os.environ.get("BCI_PASSWORD", ""))

if not st.session_state.get("bci_auth"):
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #f8fafc; }
    [data-testid="stSidebar"] { display: none; }
    .login-card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
        padding: 2.5rem 2.5rem 2rem;
        max-width: 380px;
        margin: 8vh auto 0;
    }
    .login-logo { text-align: center; margin-bottom: 1.5rem; }
    .login-logo img { height: 40px; }
    .login-title {
        text-align: center;
        font-size: 1.25rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.25rem;
        font-family: Inter, sans-serif;
    }
    .login-sub {
        text-align: center;
        font-size: 0.85rem;
        color: #94a3b8;
        margin-bottom: 1.8rem;
        font-family: Inter, sans-serif;
    }
    div[data-testid="stTextInput"] input {
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        font-size: 0.9rem !important;
        padding: 0.55rem 0.75rem !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
    }
    div[data-testid="stButton"] button {
        width: 100%;
        background: #6366f1;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 0.9rem;
        font-weight: 600;
        padding: 0.6rem 1rem;
        margin-top: 0.5rem;
        transition: background 0.2s;
    }
    div[data-testid="stButton"] button:hover { background: #4f46e5; }
    </style>
    <div class="login-card">
        <div class="login-logo">
            <img src="https://relif.com/favicon.png" onerror="this.style.display='none'">
        </div>
        <div class="login-title">Bienvenido</div>
        <div class="login-sub">Dashboard BCI · Relif</div>
    </div>
    """, unsafe_allow_html=True)

    # Contenido del form dentro de la card via columnas centradas
    _, col, _ = st.columns([1, 2, 1])
    with col:
        pwd = st.text_input("Contraseña", type="password", label_visibility="collapsed",
                            placeholder="Ingresa tu contraseña",
                            on_change=lambda: st.session_state.update({"bci_submit": True}))
        if st.button("Ingresar") or st.session_state.pop("bci_submit", False):
            if pwd == _PASSWORD:
                st.session_state["bci_auth"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    st.stop()

render_dashboard(bank_filter="BCI", chart_scroll=True, show_salary_range=True, dedup_clients=True)
