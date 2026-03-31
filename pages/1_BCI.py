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
    st.markdown("<div style='max-width:360px;margin:6rem auto'>", unsafe_allow_html=True)
    st.markdown("### 🔒 Acceso BCI")
    pwd = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        if pwd == _PASSWORD:
            st.session_state["bci_auth"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

render_dashboard(bank_filter="BCI", chart_scroll=True, show_salary_range=True, dedup_clients=True)
