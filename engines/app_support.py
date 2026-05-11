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

RECOMMENDATION_REQUIRED_KEYS = {
    "produto",
    "score",
    "lucro_estimado",
    "vendas_estimadas",
    "margem",
    "custo",
    "preco_venda",
    "categoria",
    "metricas",
}

RESULT_REQUIRED_KEYS = {
    "recomendacao",
    "alternativas",
    "explicacoes",
    "clima",
    "eventos",
    "hora_consulta",
    "data_consulta",
}

CLIMATE_REQUIRED_KEYS = {
    "condicao",
    "descricao",
    "temperatura",
    "umidade",
    "chuva_mm",
}


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


def is_valid_recommendation_result(resultado):
    if not isinstance(resultado, dict):
        return False
    if not RESULT_REQUIRED_KEYS.issubset(resultado.keys()):
        return False

    recomendacao = resultado.get("recomendacao")
    if not isinstance(recomendacao, dict):
        return False
    if not RECOMMENDATION_REQUIRED_KEYS.issubset(recomendacao.keys()):
        return False

    clima = resultado.get("clima")
    if not isinstance(clima, dict):
        return False
    if not CLIMATE_REQUIRED_KEYS.issubset(clima.keys()):
        return False

    metricas = recomendacao.get("metricas")
    if not isinstance(metricas, dict):
        return False

    return True
