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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        min-height: 100vh;
    }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stHeader"] { display: none; }

    /* Orbes de fondo */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        top: -20%;
        left: -10%;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(99,102,241,0.18) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    [data-testid="stAppViewContainer"]::after {
        content: '';
        position: fixed;
        bottom: -20%;
        right: -10%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(139,92,246,0.15) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .login-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding-top: 12vh;
    }
    .login-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 20px;
        padding: 2.8rem 2.5rem 2rem;
        width: 100%;
        max-width: 380px;
        box-shadow: 0 25px 50px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
    }
    .login-logo {
        text-align: center;
        margin-bottom: 1.8rem;
    }
    .login-logo img { height: 80px; opacity: 0.95; }
    .login-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.3rem;
        font-family: Inter, sans-serif;
        letter-spacing: -0.02em;
    }
    .login-sub {
        text-align: center;
        font-size: 0.82rem;
        color: rgba(255,255,255,0.45);
        margin-bottom: 2rem;
        font-family: Inter, sans-serif;
    }
    .login-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: rgba(255,255,255,0.6);
        font-family: Inter, sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-bottom: 0.4rem;
    }

    div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
        color: white !important;
        font-size: 0.9rem !important;
        padding: 0.65rem 0.85rem !important;
        font-family: Inter, sans-serif !important;
        transition: all 0.2s !important;
    }
    div[data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,0.3) !important; }
    div[data-testid="stTextInput"] input:focus {
        border-color: rgba(99,102,241,0.7) !important;
        background: rgba(255,255,255,0.1) !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
        outline: none !important;
    }
    /* Ícono del ojo en blanco */
    div[data-testid="stTextInput"] button svg { stroke: rgba(255,255,255,0.4) !important; }

    div[data-testid="stButton"] button {
        width: 100%;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 0.9rem;
        font-weight: 600;
        padding: 0.7rem 1rem;
        margin-top: 0.75rem;
        font-family: Inter, sans-serif;
        letter-spacing: 0.02em;
        box-shadow: 0 4px 15px rgba(99,102,241,0.4);
        transition: all 0.2s;
        cursor: pointer;
    }
    div[data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        box-shadow: 0 6px 20px rgba(99,102,241,0.55);
        transform: translateY(-1px);
    }
    div[data-testid="stButton"] button:active { transform: translateY(0); }

    /* Mensaje de error */
    div[data-testid="stAlert"] {
        background: rgba(239,68,68,0.15) !important;
        border: 1px solid rgba(239,68,68,0.3) !important;
        border-radius: 8px !important;
        color: #fca5a5 !important;
    }
    </style>

    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-logo">
                <img src="https://raw.githubusercontent.com/manuelbunster-commits/relif-dashboard/main/relif-logo-DkXo5dGJ.png">
            </div>
            <div class="login-title">Bienvenido</div>
            <div class="login-sub">Dashboard BCI · Relif</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

def _dashboard():
    render_dashboard(bank_filter="BCI", chart_scroll=True, show_salary_range=True, dedup_clients=True)


pg = st.navigation([
    st.Page(_dashboard,          title="Dashboard BCI",    icon="📊"),
    st.Page("3_Funnel_BCI.py",   title="Funnel BCI × Buk", icon="🔀"),
])
pg.run()
