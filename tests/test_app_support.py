import csv

from engines.app_support import (
    FEEDBACK_COLUMNS,
    assert_recommendation_payload,
    get_recommendation_contract_fields,
    is_valid_recommendation_result,
    save_feedback_csv,
    validate_recommendation_payload,
)


def _sample_result():
    return {
        "recomendacao": {
            "produto": "agua mineral gelada 500ml",
            "score": 87.5,
            "lucro_estimado": 140.0,
            "vendas_estimadas": 50,
            "margem": 70.0,
            "custo": 1.2,
            "preco_venda": 4.0,
            "categoria": "bebida",
            "metricas": {
                "p_clima": 0.9,
                "p_data": 0.7,
                "p_hora": 1.0,
                "p_evento": 0.4,
                "p_ml": 0.8,
            },
        },
        "alternativas": [],
        "explicacoes": ["Clima quente favorece bebidas."],
        "clima": {
            "condicao": "limpo",
            "descricao": "céu limpo",
            "temperatura": 29.0,
            "umidade": 58,
            "chuva_mm": 0.0,
        },
        "eventos": [],
        "hora_consulta": "14:00",
        "data_consulta": "11/05/2026",
    }


def test_save_feedback_csv_creates_file_with_expected_columns(tmp_path):
    arquivo = tmp_path / "data" / "feedback.csv"

    save_feedback_csv(_sample_result(), "vendeu_tudo", arquivo=arquivo)

    assert arquivo.exists()

    with arquivo.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    assert reader.fieldnames == FEEDBACK_COLUMNS
    assert len(rows) == 1
    assert rows[0]["produto"] == "agua mineral gelada 500ml"
    assert rows[0]["status"] == "vendeu_tudo"


def test_is_valid_recommendation_result_accepts_expected_schema():
    assert is_valid_recommendation_result(_sample_result()) is True


def test_is_valid_recommendation_result_rejects_missing_nested_fields():
    resultado = _sample_result()
    del resultado["recomendacao"]["metricas"]

    assert is_valid_recommendation_result(resultado) is False


def test_validate_recommendation_payload_returns_no_errors_for_valid_payload():
    valido, erros = validate_recommendation_payload(_sample_result())

    assert valido is True
    assert erros == []


def test_validate_recommendation_payload_reports_missing_top_level_field():
    resultado = _sample_result()
    del resultado["clima"]

    valido, erros = validate_recommendation_payload(resultado)

    assert valido is False
    assert "missing top-level field: clima" in erros


def test_validate_recommendation_payload_reports_missing_recommendation_field():
    resultado = _sample_result()
    del resultado["recomendacao"]["produto"]

    valido, erros = validate_recommendation_payload(resultado)

    assert valido is False
    assert "missing recommendation field: recomendacao.produto" in erros


def test_validate_recommendation_payload_rejects_invalid_metric_value():
    resultado = _sample_result()
    resultado["recomendacao"]["metricas"]["p_clima"] = 1.2

    valido, erros = validate_recommendation_payload(resultado)

    assert valido is False
    assert "metric value out of range [0, 1]: recomendacao.metricas.p_clima=1.2" in erros


def test_assert_recommendation_payload_raises_useful_error():
    resultado = _sample_result()
    del resultado["alternativas"]

    try:
        assert_recommendation_payload(resultado)
    except ValueError as exc:
        assert "missing top-level field: alternativas" in str(exc)
    else:
        raise AssertionError("assert_recommendation_payload should have raised ValueError")


def test_get_recommendation_contract_fields_exposes_canonical_lists():
    contrato = get_recommendation_contract_fields()

    assert contrato["resultado"] == [
        "recomendacao",
        "alternativas",
        "explicacoes",
        "clima",
        "eventos",
        "hora_consulta",
        "data_consulta",
    ]
    assert contrato["metricas"] == ["p_clima", "p_data", "p_hora", "p_evento", "p_ml"]
