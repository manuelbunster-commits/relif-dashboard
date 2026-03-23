"""Página principal — Consolidado."""
import streamlit as st
from utils import render_dashboard

st.set_page_config(page_title="Consolidado", page_icon="https://relif.com/favicon.png", layout="wide")
render_dashboard()
