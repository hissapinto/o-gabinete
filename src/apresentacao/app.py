import os

import requests
import streamlit as st

API_URL = os.environ["API_URL"]

st.set_page_config(page_title="O Gabinete", layout="centered")

st.title("O Gabinete")
st.caption("Mapa de Similaridade Politica entre Deputados Federais")
st.markdown("---")

st.subheader("Estado da arquitetura")

try:
    saude = requests.get(f"{API_URL}/health", timeout=5).json()
    st.success(f"Backend respondeu: {saude['status']}")
except requests.RequestException as erro:
    st.error(f"Backend indisponivel: {erro}")
    st.stop()

st.subheader("Deputados na camada de dados")

try:
    resposta = requests.get(f"{API_URL}/deputados", timeout=5)
    resposta.raise_for_status()
    st.dataframe(resposta.json(), use_container_width=True)
except requests.RequestException as erro:
    st.error(f"Nao foi possivel consultar a API: {erro}")
