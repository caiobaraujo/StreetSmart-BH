import csv

from engines.app_support import (
    FEEDBACK_COLUMNS,
    is_valid_recommendation_result,
    save_feedback_csv,
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
