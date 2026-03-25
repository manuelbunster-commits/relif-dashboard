"""Página de prueba de diseño."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils_v2 import render_dashboard

st.set_page_config(page_title="Prueba", page_icon="🧪", layout="wide")
render_dashboard()  # Sin filtro = vista Consolidado
