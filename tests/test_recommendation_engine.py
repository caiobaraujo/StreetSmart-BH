import datetime

from engines.app_support import is_valid_recommendation_result
from engines.recommendation_engine import RecommendationEngine


class ExplodingModel:
    def predict(self, _matrix):
        raise RuntimeError("simulated prediction failure")


def _engine_for_test(*, now_dt, events=None, model=None, weather=None, nlp_result=None):
    if events is None:
        events = []
    if weather is None:
        weather = {
            "condicao": "nublado",
            "descricao": "nublado",
            "temperatura": 24.0,
            "umidade": 60,
            "chuva_mm": 0.0,
        }
    if nlp_result is None:
        nlp_result = {"tipo": "evento", "confianca": 0.0}

    return RecommendationEngine(
        weather_provider=lambda: weather,
        event_provider=lambda: [dict(evento) for evento in events],
        nlp_classifier=lambda _nome: dict(nlp_result),
        now_provider=lambda: now_dt,
        model=model,
    )


def test_calcular_recomendacao_returns_expected_payload_structure():
    engine = _engine_for_test(
        now_dt=datetime.datetime(2026, 5, 13, 14, 0),
        events=[
            {
                "nome": "Corrida no Centro",
                "tipo": "evento",
                "tipo_nlp": "evento esportivo",
                "fonte": "Sympla",
                "data": "2026-05-13",
            }
        ],
        model=None,
        weather={
            "condicao": "limpo",
            "descricao": "céu limpo",
            "temperatura": 31.0,
            "umidade": 48,
            "chuva_mm": 0.0,
        },
    )

    resultado = engine.calcular_recomendacao()

    assert is_valid_recommendation_result(resultado) is True
    assert set(resultado.keys()) == {
        "recomendacao",
        "alternativas",
        "explicacoes",
        "clima",
        "eventos",
        "hora_consulta",
        "data_consulta",
    }

    recomendacao = resultado["recomendacao"]
    assert {
        "produto",
        "score",
        "lucro_estimado",
        "margem",
        "vendas_estimadas",
        "preco_venda",
        "custo",
        "metricas",
    }.issubset(recomendacao.keys())
    assert isinstance(resultado["alternativas"], list)
    assert isinstance(resultado["explicacoes"], list)
    assert resultado["hora_consulta"] == "14:00"
    assert resultado["data_consulta"] == "13/05/2026"


def test_calcular_recomendacao_prefers_rain_products_in_rainy_scenario():
    engine = _engine_for_test(
        now_dt=datetime.datetime(2026, 5, 11, 17, 0),
        events=[],
        model=None,
        weather={
            "condicao": "chuva",
            "descricao": "chuva moderada",
            "temperatura": 21.0,
            "umidade": 88,
            "chuva_mm": 8.0,
        },
    )

    resultado = engine.calcular_recomendacao()
    produtos_top3 = [resultado["recomendacao"]["produto"], *[alt["produto"] for alt in resultado["alternativas"]]]

    assert resultado["recomendacao"]["produto"] in {
        "guarda-chuva compacto",
        "capa de chuva descartavel",
    }
    assert any(
        produto in {"guarda-chuva compacto", "capa de chuva descartavel"}
        for produto in produtos_top3
    )


def test_calcular_recomendacao_prefers_cold_drink_for_hot_sports_scenario():
    engine = _engine_for_test(
        now_dt=datetime.datetime(2026, 5, 13, 14, 0),
        events=[
            {
                "nome": "Corrida de Rua BH",
                "tipo": "evento",
                "tipo_nlp": "evento esportivo",
                "fonte": "Sympla",
                "data": "2026-05-13",
            }
        ],
        model=None,
        weather={
            "condicao": "limpo",
            "descricao": "céu limpo",
            "temperatura": 32.0,
            "umidade": 42,
            "chuva_mm": 0.0,
        },
    )

    resultado = engine.calcular_recomendacao()
    produtos_top3 = [resultado["recomendacao"]["produto"], *[alt["produto"] for alt in resultado["alternativas"]]]

    assert resultado["recomendacao"]["produto"] == "agua mineral gelada 500ml"
    assert "agua mineral gelada 500ml" in produtos_top3


def test_calcular_recomendacao_returns_payload_when_ml_prediction_fails():
    engine = _engine_for_test(
        now_dt=datetime.datetime(2026, 5, 11, 17, 0),
        events=[],
        model=ExplodingModel(),
        weather={
            "condicao": "chuva",
            "descricao": "chuva moderada",
            "temperatura": 21.0,
            "umidade": 88,
            "chuva_mm": 8.0,
        },
    )

    resultado = engine.calcular_recomendacao()

    assert is_valid_recommendation_result(resultado) is True
    assert resultado["recomendacao"]["produto"] in {
        "guarda-chuva compacto",
        "capa de chuva descartavel",
    }
