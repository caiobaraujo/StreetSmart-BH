# StreetSmart BH AI Project Memory

## Project Purpose

StreetSmart BH is a Python + Streamlit decision-support app for street vendors in Belo Horizonte, Brazil. It recommends what product a vendor should sell on a given day by combining weather conditions, event signals, NLP-based event classification, and an XGBoost model.

The end user is a local street vendor or someone simulating that workflow. The problem being solved is day-to-day product selection under uncertainty: vendors need a fast recommendation that balances demand drivers such as climate, time, day of week, and local events.

## Current Architecture

- `app.py`
  Streamlit UI entry point. Owns session state, sidebar status display, recommendation trigger button, recommendation rendering, and feedback buttons.
- `engines/weather_service.py`
  Fetches Belo Horizonte weather from Open-Meteo. Keeps a short in-memory cache and falls back to simulated weather when the API is unavailable.
- `engines/event_service.py`
  Collects events from PBH, Sympla, and Eventbrite, with a disk cache in `data/eventos_cache.json`. Falls back to local default event patterns when live sources fail or return nothing.
- `engines/nlp_classifier.py`
  Uses Hugging Face `facebook/bart-large-mnli` for zero-shot event classification. Must degrade safely if model loading or inference fails.
- `engines/recommendation_engine.py`
  Main orchestration layer. Loads products, events, and the XGBoost model; computes hybrid recommendation scores; returns the payload used by the UI. It now supports small constructor-level dependency injection points for testing: `weather_provider`, `event_provider`, `nlp_classifier`, `now_provider`, and `model`.
- `engines/app_support.py`
  Small helper module for app-facing data contracts. Handles feedback CSV persistence and lightweight recommendation payload validation.
- `train_model.py`
  Generates synthetic training data and trains `models/xgboost_model.json`.
- `data/`
  Stores product catalog, cached events, synthetic training data, and runtime feedback CSV.
- `models/`
  Stores the trained XGBoost model expected by the recommendation engine.

## Data Contracts

### `RecommendationEngine.calcular_recomendacao()`

Expected top-level result shape:

```python
{
    "recomendacao": {...},
    "alternativas": [...],
    "explicacoes": [...],
    "clima": {...},
    "eventos": [...],
    "hora_consulta": "HH:MM",
    "data_consulta": "DD/MM/YYYY",
}
```

For deterministic tests, pass explicit providers into `RecommendationEngine(...)` and/or pass a `clima` payload directly into `calcular_recomendacao(clima=...)`. This is the preferred mock strategy over patching external APIs.

### `resultado["recomendacao"]`

Required fields:

- `produto`
- `score`
- `lucro_estimado`
- `vendas_estimadas`
- `margem`
- `custo`
- `preco_venda`
- `categoria`
- `metricas`

`metricas` is expected to be a dictionary used by the Streamlit progress bars.

### Climate payload

Expected minimum fields:

- `condicao`
- `descricao`
- `temperatura`
- `umidade`
- `chuva_mm`

Common additional fields currently returned by `weather_service`:

- `sensacao_termica`
- `icone`
- `data_hora`
- `simulado`

### Feedback CSV columns

`data/feedback.csv` must keep these columns:

- `timestamp`
- `produto`
- `score`
- `status`
- `temperatura`
- `chuva_mm`
- `umidade`
- `condicao`
- `hora`
- `data`
- `vendas_estimadas`
- `lucro_estimado`

## Important Runtime Behavior

- Weather can fall back to simulated data when Open-Meteo is unreachable.
- Event discovery can fall back to cache or to local default Belo Horizonte event patterns.
- NLP model loading is optional at runtime from a stability perspective. If the Hugging Face model fails to download or initialize, event classification should return a safe neutral result instead of crashing the app.
- The XGBoost model may be missing or fail during prediction. That must not crash the UI; the engine should continue with fallback scoring.
- External APIs are unreliable during local development and CI-like environments. Future work should assume offline or DNS-restricted execution is common.

## Testing Strategy

- Unit tests must avoid live weather/event APIs, Hugging Face downloads, and network access.
- `RecommendationEngine` should be tested with injected fake providers rather than with global monkeypatching whenever practical.
- Deterministic recommendation tests should freeze time with `now_provider`, inject fixed event lists with `event_provider`, and use either `model=None` or a fake model object.
- Ranking tests should assert stable product outcomes or top-tier membership in realistic scenarios, but should avoid brittle exact-score assertions unless the inputs are fully controlled.

## Development Rules for Future Codex Tasks

- Do not commit `.env`, API keys, tokens, or other secrets.
- Do not introduce paid services or external infrastructure without explicit approval.
- Keep changes small, local, and easy to review.
- Preserve Portuguese UX copy unless the task explicitly asks for language changes.
- Prefer robust fallbacks over hard crashes.
- When changing architecture, core behavior, or data contracts, update this file in the same task.

## Current Known Risks / TODOs

- NLP startup latency is still high because `facebook/bart-large-mnli` may need network access or a large local cache.
- Event API integrations still need real-world validation against actual PBH, Sympla, and Eventbrite responses.
- The UI still depends on a nested recommendation schema staying stable.
- The automated test layer is intentionally minimal and should be expanded around recommendation scoring and service fallback behavior.
