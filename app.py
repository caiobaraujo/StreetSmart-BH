import streamlit as st
from engines.weather_service import obter_previsao_bh
from engines.recommendation_engine import RecommendationEngine
import datetime

st.set_page_config(page_title="StreetSmart BH v3.0", page_icon="🛒", layout="wide")
st.title("🛒 StreetSmart BH v3.0 — O que vender hoje?")

@st.cache_resource
def get_engine():
    return RecommendationEngine()

engine = get_engine()

with st.sidebar:
    st.header("⚙️ Status")
    clima = obter_previsao_bh()
    if clima:
        st.metric("🌡️ Temperatura", f"{clima['temperatura']:.1f}°C")
        st.metric("🌧️ Condição", clima['descricao'].capitalize())
        if clima.get("simulado"):
            st.warning("⚠️ Dados simulados")
    st.divider()
    st.caption("v3.0 • Regras + XGBoost + NLP")
    st.caption("Pesos: Clima 30% | Data 10% | Hora 15% | Evento 25% | ML 20%")

if st.button("🔍 Recomendar agora", use_container_width=True, type="primary"):
    with st.spinner("🧠 Analisando clima, eventos, rodando NLP e XGBoost..."):
        resultado = engine.calcular_recomendacao()

    if resultado and resultado["recomendacao"]:
        rec = resultado["recomendacao"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Recomendado", rec["produto"].title())
        col2.metric("📊 Score", f"{rec['score']}/100")
        col3.metric("💰 Lucro Est.", f"R$ {rec['lucro_estimado']:.2f}")
        col4.metric("📈 Margem", f"{rec['margem']:.1f}%")

        st.divider()
        col_esq, col_dir = st.columns([2, 1])
        with col_esq:
            st.subheader("📋 Detalhes")
            st.markdown(f"**🕐 Vendas estimadas:** {rec['vendas_estimadas']} unidades")
            st.markdown(f"**🚚 Fornecedor:** {engine.sugerir_fornecedor(rec['produto'])}")
            st.markdown(f"**💵 Preço:** R$ {rec['preco_venda']:.2f} | **Custo:** R$ {rec['custo']:.2f}")
            st.subheader("🧠 Explicações")
            for exp in resultado["explicacoes"]:
                st.markdown(f"- {exp}")
        with col_dir:
            st.subheader("🔄 Alternativas")
            for alt in resultado["alternativas"]:
                st.metric(alt["produto"].title(), f"{alt['score']}/100",
                         delta=f"-{rec['score'] - alt['score']:.1f} pts")
    else:
        st.error("❌ Não foi possível gerar recomendação.")

st.caption(f"🕒 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")