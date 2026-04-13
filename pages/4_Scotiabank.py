"""Página Scotiabank."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import render_dashboard

st.set_page_config(page_title="Scotiabank", page_icon="🏦", layout="wide")

# ── Protección con contraseña ──
_PASSWORD = st.secrets.get("SCOTIA_PASSWORD", os.environ.get("SCOTIA_PASSWORD", ""))

if not st.session_state.get("scotia_auth"):
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0f172a 0%, #1a0a0a 50%, #0f172a 100%);
        min-height: 100vh;
    }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stHeader"] { display: none; }

    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        top: -20%; left: -10%;
        width: 600px; height: 600px;
        background: radial-gradient(circle, rgba(218,41,28,0.18) 0%, transparent 70%);
        border-radius: 50%; pointer-events: none;
    }
    [data-testid="stAppViewContainer"]::after {
        content: '';
        position: fixed;
        bottom: -20%; right: -10%;
        width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(218,41,28,0.12) 0%, transparent 70%);
        border-radius: 50%; pointer-events: none;
    }

    .login-wrapper {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        padding-top: 12vh;
    }
    .login-card {
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 20px;
        padding: 2.8rem 2.5rem 2rem;
        width: 100%; max-width: 380px;
        box-shadow: 0 25px 50px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
    }
    .login-title {
        text-align: center; font-size: 1.5rem; font-weight: 700;
        color: #ffffff; margin-bottom: 0.3rem;
        font-family: Inter, sans-serif; letter-spacing: -0.02em;
    }
    .login-sub {
        text-align: center; font-size: 0.82rem;
        color: rgba(255,255,255,0.45); margin-bottom: 2rem;
        font-family: Inter, sans-serif;
    }
    .login-icon {
        text-align: center; font-size: 3rem; margin-bottom: 1.2rem;
    }
    div[data-testid="stTextInput"] input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important; color: white !important;
        font-size: 0.9rem !important; padding: 0.65rem 0.85rem !important;
        font-family: Inter, sans-serif !important; transition: all 0.2s !important;
    }
    div[data-testid="stTextInput"] input::placeholder { color: rgba(255,255,255,0.3) !important; }
    div[data-testid="stTextInput"] input:focus {
        border-color: rgba(218,41,28,0.7) !important;
        background: rgba(255,255,255,0.1) !important;
        box-shadow: 0 0 0 3px rgba(218,41,28,0.2) !important;
        outline: none !important;
    }
    div[data-testid="stTextInput"] button svg { stroke: rgba(255,255,255,0.4) !important; }
    div[data-testid="stButton"] button {
        width: 100%;
        background: linear-gradient(135deg, #da291c, #b91c1c);
        color: white; border: none; border-radius: 10px;
        font-size: 0.9rem; font-weight: 600;
        padding: 0.7rem 1rem; margin-top: 0.75rem;
        font-family: Inter, sans-serif; letter-spacing: 0.02em;
        box-shadow: 0 4px 15px rgba(218,41,28,0.4);
        transition: all 0.2s; cursor: pointer;
    }
    div[data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #b91c1c, #991b1b);
        box-shadow: 0 6px 20px rgba(218,41,28,0.55);
        transform: translateY(-1px);
    }
    div[data-testid="stAlert"] {
        background: rgba(239,68,68,0.15) !important;
        border: 1px solid rgba(239,68,68,0.3) !important;
        border-radius: 8px !important; color: #fca5a5 !important;
    }
    </style>

    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-icon">🏦</div>
            <div class="login-title">Bienvenido</div>
            <div class="login-sub">Dashboard Scotiabank · Relif</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 2, 1])
    with col:
        pwd = st.text_input("Contraseña", type="password", label_visibility="collapsed",
                            placeholder="Ingresa tu contraseña",
                            on_change=lambda: st.session_state.update({"scotia_submit": True}))
        if st.button("Ingresar") or st.session_state.pop("scotia_submit", False):
            if pwd == _PASSWORD:
                st.session_state["scotia_auth"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    st.stop()

render_dashboard(bank_filter="Scotiabank", chart_scroll=True, show_salary_range=True, dedup_clients=True)
