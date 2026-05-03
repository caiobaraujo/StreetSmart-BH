# StreetSmart BH — Histórico do Projeto

## Versão 3.0 — Arquitetura Híbrida Inteligente

### 📂 Estrutura Atual

````text
street_smart_bh/
├── app.py                     # Frontend Streamlit
├── context/
│   ├── contexto.md            # Este arquivo (memória do projeto)
│   └── contexto_ia.txt        # Export consolidado para IAs
├── data/
│   ├── produtos.json          # 13 produtos com atributos reais
│   ├── eventos_cache.json     # Cache de eventos (6h de validade)
│   └── training_data.csv      # 5000 amostras de treino sintéticas
├── engines/
│   ├── __init__.py            # Torna a pasta um módulo Python
│   ├── weather_service.py     # OpenWeather API 3.0 (chave via .env)
│   ├── event_service.py       # Eventos: PBH + Sympla + Eventbrite
│   ├── nlp_classifier.py      # BERTimbau via Hugging Face (zero-shot)
│   └── recommendation_engine.py # Híbrido: regras + XGBoost + NLP
├── models/
│   └── xgboost_model.json     # Modelo XGBoost treinado
├── train_model.py             # Gera dados sintéticos e treina XGBoost
├── export_contexto.py         # Gera contexto_ia.txt consolidado
├── requirements.txt           # Dependências Python
├── Makefile                   # Comandos úteis (make install, make run)
├── .env.example               # Template de variáveis de ambiente
├── .env                       # Chaves reais (NUNCA commitar)
└── .gitignore                 # Exclui venv, .env, pycache, models
text

### Tecnologias utilizadas

- **Clima:** OpenWeather API 3.0 (plano gratuito, 1000 chamadas/dia)
- **Eventos:** Portal Dados Abertos PBH (CKAN), Sympla API, Eventbrite API
- **NLP:** `facebook/bart-large-mnli` via Hugging Face transformers (zero-shot classification)
- **ML:** XGBoost Regressor (scikit-learn + xgboost)
- **Frontend:** Streamlit (gratuito)
- **Cache:** Clima 10 minutos, Eventos 6 horas

### Como rodar o projeto

```bash
# 1. Clonar e instalar
git clone <repo>
cd street_smart_bh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configurar chaves
cp .env.example .env
nano .env  # Coloque sua chave OPENWEATHER_API_KEY

# 3. Treinar modelo
python train_model.py

# 4. Rodar
streamlit run app.py
Métricas e parâmetros
13 produtos catalogados com margens reais (50% a 75%)

5000 amostras de treino sintéticas geradas com regras realistas

5 fatores de decisão:

Clima: 30%

Data (dia da semana): 10%

Hora: 15%

Eventos (classificados via NLP): 25%

Modelo ML (XGBoost): 20%

12 categorias de eventos classificadas pelo NLP

Cache clima: 10 minutos | Cache eventos: 6 horas

Fallback simulado quando APIs estão offline (com indicador ⚠️)

Funcionalidades implementadas
✅ Recomendação multi-fatorial com scores normalizados (0-100)

✅ Classificação NLP de eventos (substituiu regex frágil)

✅ Modelo XGBoost treinado (substituiu pesos fixos arbitrários)

✅ Explicações em português sobre o fator decisivo

✅ Estimativa de lucro baseada em vendas × margem

✅ Mapeamento de fornecedores reais de BH

✅ Segurança: chaves em .env, não no código

✅ Export de contexto para continuidade entre IAs

✅ Makefile para comandos simplificados

Funcionalidades planejadas (próximos passos)
⬜ Coleta de feedback real dos ambulantes (botão "Vendi tudo"/"Sobrou")

⬜ Bot WhatsApp usando Twilio API (gratuita para teste)

⬜ Deploy no Streamlit Cloud (grátis)

⬜ Retreino do XGBoost com dados reais de feedback

⬜ Precificação dinâmica baseada em demanda

⬜ Dashboard de histórico de recomendações

Notas técnicas importantes
O NLP usa device=-1 (CPU). Se tiver GPU NVIDIA, mude para device=0

O modelo BART-large-mnli tem ~1.6GB e é baixado na primeira execução

As APIs Sympla e Eventbrite são opcionais — sistema funciona sem elas

O fallback de eventos inclui padrões reais de BH (Feira Hippie, Expominas, blocos)

O XGBoost foi alterado de XGBRegressor (sklearn) para API nativa xgb.train para evitar bug de _estimator_type

O arquivo contexto_ia.txt é gerado por export_contexto.py para enviar a IAs

Os imports em recommendation_engine.py usam caminho completo: from engines.weather_service import ...
````
