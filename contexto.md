# StreetSmart BH – Histórico do Projeto

## Estrutura inicial

- Criação do repositório e ambiente virtual (Python 3)
- Frontend Streamlit com botão e resposta simulada
- Git inicializado com requirements.txt, app.py, .gitignore

## Passo 2 — Integração API de clima (OpenWeather)

- Criado `weather_service.py` com integração à OpenWeather One Call API 3.0
- Coordenadas fixas de BH (-19.9167, -43.9345)
- Fallback para dados simulados quando a API falha ou chave não configurada
- Cache de 10 minutos para não estourar limite gratuito
- `app.py` atualizado: exibe métricas climáticas e recomendação baseada em regras simples:
  - Chuva → guarda-chuva
  - Calor (>30°C) → água gelada
  - Frio (<18°C) → café quente
  - Nublado → pastel
  - Limpo → suco natural
- Sugestão de horário por período (almoço, saída do trabalho) e local adaptado ao clima
- Sidebar com status da API
- Expander com dados técnicos brutos (debug)

## Próximos passos planejados

- Integrar dados de eventos (Portal de Dados Abertos PBH + detecção em redes sociais)
- Criar motor de recomendação com pesos estatísticos
- Adicionar estimativa realista de lucro baseada em custos de fornecedores
- Sugestão inteligente de localização (fluxo de pessoas)
