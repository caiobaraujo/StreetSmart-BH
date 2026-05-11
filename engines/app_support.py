import csv
import datetime
from pathlib import Path

FEEDBACK_COLUMNS = [
    "timestamp",
    "produto",
    "score",
    "status",
    "temperatura",
    "chuva_mm",
    "umidade",
    "condicao",
    "hora",
    "data",
    "vendas_estimadas",
    "lucro_estimado",
]

RESULT_REQUIRED_KEYS = [
    "recomendacao",
    "alternativas",
    "explicacoes",
    "clima",
    "eventos",
    "hora_consulta",
    "data_consulta",
]

RECOMMENDATION_REQUIRED_KEYS = [
    "produto",
    "score",
    "lucro_estimado",
    "vendas_estimadas",
    "margem",
    "custo",
    "preco_venda",
    "categoria",
    "metricas",
]

ALTERNATIVE_REQUIRED_KEYS = [
    "produto",
    "score",
]

CLIMATE_REQUIRED_KEYS = [
    "condicao",
    "descricao",
    "temperatura",
    "umidade",
    "chuva_mm",
]

METRIC_REQUIRED_KEYS = [
    "p_clima",
    "p_data",
    "p_hora",
    "p_evento",
    "p_ml",
]


def build_feedback_row(resultado, status):
    rec = resultado["recomendacao"]
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "produto": rec["produto"],
        "score": rec["score"],
        "status": status,
        "temperatura": resultado["clima"]["temperatura"],
        "chuva_mm": resultado["clima"]["chuva_mm"],
        "umidade": resultado["clima"]["umidade"],
        "condicao": resultado["clima"]["condicao"],
        "hora": resultado["hora_consulta"],
        "data": resultado["data_consulta"],
        "vendas_estimadas": rec["vendas_estimadas"],
        "lucro_estimado": rec["lucro_estimado"],
    }


def save_feedback_csv(resultado, status, arquivo=Path("data/feedback.csv")):
    arquivo = Path(arquivo)
    arquivo.parent.mkdir(parents=True, exist_ok=True)

    novo = build_feedback_row(resultado, status)
    escrever_cabecalho = not arquivo.exists() or arquivo.stat().st_size == 0
    with arquivo.open("a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FEEDBACK_COLUMNS)
        if escrever_cabecalho:
            writer.writeheader()
        writer.writerow(novo)


def get_recommendation_contract_fields():
    return {
        "resultado": list(RESULT_REQUIRED_KEYS),
        "recomendacao": list(RECOMMENDATION_REQUIRED_KEYS),
        "alternativa": list(ALTERNATIVE_REQUIRED_KEYS),
        "clima": list(CLIMATE_REQUIRED_KEYS),
        "metricas": list(METRIC_REQUIRED_KEYS),
        "feedback_csv": list(FEEDBACK_COLUMNS),
    }


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_recommendation_payload(payload):
    errors = []

    if not isinstance(payload, dict):
        return False, ["payload must be a dict"]

    for key in RESULT_REQUIRED_KEYS:
        if key not in payload:
            errors.append(f"missing top-level field: {key}")

    recomendacao = payload.get("recomendacao")
    if recomendacao is None:
        return False, errors
    if not isinstance(recomendacao, dict):
        errors.append("field 'recomendacao' must be a dict")
    else:
        for key in RECOMMENDATION_REQUIRED_KEYS:
            if key not in recomendacao:
                errors.append(f"missing recommendation field: recomendacao.{key}")

        metricas = recomendacao.get("metricas")
        if not isinstance(metricas, dict):
            errors.append("field 'recomendacao.metricas' must be a dict")
        else:
            if not metricas:
                errors.append("field 'recomendacao.metricas' must not be empty")
            for key in METRIC_REQUIRED_KEYS:
                if key not in metricas:
                    errors.append(f"missing metric field: recomendacao.metricas.{key}")
            for key, value in metricas.items():
                if not _is_number(value):
                    errors.append(f"metric value must be numeric: recomendacao.metricas.{key}")
                    continue
                if value < 0 or value > 1:
                    errors.append(f"metric value out of range [0, 1]: recomendacao.metricas.{key}={value}")

    clima = payload.get("clima")
    if clima is None:
        return False, errors
    if not isinstance(clima, dict):
        errors.append("field 'clima' must be a dict")
    else:
        for key in CLIMATE_REQUIRED_KEYS:
            if key not in clima:
                errors.append(f"missing climate field: clima.{key}")

    alternativas = payload.get("alternativas")
    if alternativas is not None:
        if not isinstance(alternativas, list):
            errors.append("field 'alternativas' must be a list")
        else:
            for index, alternativa in enumerate(alternativas):
                if not isinstance(alternativa, dict):
                    errors.append(f"alternative must be a dict: alternativas[{index}]")
                    continue
                for key in ALTERNATIVE_REQUIRED_KEYS:
                    if key not in alternativa:
                        errors.append(f"missing alternative field: alternativas[{index}].{key}")

    explicacoes = payload.get("explicacoes")
    if explicacoes is not None:
        if not isinstance(explicacoes, list):
            errors.append("field 'explicacoes' must be a list")
        elif any(not isinstance(item, str) for item in explicacoes):
            errors.append("field 'explicacoes' must contain only strings")

    for key in ("hora_consulta", "data_consulta"):
        if key in payload and not isinstance(payload[key], str):
            errors.append(f"field '{key}' must be a string")

    return len(errors) == 0, errors


def assert_recommendation_payload(payload):
    valid, errors = validate_recommendation_payload(payload)
    if not valid:
        raise ValueError("Invalid recommendation payload: " + "; ".join(errors))


def is_valid_recommendation_result(resultado):
    valid, _errors = validate_recommendation_payload(resultado)
    return valid
