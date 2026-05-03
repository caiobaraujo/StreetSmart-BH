import streamlit as st
import sys
from pathlib import Path

# Garante que a pasta do projeto está no path do Python
sys.path.insert(0, str(Path(__file__).parent))

from engines.weather_service import obter_previsao_bh
from engines.recommendation_engine import RecommendationEngine
import datetime
import json

st.set_page_config(page_title="StreetSmart BH v3.0", page_icon="🛒", layout="wide")
st.title("🛒 StreetSmart BH v3.0 — O que vender hoje em Belo Horizonte?")

@st.cache_resource
def get_engine():
    return RecommendationEngine()

engine = get_engine()

if "recomendacao_ativa" not in st.session_state:
    st.session_state.recomendacao_ativa = False
if "resultado_atual" not in st.session_state:
    st.session_state.resultado_atual = None
if "feedback_enviado" not in st.session_state:
    st.session_state.feedback_enviado = False

with st.sidebar:
    st.header("⚙️ Status do Sistema")
    clima = obter_previsao_bh()
    if clima:
        status_clima = "🟢 Dados reais" if not clima.get("simulado") else "🟡 Dados simulados"
        st.metric("🌡️ Temperatura", f"{clima['temperatura']:.1f}°C")
        st.metric("🌧️ Condição", clima['descricao'].capitalize())
        st.caption(f"Fonte: {status_clima}")
    st.divider()
    st.subheader("📊 Modelos Ativos")
    st.caption("✅ Open-Meteo (clima)")
    st.caption("✅ PBH + Sympla (eventos)")
    st.caption("✅ BART-large-mnli (NLP)")
    st.caption("✅ XGBoost (ML)")
    st.divider()
    st.caption(f"Versão 3.0 | {datetime.datetime.now().strftime('%d/%m/%Y')}")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔍 Recomendar Agora", use_container_width=True, type="primary"):
        with st.spinner("🧠 Analisando clima, eventos, NLP e XGBoost..."):
            st.session_state.resultado_atual = engine.calcular_recomendacao()
            st.session_state.recomendacao_ativa = True
            st.session_state.feedback_enviado = False
        st.rerun()

if st.session_state.recomendacao_ativa and st.session_state.resultado_atual:
    rec = st.session_state.resultado_atual["recomendacao"]
    clima = st.session_state.resultado_atual["clima"]
    
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Produto Recomendado", rec["produto"].title())
    col2.metric("📊 Score Final", f"{rec['score']}/100")
    col3.metric("💰 Lucro Estimado", f"R$ {rec['lucro_estimado']:.2f}")
    col4.metric("📈 Margem", f"{rec['margem']:.1f}%")
    st.divider()
    
    col_esq, col_dir = st.columns([2, 1])
    with col_esq:
        st.subheader("📋 Detalhes da Recomendação")
        st.markdown(f"**🕐 Vendas estimadas:** {rec['vendas_estimadas']} unidades")
        st.markdown(f"**🚚 Fornecedor:** {engine.sugerir_fornecedor(rec['produto'])}")
        st.markdown(f"**💵 Preço de venda:** R$ {rec['preco_venda']:.2f} | **Custo:** R$ {rec['custo']:.2f}")
        st.subheader("🧠 Por que este produto?")
        for exp in st.session_state.resultado_atual["explicacoes"]:
            st.markdown(f"- {exp}")
    
    with col_dir:
        st.subheader("🔄 Alternativas")
        if st.session_state.resultado_atual["alternativas"]:
            for alt in st.session_state.resultado_atual["alternativas"]:
                delta = rec["score"] - alt["score"]
                st.metric(
                    f"{alt['produto'].title()}",
                    f"Score: {alt['score']}/100",
                    delta=f"-{delta:.1f} pts"
                )
        st.divider()
        st.subheader("📊 Score por Fator")
        metricas = rec["metricas"]
        for k, v in metricas.items():
            st.progress(v, text=f"{k}: {v:.0%}")

    st.divider()
    st.subheader("📝 Feedback do Vendedor")
    st.caption("Sua resposta ajuda a melhorar as recomendações futuras!")
    
    if not st.session_state.feedback_enviado:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            if st.button("✅ Vendi Tudo!", use_container_width=True, type="primary"):
                _salvar_feedback(st.session_state.resultado_atual, "vendeu_tudo")
                st.session_state.feedback_enviado = True
                st.rerun()
        with col_f2:
            if st.button("⚠️ Vendi Parcialmente", use_container_width=True):
                _salvar_feedback(st.session_state.resultado_atual, "vendeu_parcial")
                st.session_state.feedback_enviado = True
                st.rerun()
        with col_f3:
            if st.button("❌ Não Vendi", use_container_width=True):
                _salvar_feedback(st.session_state.resultado_atual, "nao_vendeu")
                st.session_state.feedback_enviado = True
                st.rerun()
    else:
        st.success("✅ Feedback registrado! Obrigado por contribuir.")

else:
    st.info("👆 Clique no botão acima para receber sua recomendação personalizada!")

st.caption(f"🕒 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | StreetSmart BH v3.0")

def _salvar_feedback(resultado, status):
    arquivo = Path("data/feedback.csv")
    rec = resultado["recomendacao"]
    novo = {
        "timestamp": datetime.datetime.now().isoformat(),
        "produto": rec["produto"],
        "score": rec["score"],
        "status": status,
        "temperatura": resultado["clima"]["temperatura"],
        "chuva_mm": resultado["clima"]["chuva_mm"],
        "umidade": resultado["clima"]["umidade"],
        "condicao": resultado["clima"]["condicao"],
        "hora": resultado["hora_consulta"],
        "data": resultado["data_consulta"],
        "vendas_estimadas": rec["vendas_estimadas"],
        "lucro_estimado": rec["lucro_estimado"]
    }
    if not arquivo.exists():
        with open(arquivo, "w", encoding="utf-8") as f:
            f.write("timestamp,produto,score,status,temperatura,chuva_mm,umidade,condicao,hora,data,vendas_estimadas,lucro_estimado\n")
    with open(arquivo, "a", encoding="utf-8") as f:
        f.write(f"{novo['timestamp']},{novo['produto']},{novo['score']},{novo['status']},"
                f"{novo['temperatura']},{novo['chuva_mm']},{novo['umidade']},{novo['condicao']},"
                f"{novo['hora']},{novo['data']},{novo['vendas_estimadas']},{novo['lucro_estimado']}\n")
