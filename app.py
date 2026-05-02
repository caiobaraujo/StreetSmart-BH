import streamlit as st
from weather_service import obter_previsao_bh
import datetime

# ═══════════════════════════════════════════════════
# FUNÇÕES AUXILIARES (definidas ANTES de usar)
# ═══════════════════════════════════════════════════

def _sugerir_horario(clima):
    """Sugere horário baseado na condição climática"""
    agora = datetime.datetime.now().hour
    if clima["condicao"] == "chuva":
        return "Assim que a chuva começar (consulte radar meteorológico)"
    elif 11 <= agora <= 13:
        return "11:30 – 13:30 (horário de almoço)"
    elif 17 <= agora <= 19:
        return "17:00 – 19:00 (saída do trabalho)"
    return "10:00 – 16:00 (movimento constante)"


def _sugerir_local(clima):
    """Sugere local baseado na condição climática"""
    if clima["condicao"] == "chuva":
        return "Áreas cobertas: shopping centers, marquises da Praça Sete"
    elif clima["temperatura"] > 30:
        return "Praças com sombra: Praça da Liberdade, Parque Municipal"
    return "Praça Sete – Centro (fluxo tradicional)"


# ═══════════════════════════════════════════════════
# CONFIGURAÇÃO DA PÁGINA
# ═══════════════════════════════════════════════════

st.set_page_config(page_title="StreetSmart BH", page_icon="🛒")
st.title("📊 StreetSmart BH – O que vender hoje em Belo Horizonte?")

# Sidebar com informações de debug
with st.sidebar:
    st.header("⚙️ Status do sistema")
    clima_debug = obter_previsao_bh()
    st.write("API OpenWeather:", "🟢 Conectada" if clima_debug else "🔴 Falha")
    st.write("Atualizado:", datetime.datetime.now().strftime("%H:%M:%S"))

# ═══════════════════════════════════════════════════
# BOTÃO PRINCIPAL E LÓGICA DE RECOMENDAÇÃO
# ═══════════════════════════════════════════════════

if st.button("🔍 Descobrir recomendação do dia", use_container_width=True):
    clima = obter_previsao_bh()

    if clima is None:
        st.error("❌ Não foi possível obter a previsão do tempo. Verifique sua conexão e a chave da API.")
    else:
        # Mostra dados climáticos
        col1, col2, col3 = st.columns(3)
        col1.metric("🌡️ Temperatura", f"{clima['temperatura']:.1f}°C")
        col2.metric("💧 Umidade", f"{clima['umidade']}%")
        col3.metric("🌧️ Chuva", f"{clima['chuva_mm']:.1f} mm")

        st.info(f"**Condição atual:** {clima['descricao'].capitalize()}")

        # Lógica de recomendação baseada no clima (simples, será expandida)
        st.subheader("📦 Recomendação do Sistema")

        if clima["condicao"] in ["chuva", "tempestade", "garoa"]:
            produto = "Guarda-chuva compacto"
            explicacao = "Precipitação detectada — alta demanda por proteção contra chuva"

        elif clima["temperatura"] > 30:
            produto = "Água mineral gelada (500ml)"
            explicacao = "Temperatura acima de 30°C — hidratação é prioridade"

        elif clima["temperatura"] < 18:
            produto = "Café quente (200ml)"
            explicacao = "Temperatura baixa para BH — bebidas quentes têm alta conversão"

        elif clima["condicao"] == "nublado":
            produto = "Pastel frito na hora"
            explicacao = "Clima ameno e nublado — alimentos de rua têm apelo emocional"

        else:
            produto = "Suco natural (laranja)"
            explicacao = "Dia limpo — bebidas refrescantes são a melhor escolha"

        st.success(f"**{produto}**")
        st.markdown(f"*Por quê:* {explicacao}")
        st.markdown(f"**Horário ideal:** {_sugerir_horario(clima)}")
        st.markdown(f"**Local:** {_sugerir_local(clima)}")

        with st.expander("🔬 Dados técnicos (debug)"):
            st.json(clima)

st.caption(f"Última atualização: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")