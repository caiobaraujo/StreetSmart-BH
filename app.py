import streamlit as st

st.set_page_config(page_title="StreetSmart BH", page_icon="🛒")
st.title("📊 StreetSmart BH – O que vender hoje em Belo Horizonte?")

# Botão principal
if st.button("🔍 Descobrir recomendação do dia"):
    # Por enquanto, resposta estática
    st.success("Recomendação do dia:")
    st.markdown("**Produto:** Guarda-chuva (proteção extra para garoa)")
    st.markdown("**Horário:** 16:00 – 18:00")
    st.markdown("**Local:** Praça Sete – Centro")
    st.markdown("**Fornecedor sugerido:** Atacadão Central (R$ 8/un)")
    st.markdown("**Lucro estimado:** +160% de margem")
    st.write("---")
    st.caption("Em breve: explicações detalhadas baseadas em clima, eventos e fluxo de pessoas.")