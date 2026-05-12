# StreetSmart BH AI Project Memory

## Project Purpose

StreetSmart BH is a Python + Streamlit decision-support app for street vendors in Belo Horizonte, Brazil. It recommends what product a vendor should sell on a given day by combining weather conditions, event signals, NLP-based event classification, and an XGBoost model.

The end user is a local street vendor or someone simulating that workflow. The problem being solved is day-to-day product selection under uncertainty: vendors need a fast recommendation that balances demand drivers such as climate, time, day of week, and local events.

## Canonical Status

This file is the canonical technical memory for future Codex/AI sessions.

- If architecture, data contracts, testing strategy, or core runtime behavior changes, update this file in the same commit.
- `context/contexto.md` is a human-facing historical log in Portuguese.
- `context/contexto_ia.txt` is a generated and committed snapshot produced by `python export_contexto.py`.
- No `README.md` is currently tracked in the repository; do not assume one exists.

## Current Architecture

- `app.py`
  Streamlit UI entry point. Owns session state, sidebar status display, recommendation trigger button, recommendation rendering, feedback buttons, and a lightweight feedback-history dashboard expander.
- `engines/weather_service.py`
  Fetches Belo Horizonte weather from Open-Meteo. Keeps a short in-memory cache and falls back to simulated weather when the API is unavailable.
- `engines/event_service.py`
  Collects events from PBH, Sympla, and Eventbrite, with a disk cache in `data/eventos_cache.json`. Falls back to local default event patterns when live sources fail or return nothing.
- `engines/nlp_classifier.py`
  Uses Hugging Face `facebook/bart-large-mnli` for zero-shot event classification. Must degrade safely if model loading or inference fails.
- `engines/recommendation_engine.py`
  Main orchestration layer. Loads products, events, and the XGBoost model; computes hybrid recommendation scores; returns the payload used by the UI. It now supports small constructor-level dependency injection points for testing: `weather_provider`, `event_provider`, `nlp_classifier`, `now_provider`, and `model`.
- `engines/app_support.py`
  Small helper module for app-facing data contracts. Handles feedback CSV persistence, safe feedback-history loading for the dashboard, derived historical metrics, and the canonical recommendation payload validation helpers used by the app and tests.
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

Canonical validation lives in `engines/app_support.py`:

- `validate_recommendation_payload(payload) -> tuple[bool, list[str]]`
- `assert_recommendation_payload(payload) -> None`
- `get_recommendation_contract_fields() -> dict`
- `save_feedback_csv(resultado, status, arquivo=...) -> None`
- `carregar_historico_feedback(path=...) -> pandas.DataFrame`
- `calcular_metricas_historico_feedback(df) -> dict`

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
Current canonical metric keys are:

- `p_clima`
- `p_data`
- `p_hora`
- `p_evento`
- `p_ml`

Metric values are expected to be numeric and within the inclusive range `[0, 1]`.

### `resultado["alternativas"]`

- `alternativas` must be a list.
- Each alternative must contain at least:
  - `produto`
  - `score`
- In practice the engine currently returns alternative entries with the same rich structure as the main recommendation, but the UI only depends on `produto` and `score`.

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

`carregar_historico_feedback()` uses this same schema. If `data/feedback.csv` does not exist or is malformed, it currently returns an empty DataFrame with the canonical feedback columns instead of crashing the UI.

`calcular_metricas_historico_feedback()` derives dashboard metrics from this history. It treats success as `status == "vendeu_tudo"` and returns safe zero/empty defaults for empty history inputs.

### Product catalog contract

`data/produtos.json` is loaded by `RecommendationEngine` at initialization time and must be a non-empty JSON object keyed by product name.

Each product entry currently requires:

- `categoria`
- `preco_venda`
- `custo`
- `margem`
- `climas_favoraveis`
- `climas_desfavoraveis`
- `dias_favoraveis`
- `horarios_pico`
- `eventos_associados`

Validation rules currently enforced before scoring:

- `categoria` must be a non-empty string
- `preco_venda`, `custo`, and `margem` must be numeric
- `climas_favoraveis`, `climas_desfavoraveis`, `dias_favoraveis`, `horarios_pico`, and `eventos_associados` must be lists
- `horarios_pico` must not be empty because `_score_hora()` depends on at least one reference hour
- `nota_mercado` is optional and only affects explanations

## Important Runtime Behavior

- Weather service (`engines/weather_service.py`) uses Open-Meteo, caches the latest result in memory for 10 minutes, and falls back to `_previsao_simulada()` with `simulado=True` when the API fails.
- Event discovery (`engines/event_service.py`) reads a 6-hour disk cache from `data/eventos_cache.json`; if live providers fail or return nothing, it falls back to `_eventos_fallback()` with local BH patterns such as Feira Hippie, Savassi/blocos, Expominas, and Praça Sete flow.
- NLP model loading is optional at runtime from a stability perspective. If the Hugging Face zero-shot pipeline fails to download, load, or infer, `classificar_evento()` must return a safe neutral result like `{"tipo": "evento", "confianca": 0.0}` instead of crashing the app.
- The XGBoost model may be missing or fail during prediction. That must not crash the UI; `_score_ml()` should continue with the neutral fallback score `0.5`.
- Product catalog validation now happens during `RecommendationEngine` initialization. Empty or malformed catalogs raise `ProductCatalogError` with a product/field-specific message before scoring begins.
- External APIs are unreliable during local development and CI-like environments. Future work should assume offline or DNS-restricted execution is common.
- `app.py` must validate the recommendation payload before storing or rendering it. If invalid, it should show a user-friendly error plus development-facing field diagnostics instead of crashing with a nested-key lookup error.
- The feedback-history dashboard reads `data/feedback.csv` through `carregar_historico_feedback()` and derives aggregate insights through `calcular_metricas_historico_feedback()`. If there is no feedback file yet, or if the CSV is malformed, the dashboard shows an empty-state message rather than breaking the app.

