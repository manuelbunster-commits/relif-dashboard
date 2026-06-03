"""Página Campaña Junio 1% — leads BCI sin bukId."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import render_dashboard

try:
    st.set_page_config(page_title="Campaña Junio 1%", page_icon="🎯", layout="wide")
except Exception:
    pass

render_dashboard(bank_filter="BCI", chart_scroll=True, show_salary_range=True, dedup_clients=True, campaign_only=True, show_rejection_reason=True)
