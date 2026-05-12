import datetime
import json

import pytest

from engines.app_support import assert_recommendation_payload, validate_recommendation_payload
from engines.recommendation_engine import ProductCatalogError, RecommendationEngine


class ExplodingModel:
    def predict(self, _matrix):
        raise RuntimeError("simulated prediction failure")


class HighConfidenceModel:
    def predict(self, _matrix):
        return [500.0]


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


def _joined_explanations(resultado):
    return " ".join(resultado["explicacoes"]).lower()


def _write_catalog(tmp_path, data, filename="catalogo.json"):
    catalog_path = tmp_path / filename
    catalog_path.write_text(json.dumps(data), encoding="utf-8")
    return catalog_path


def _valid_minimal_product():
    return {
        "categoria": "bebida",
        "preco_venda": 5.0,
        "custo": 2.0,
        "margem": 60.0,
        "climas_favoraveis": ["limpo"],
        "climas_desfavoraveis": ["chuva"],
        "dias_favoraveis": [0, 1, 2, 3, 4, 5, 6],
        "horarios_pico": [10, 11, 12],
        "eventos_associados": ["evento"],
    }


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

    assert_recommendation_payload(resultado)
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
    assert resultado["explicacoes"]
    assert all(isinstance(explicacao, str) and explicacao.strip() for explicacao in resultado["explicacoes"])
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
    assert_recommendation_payload(resultado)
    produtos_top3 = [resultado["recomendacao"]["produto"], *[alt["produto"] for alt in resultado["alternativas"]]]
    explicacoes = _joined_explanations(resultado)

    assert resultado["recomendacao"]["produto"] in {
        "guarda-chuva compacto",
        "capa de chuva descartavel",
    }
    assert any(
        produto in {"guarda-chuva compacto", "capa de chuva descartavel"}
        for produto in produtos_top3
    )
    assert any(palavra in explicacoes for palavra in ("chuva", "clim", "chuvoso", "guarda-chuva"))
    assert "eventos:" not in explicacoes


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
    assert_recommendation_payload(resultado)
    produtos_top3 = [resultado["recomendacao"]["produto"], *[alt["produto"] for alt in resultado["alternativas"]]]
    explicacoes = _joined_explanations(resultado)

    assert resultado["recomendacao"]["produto"] == "agua mineral gelada 500ml"
    assert "agua mineral gelada 500ml" in produtos_top3
    assert any(palavra in explicacoes for palavra in ("evento", "corrida", "quente", "esportiv"))


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

    valido, erros = validate_recommendation_payload(resultado)
    assert valido is True
    assert erros == []
    assert resultado["recomendacao"]["produto"] in {
        "guarda-chuva compacto",
        "capa de chuva descartavel",
    }


def test_calcular_recomendacao_surfaces_simulated_weather_in_explanations():
    engine = _engine_for_test(
        now_dt=datetime.datetime(2026, 5, 11, 17, 0),
        events=[],
        model=None,
        weather={
            "condicao": "chuva",
            "descricao": "chuva moderada (simulada)",
            "temperatura": 21.0,
            "umidade": 88,
            "chuva_mm": 8.0,
            "simulado": True,
        },
    )

    resultado = engine.calcular_recomendacao()

    assert_recommendation_payload(resultado)
    assert any("simulad" in explicacao.lower() for explicacao in resultado["explicacoes"])


def test_calcular_recomendacao_handles_unknown_nlp_category_with_real_event():
    engine = _engine_for_test(
        now_dt=datetime.datetime(2026, 5, 13, 15, 0),
        events=[
            {
                "nome": "Encontro Urbano na Savassi",
                "tipo": "evento",
                "fonte": "Sympla",
                "data": "2026-05-13",
            }
        ],
        model=None,
        weather={
            "condicao": "limpo",
            "descricao": "céu limpo",
            "temperatura": 30.0,
            "umidade": 45,
            "chuva_mm": 0.0,
        },
        nlp_result={"tipo": "categoria_desconhecida", "confianca": 0.12},
    )

    resultado = engine.calcular_recomendacao()

    assert_recommendation_payload(resultado)
    assert resultado["eventos"][0]["tipo_nlp"] == "categoria_desconhecida"
    assert any("eventos:" in explicacao.lower() for explicacao in resultado["explicacoes"])


