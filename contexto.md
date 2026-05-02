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
- `app.py` atualizado com métricas climáticas e recomendação baseada em regras
- Sidebar com status da API e expander com dados brutos

## Correção (entre Passo 2 e 3)

- Funções `_sugerir_horario` e `_sugerir_local` movidas para o topo do `app.py`
- NameError resolvido

## Passo 3 — Motor de Recomendação com Pesos Estatísticos (Data Science)

- Criado `recommendation_engine.py` com classe `RecommendationEngine`
- Matriz de decisão multi-fatorial com 4 dimensões:
  1. **Clima** (35%): adequação do produto à condição climática
  2. **Data** (15%): sazonalidade por dia da semana
  3. **Hora** (20%): picos de consumo por horário
  4. **Eventos** (30%): demanda concentrada por tipo de evento
- Catálogo de 9 produtos em `data/produtos.json` com atributos:
  - custo, preço de venda, margem
  - climas favoráveis/desfavoráveis
  - dias da semana favoráveis
  - horários de pico
  - eventos associados
  - categoria, perecibilidade, peso na mochila
- Sistema de pontuação normalizada (0-1) por fator:
  - Clima: match exato ou temperatura como proxy
  - Data: dias favoráveis com score proporcional
  - Hora: decaimento gaussiano a partir do pico mais próximo
  - Evento: match entre tipo de evento e produto
- Score final = soma ponderada convertida para 0-100
- Lucro estimado = (preço - custo) × (score/100) × 50 unidades
- Top 3 produtos com scores comparativos
- Explicações textuais baseadas no fator de maior influência
- Sugestão de local por categoria × clima × evento
- Mapeamento de fornecedores por produto
- `app.py` refatorado com layout wide, colunas, progress bars por fator

### Eventos (simulação)

- Sábado → Show no Mineirão
- Domingo → Feira Hippie
- Quarta/Quinta → Congresso no Expominas
- (Passo 4 substituirá por API real)

## Próximos passos

- Integrar Portal de Dados Abertos PBH (eventos reais)
- Coleta de tendências em redes sociais
- API de fluxo de pedestres (Google Popular Times ou similar)
- Modelo ML supervisionado para calibrar pesos automaticamente
- Histórico de vendas do usuário para personalização
- Módulo de precificação dinâmica
