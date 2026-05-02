import streamlit as st
import datetime
from weather_service import obter_previsao_bh
from recommendation_engine import RecommendationEngine

# ═══════════════════════════════════════════════════
# INICIALIZAÇÃO (cache para não recarregar o motor a cada clique)
# ═══════════════════════════════════════════════════

@st.cache_resource
def get_engine():
    return RecommendationEngine()

engine = get_engine()

# ═══════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════

st.set_page_config(page_title="StreetSmart BH", page_icon="🛒", layout="wide")
st.title("📊 StreetSmart BH – O que vender hoje em Belo Horizonte?")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    clima_preview = obter_previsao_bh()
    if clima_preview:
        st.metric("🌡️ Temperatura", f"{clima_preview['temperatura']:.1f}°C")
        st.metric("🌧️ Condição", clima_preview['descricao'].capitalize())
    st.divider()
    st.caption("Motor de recomendação v2.0")
    st.caption("Pesos: Clima 35% | Data 15% | Hora 20% | Eventos 30%")

# ═══════════════════════════════════════════════════
# BOTÃO PRINCIPAL
# ═══════════════════════════════════════════════════

if st.button("🔍 Descobrir recomendação do dia", use_container_width=True, type="primary"):
    with st.spinner("🧠 Analisando clima, eventos, dia da semana e horário..."):
        resultado = engine.calcular_recomendacao()
    
    if resultado is None or resultado["recomendacao"] is None:
        st.error("❌ Não foi possível gerar a recomendação.")
    else:
        rec = resultado["recomendacao"]
        clima = resultado["clima"]
        
        # ════ CABEÇALHO COM MÉTRICAS ════
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Produto Recomendado", rec["produto"].title())
        col2.metric("📊 Score Final", f"{rec['score']}/100")
        col3.metric("💰 Lucro Estimado", f"R$ {rec['lucro_estimado']:.2f}")
        col4.metric("📈 Margem", f"{rec['margem']:.1f}%")
        
        st.divider()
        
        # ════ DETALHES ════
        col_esq, col_dir = st.columns([2, 1])
        
        with col_esq:
            st.subheader("📋 Detalhes da Recomendação")
            hora_atual = datetime.datetime.now().hour
            st.markdown(f"**🕐 Melhor horário:** {engine._score_hora(rec['produto'], hora_atual):.0%} de adequação ao horário atual")
            st.markdown(f"**📍 Local sugerido:** {engine.sugerir_local(rec, clima)}")
            st.markdown(f"**🚚 Fornecedor:** {engine.sugerir_fornecedor(rec['produto'])}")
            st.markdown(f"**💵 Preço de venda:** R$ {rec['preco_venda']:.2f} | **Custo:** R$ {rec['custo']:.2f}")
            
            st.subheader("🧠 Por que esta é a melhor escolha?")
            for exp in resultado["explicacoes"]:
                st.markdown(f"- {exp}")
        
        with col_dir:
            st.subheader("🔄 Alternativas")
            if resultado["alternativas"]:
                for alt in resultado["alternativas"]:
                    delta = rec["score"] - alt["score"]
                    st.metric(
                        f"{alt['produto'].title()}",
                        f"Score: {alt['score']}/100",
                        delta=f"-{delta:.1f} pts"
                    )
            else:
                st.write("Nenhuma alternativa próxima")
            
            st.divider()
            st.subheader("📊 Score por Fator")
            metricas = rec["metricas"]
            st.progress(metricas["p_clima"], text=f"Clima: {metricas['p_clima']:.0%}")
            st.progress(metricas["p_data"], text=f"Data: {metricas['p_data']:.0%}")
            st.progress(metricas["p_hora"], text=f"Hora: {metricas['p_hora']:.0%}")
            st.progress(metricas["p_evento"], text=f"Evento: {metricas['p_evento']:.0%}")
        
        # ════ DADOS TÉCNICOS (debug) ════
        with st.expander("🔬 Dados técnicos (debug)"):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.write("**Clima:**", clima)
                st.write("**Eventos detectados:**", resultado["eventos"])
            with col_d2:
                st.write("**Top 3 scores:**")
                # Monta lista com recomendação + alternativas
                top3 = [rec] + resultado["alternativas"]
                for i, item in enumerate(top3):
                    st.write(f"{i+1}. {item['produto'].title()}: {item['score']}/100")

st.caption(f"🕒 Última atualização: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")