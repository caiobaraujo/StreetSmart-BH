# StreetSmart BH – Histórico do Projeto

## Estrutura inicial

- Criação do repositório e ambiente virtual (Python 3)
- Frontend Streamlit com botão e resposta simulada
- Git inicializado

## Passo 2 — Integração API de clima (OpenWeather)

- `weather_service.py`: OpenWeather One Call API 3.0
- Coordenadas BH (-19.9167, -43.9345)
- Cache 10 min, fallback simulado

## Passo 3 — Motor de Recomendação com Pesos Estatísticos

- `recommendation_engine.py`: matriz multi-fatorial (clima 35%, data 15%, hora 20%, eventos 30%)
- Catálogo 9 produtos em `data/produtos.json`
- Scores normalizados + explicações + fornecedores mapeados

## Passo 4A — Eventos Reais + Casos de Mercado

- **event_service.py**: integração com 3 APIs:
  - Portal Dados Abertos PBH (CKAN) — eventos oficiais
  - Sympla API — shows, festas, congressos em BH
  - Eventbrite API — eventos internacionais/locais
- Fallback com padrões reais de BH (Feira Hippie, blocos, Expominas)
- Cache de 6 horas em `data/eventos_cache.json`
- **+4 produtos** baseados em casos reais:
  - Drink pronto latinha (faturamento R$ 3k/dia no Carnaval)
  - Palha italiana (300/dia na Praça Sete)
  - Kit lanche saudável (3× faturamento em eventos corporativos)
  - Adereço carnavalesco (permitido PBH)
- **Insights de mercado** incorporados:
  - Posicionamento tático (à frente do bloco, perto de banheiros)
  - Locais de BH consagrados (Praça Sete, Praça da Liberdade, Savassi)
  - Fornecedores reais mapeados (Ceasa, Mercado Central, Shopping Oiapoque)

## Próximos passos

- Histórico de vendas do usuário (feedback loop)
- Modelo ML para calibrar pesos automaticamente
- Precificação dinâmica
- Deploy Streamlit Cloud