def test_calcular_recomendacao_clamps_extreme_ml_prediction_and_scores():
    engine = _engine_for_test(
        now_dt=datetime.datetime(2026, 5, 13, 14, 0),
        events=[],
        model=HighConfidenceModel(),
        weather={
            "condicao": "limpo",
            "descricao": "céu limpo",
            "temperatura": 32.0,
            "umidade": 42,
            "chuva_mm": 0.0,
        },
    )

    resultado = engine.calcular_recomendacao()

    assert_recommendation_payload(resultado)
    assert resultado["recomendacao"]["metricas"]["p_ml"] == 1.0

    for item in [resultado["recomendacao"], *resultado["alternativas"]]:
        assert 0.0 <= item["score"] <= 100.0


def test_calcular_recomendacao_empty_catalog_raises_product_catalog_error(tmp_path):
    catalog_path = _write_catalog(tmp_path, {}, "produtos_vazios.json")

    with pytest.raises(ProductCatalogError, match="catálogo de produtos está vazio"):
        RecommendationEngine(
            produtos_path=str(catalog_path),
            weather_provider=lambda: {
                "condicao": "limpo",
                "descricao": "céu limpo",
                "temperatura": 25.0,
                "umidade": 50,
                "chuva_mm": 0.0,
            },
            event_provider=lambda: [],
            nlp_classifier=lambda _nome: {"tipo": "evento", "confianca": 0.0},
            now_provider=lambda: datetime.datetime(2026, 5, 13, 12, 0),
            model=None,
        )


def test_recommendation_engine_raises_product_catalog_error_for_missing_field(tmp_path):
    produto = _valid_minimal_product()
    del produto["categoria"]
    catalog_path = _write_catalog(tmp_path, {"produto teste": produto}, "sem_categoria.json")

    with pytest.raises(ProductCatalogError, match="campo obrigatório ausente: categoria"):
        RecommendationEngine(produtos_path=str(catalog_path), model=None)


def test_recommendation_engine_raises_product_catalog_error_for_invalid_numeric_field(tmp_path):
    produto = _valid_minimal_product()
    produto["margem"] = "alta"
    catalog_path = _write_catalog(tmp_path, {"produto teste": produto}, "margem_invalida.json")

    with pytest.raises(ProductCatalogError, match="campo 'margem' deve ser numérico"):
        RecommendationEngine(produtos_path=str(catalog_path), model=None)


def test_recommendation_engine_raises_product_catalog_error_for_invalid_list_field(tmp_path):
    produto = _valid_minimal_product()
    produto["eventos_associados"] = "evento"
    catalog_path = _write_catalog(tmp_path, {"produto teste": produto}, "eventos_invalidos.json")

    with pytest.raises(ProductCatalogError, match="campo 'eventos_associados' deve ser uma lista"):
        RecommendationEngine(produtos_path=str(catalog_path), model=None)


def test_recommendation_engine_accepts_valid_minimal_catalog(tmp_path):
    catalog_path = _write_catalog(
        tmp_path,
        {"produto teste": _valid_minimal_product()},
        "catalogo_valido.json",
    )

    engine = RecommendationEngine(
        produtos_path=str(catalog_path),
        weather_provider=lambda: {
            "condicao": "limpo",
            "descricao": "céu limpo",
            "temperatura": 25.0,
            "umidade": 50,
            "chuva_mm": 0.0,
        },
        event_provider=lambda: [],
        nlp_classifier=lambda _nome: {"tipo": "evento", "confianca": 0.0},
        now_provider=lambda: datetime.datetime(2026, 5, 13, 12, 0),
        model=None,
    )

    resultado = engine.calcular_recomendacao()

    assert_recommendation_payload(resultado)
    assert resultado["recomendacao"]["produto"] == "produto teste"
