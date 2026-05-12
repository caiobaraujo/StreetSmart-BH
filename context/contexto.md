# StreetSmart BH — Histórico do Projeto

> Fonte canônica para agentes de IA/Codex: `context/AI_PROJECT_MEMORY.md`
>
> Este arquivo permanece como histórico humano em português. Se houver conflito entre este documento e `AI_PROJECT_MEMORY.md`, considere `AI_PROJECT_MEMORY.md` como a referência técnica correta.

## Estado Atual

- O app continua sendo um frontend Streamlit em `app.py`.
- O motor central continua em `engines/recommendation_engine.py`.
- A validação do payload de recomendação agora é centralizada em `engines/app_support.py`.
- O projeto possui testes automatizados com `pytest`, incluindo contratos de payload, fallbacks e cenários determinísticos do motor.
- O arquivo `context/contexto_ia.txt` é um snapshot gerado e versionado por `export_contexto.py`; ele deve ser regenerado quando a memória técnica ou a arquitetura mudarem.

## Changelog Recente

### Endurecimento de runtime

- `app.py` passou a validar o payload retornado pelo motor antes de renderizar a UI.
- Salvamento de feedback foi tornado mais robusto com helper dedicado e escrita estruturada em CSV.
- O classificador NLP passou a degradar com segurança quando o modelo não carrega.
- Leitura de cache de eventos malformado deixou de quebrar a inicialização.
- Falhas de score de ML deixaram de ser silenciosas.

### Contratos e manutenção

- `engines/app_support.py` centraliza o contrato do payload de recomendação.
- `RecommendationEngine` recebeu pequenos pontos de injeção de dependência para testes determinísticos:
  - `weather_provider`
  - `event_provider`
  - `nlp_classifier`
  - `now_provider`
  - `model`
- `context/AI_PROJECT_MEMORY.md` passou a ser a memória técnica canônica para continuidade com IA.

### Testes automatizados

- Testes de fallback para NLP e cache de eventos.
- Testes de persistência de feedback.
- Testes determinísticos de `RecommendationEngine.calcular_recomendacao()`.
- Testes do validador centralizado do payload de recomendação.
- Testes leves do exportador de contexto para garantir prioridade da memória canônica e exclusão de segredos/artefatos ruidosos.

## Notas Históricas

- O projeto já teve descrições antigas mencionando OpenWeather como fonte de clima; o estado atual usa Open-Meteo no serviço de clima.
- O snapshot `context/contexto_ia.txt` não deve ser editado manualmente; a fonte correta é `AI_PROJECT_MEMORY.md` mais os arquivos reais do projeto.
- O exportador agora exclui artefatos gerados e ruidosos, como cache de eventos e dados sintéticos de treino, para reduzir contexto enganoso em handoffs de IA.
- Informações operacionais, contratos de dados e estratégia de testes devem ser mantidas em `AI_PROJECT_MEMORY.md`, não aqui.

## Próximas Prioridades Técnicas

- Expandir testes em torno da geração de explicações e de casos de borda do payload.
- Validar melhor integrações reais de eventos (PBH, Sympla, Eventbrite).
- Considerar uma estratégia offline mais rápida para NLP, reduzindo latência de startup.