## Current Explanation Behavior

- `RecommendationEngine._gerar_explicacoes()` always starts with a "fator decisivo" line derived from the highest metric among `p_clima`, `p_data`, `p_hora`, `p_evento`, and `p_ml`.
- If the decisive factor is climate, the explanation includes `clima["descricao"]`, so scenario text such as `chuva moderada` or `céu limpo` can surface directly.
- If `clima["simulado"]` is truthy, the engine currently adds an explicit `Dados climáticos SIMULADOS` warning to `explicacoes`.
- If there are real events (that is, event entries whose `fonte` is not `padrao_bh`), the engine appends a compact `Eventos: ...` line listing up to three event names.
- If the selected product has `nota_mercado`, that note is appended as a final explanation. This is where phrases like `dias chuvosos`, `eventos esportivos`, or `dias quentes` currently come from.
- Explanations currently do not provide a full natural-language decomposition of all score components; they surface the top factor plus optional weather/event/product-note context.

## Testing Strategy

- Unit tests must avoid live weather/event APIs, Hugging Face downloads, and network access.
- `RecommendationEngine` should be tested with injected fake providers rather than with global monkeypatching whenever practical.
- Deterministic recommendation tests should freeze time with `now_provider`, inject fixed event lists with `event_provider`, and use either `model=None` or a fake model object.
- Fallback behavior has explicit regression coverage for malformed event cache reads, NLP model failures, and ML prediction failures.
- Recommendation tests now also cover explanation semantics for rainy demand, hot sports-event demand, simulated weather warnings, unknown NLP categories on real events, extreme ML predictions, and score-boundary checks.
- Product catalog tests now cover empty catalogs, missing required fields, invalid numeric/list fields, and a valid minimal catalog path.
- Feedback-history tests now cover missing files, valid CSV loading, numeric conversion, and malformed CSV fallback behavior.
- Feedback-history metrics tests now cover empty defaults, total feedback count, product frequency, total estimated profit, overall success rate, success rate by product, and average estimated profit by product.
- Ranking tests should assert stable product outcomes or top-tier membership in realistic scenarios, but should avoid brittle exact-score assertions unless the inputs are fully controlled.
- Standard final local validation command:
  - `make check`
- Supporting commands:
  - `python -m py_compile app.py train_model.py engines/*.py export_contexto.py`
  - `python -m pytest`
  - `python export_contexto.py --check`
  - `python export_contexto.py`
- CI workflow:
  - `.github/workflows/check.yml`
  - runs `make check` on `push` and `pull_request` using Python 3.11
- Expected passing test count after the latest stabilization/docs work: `36 passed`

## Development Rules for Future Codex Tasks

- Do not commit `.env`, API keys, tokens, or other secrets.
- Do not introduce paid services or external infrastructure without explicit approval.
- Keep changes small, local, and easy to review.
- Preserve Portuguese UX copy unless the task explicitly asks for language changes.
- Prefer robust fallbacks over hard crashes.
- Keep tests and validation offline-safe: no real external API calls, no required secrets, and no Hugging Face model downloads during test execution.
- When changing architecture, core behavior, or data contracts, update this file in the same task.
- If the recommendation payload changes, update `engines/app_support.py`, the related tests, and this memory file together in the same change.
- If context export behavior changes, review `export_contexto.py`, its tests, and regenerate `context/contexto_ia.txt` intentionally.
- Treat `context/contexto_ia.txt` as a committed generated artifact: edit the script or source docs, then regenerate; do not hand-edit the snapshot.
- After changing architecture, docs, contracts, or core behavior, run `python export_contexto.py` and then `make check` before finishing the task.
- `make check` should pass locally before pushing, because CI runs the same command remotely.

## Current Known Risks / TODOs

- NLP startup latency is still high because `facebook/bart-large-mnli` may need network access or a large local cache.
- Event API integrations still need real-world validation against actual PBH, Sympla, and Eventbrite responses.
- The UI still depends on a nested recommendation schema staying stable.
- Explanation quality is still template-driven: it highlights the strongest factor and some contextual hints, but it does not yet justify every relevant factor in richer Portuguese prose.
- Catalog validation is intentionally practical rather than exhaustive; for example, it checks field presence/types but not deeper semantic ranges for every list item.
- The dashboard metrics are feedback-based and use `lucro_estimado`; they are useful operational indicators, not confirmed accounting or realized-sales truth.
- The automated test layer should still expand around malformed product attribute values and more service fallback cases.
- The generated AI snapshot can become stale if not regenerated after architecture/documentation changes.
