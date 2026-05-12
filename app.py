import datetime
import sys
from pathlib import Path

import streamlit as st

# Garante que a pasta do projeto está no path do Python
sys.path.insert(0, str(Path(__file__).parent))

from engines.recommendation_engine import RecommendationEngine
from engines.app_support import (
    calcular_metricas_historico_feedback,
    carregar_historico_feedback,
    save_feedback_csv,
    validate_recommendation_payload,
)
from engines.weather_service import obter_previsao_bh


@st.cache_resource
def get_engine():
    return RecommendationEngine()


def _salvar_feedback(resultado, status):
    save_feedback_csv(resultado, status, Path("data/feedback.csv"))


def _renderizar_historico_feedback():
    with st.expander("📈 Histórico e desempenho"):
        historico = carregar_historico_feedback(Path("data/feedback.csv"))
        metricas = calcular_metricas_historico_feedback(historico)

        if historico.empty:
            st.info("Nenhum feedback registrado ainda.")
            return

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total de feedbacks", str(metricas["total_feedbacks"]))
        col2.metric("Produto mais frequente", str(metricas["produto_mais_frequente"]).title())
        col3.metric("Lucro estimado total", f"R$ {metricas['lucro_estimado_total']:.2f}")
        col4.metric("Taxa de sucesso", f"{metricas['taxa_sucesso']:.0%}")

        contagem_status = metricas["contagem_status"]
        if not contagem_status.empty:
            st.subheader("📊 Resultado dos feedbacks")
            st.bar_chart(contagem_status)

        contagem_produtos = metricas["produtos_mais_frequentes"]
        if not contagem_produtos.empty:
            st.subheader("🏷️ Produtos mais recorrentes")
            st.bar_chart(contagem_produtos)

        lucro_medio_por_produto = metricas["lucro_medio_por_produto"].head(5)
        if not lucro_medio_por_produto.empty:
            st.subheader("💵 Lucro estimado médio por produto")
            st.bar_chart(lucro_medio_por_produto)

        taxa_sucesso_por_produto = metricas["taxa_sucesso_por_produto"].head(5)
        if not taxa_sucesso_por_produto.empty:
            st.subheader("✅ Taxa de sucesso por produto")
            st.bar_chart(taxa_sucesso_por_produto)

        colunas_tabela = [
            "timestamp",
            "produto",
            "status",
            "score",
            "temperatura",
            "chuva_mm",
            "vendas_estimadas",
            "lucro_estimado",
        ]
        tabela = historico.sort_values("timestamp", ascending=False).head(10).copy()
        if "timestamp" in tabela.columns:
            tabela["timestamp"] = tabela["timestamp"].dt.strftime("%d/%m/%Y %H:%M:%S").fillna("-")

        st.subheader("🧾 Feedbacks recentes")
        st.dataframe(tabela[colunas_tabela], use_container_width=True, hide_index=True)


def _executar_recomendacao(engine):
    try:
        resultado = engine.calcular_recomendacao()
    except Exception as exc:
        st.session_state.resultado_atual = None
        st.session_state.recomendacao_ativa = False
        st.session_state.feedback_enviado = False
        st.error("Não foi possível gerar a recomendação agora.")
        st.exception(exc)
        return

    valido, erros = validate_recommendation_payload(resultado)
    if not valido:
        st.session_state.resultado_atual = None
        st.session_state.recomendacao_ativa = False
        st.session_state.feedback_enviado = False
        st.error("O motor retornou uma resposta inválida. Verifique os logs e dependências do projeto.")
        st.code("\n".join(erros))
        return

    st.session_state.resultado_atual = resultado
    st.session_state.recomendacao_ativa = True
    st.session_state.feedback_enviado = False
    st.rerun()


st.set_page_config(page_title="StreetSmart BH v3.0", page_icon="🛒", layout="wide")
st.title("🛒 StreetSmart BH v3.0 — O que vender hoje em Belo Horizonte?")

try:
    engine = get_engine()
    engine_error = None
except Exception as exc:
    engine = None
    engine_error = exc

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
        st.metric("🌧️ Condição", clima["descricao"].capitalize())
        st.caption(f"Fonte: {status_clima}")
    st.divider()
    st.subheader("📊 Modelos Ativos")
    st.caption("✅ Open-Meteo (clima)")
    st.caption("✅ PBH + Sympla (eventos)")
    st.caption("✅ BART-large-mnli (NLP)")
    st.caption("✅ XGBoost (ML)")
    st.divider()
    st.caption(f"Versão 3.0 | {datetime.datetime.now().strftime('%d/%m/%Y')}")

if engine_error is not None:
    st.error("O motor de recomendação não inicializou corretamente.")
    st.exception(engine_error)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button(
        "🔍 Recomendar Agora",
        use_container_width=True,
        type="primary",
        disabled=engine is None,
    ):
        with st.spinner("🧠 Analisando clima, eventos, NLP e XGBoost..."):
            _executar_recomendacao(engine)

if st.session_state.recomendacao_ativa and st.session_state.resultado_atual:
    rec = st.session_state.resultado_atual["recomendacao"]

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
        st.markdown(
            f"**💵 Preço de venda:** R$ {rec['preco_venda']:.2f} | **Custo:** R$ {rec['custo']:.2f}"
        )
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
                    delta=f"-{delta:.1f} pts",
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

_renderizar_historico_feedback()

st.caption(f"🕒 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | StreetSmart BH v3.0")
