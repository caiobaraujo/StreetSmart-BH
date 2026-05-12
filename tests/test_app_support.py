import csv

import pandas as pd

from engines.app_support import (
    FEEDBACK_COLUMNS,
    assert_recommendation_payload,
    calcular_metricas_historico_feedback,
    carregar_historico_feedback,
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


def test_carregar_historico_feedback_returns_empty_dataframe_when_file_is_missing(tmp_path):
    arquivo = tmp_path / "data" / "feedback.csv"

    historico = carregar_historico_feedback(arquivo)

    assert list(historico.columns) == FEEDBACK_COLUMNS
    assert historico.empty is True


def test_carregar_historico_feedback_loads_valid_csv_and_converts_numeric_columns(tmp_path):
    arquivo = tmp_path / "data" / "feedback.csv"
    save_feedback_csv(_sample_result(), "vendeu_tudo", arquivo=arquivo)

    historico = carregar_historico_feedback(arquivo)

    assert len(historico) == 1
    assert historico.loc[0, "produto"] == "agua mineral gelada 500ml"
    assert pd.api.types.is_datetime64_any_dtype(historico["timestamp"]) is True
    assert pd.api.types.is_numeric_dtype(historico["score"]) is True
    assert pd.api.types.is_numeric_dtype(historico["lucro_estimado"]) is True


def test_carregar_historico_feedback_handles_malformed_csv_safely(tmp_path):
    arquivo = tmp_path / "data" / "feedback.csv"
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text("coluna_errada\nvalor\n", encoding="utf-8")

    historico = carregar_historico_feedback(arquivo)

    assert list(historico.columns) == FEEDBACK_COLUMNS
    assert historico.empty is True


def test_calcular_metricas_historico_feedback_returns_safe_defaults_for_empty_dataframe():
    metricas = calcular_metricas_historico_feedback(pd.DataFrame(columns=FEEDBACK_COLUMNS))

    assert metricas["total_feedbacks"] == 0
    assert metricas["produto_mais_frequente"] == "-"
    assert metricas["lucro_estimado_total"] == 0.0
    assert metricas["taxa_sucesso"] == 0.0
    assert metricas["contagem_status"].empty is True
    assert metricas["produtos_mais_frequentes"].empty is True
    assert metricas["lucro_medio_por_produto"].empty is True
    assert metricas["taxa_sucesso_por_produto"].empty is True


def test_calcular_metricas_historico_feedback_calcula_totais_e_produto_mais_frequente():
    df = pd.DataFrame(
        [
            {"produto": "agua", "status": "vendeu_tudo", "lucro_estimado": 100.0},
            {"produto": "agua", "status": "nao_vendeu", "lucro_estimado": 20.0},
            {"produto": "cafe", "status": "vendeu_tudo", "lucro_estimado": 60.0},
        ]
    )

    metricas = calcular_metricas_historico_feedback(df)

    assert metricas["total_feedbacks"] == 3
    assert metricas["produto_mais_frequente"] == "agua"
    assert metricas["lucro_estimado_total"] == 180.0


def test_calcular_metricas_historico_feedback_calcula_taxa_sucesso_corretamente():
    df = pd.DataFrame(
        [
            {"produto": "agua", "status": "vendeu_tudo", "lucro_estimado": 100.0},
            {"produto": "agua", "status": "nao_vendeu", "lucro_estimado": 20.0},
            {"produto": "cafe", "status": "vendeu_tudo", "lucro_estimado": 60.0},
            {"produto": "cafe", "status": "vendeu_parcial", "lucro_estimado": 40.0},
        ]
    )

    metricas = calcular_metricas_historico_feedback(df)

    assert metricas["taxa_sucesso"] == 0.5


def test_calcular_metricas_historico_feedback_calcula_taxa_sucesso_por_produto():
    df = pd.DataFrame(
        [
            {"produto": "agua", "status": "vendeu_tudo", "lucro_estimado": 100.0},
            {"produto": "agua", "status": "nao_vendeu", "lucro_estimado": 20.0},
            {"produto": "cafe", "status": "vendeu_tudo", "lucro_estimado": 60.0},
            {"produto": "cafe", "status": "vendeu_tudo", "lucro_estimado": 80.0},
        ]
    )

    metricas = calcular_metricas_historico_feedback(df)

    assert metricas["taxa_sucesso_por_produto"]["agua"] == 0.5
    assert metricas["taxa_sucesso_por_produto"]["cafe"] == 1.0


def test_calcular_metricas_historico_feedback_calcula_lucro_medio_por_produto():
    df = pd.DataFrame(
        [
            {"produto": "agua", "status": "vendeu_tudo", "lucro_estimado": 100.0},
            {"produto": "agua", "status": "nao_vendeu", "lucro_estimado": 20.0},
            {"produto": "cafe", "status": "vendeu_tudo", "lucro_estimado": 60.0},
            {"produto": "cafe", "status": "vendeu_tudo", "lucro_estimado": 80.0},
        ]
    )

    metricas = calcular_metricas_historico_feedback(df)

    assert metricas["lucro_medio_por_produto"]["agua"] == 60.0
    assert metricas["lucro_medio_por_produto"]["cafe"] == 70.0


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
