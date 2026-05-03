"""
Serviço de clima - integração com Open-Meteo API (100% gratuito e sem chave)
Documentação: https://open-meteo.com/en/docs
"""
import requests
from datetime import datetime, timezone

LAT_BH = -19.9167
LON_BH = -43.9345

_cache = {"timestamp": None, "data": None}


def obter_previsao_bh():
    """
    Retorna dict com dados climáticos de BH usando Open-Meteo.
    Em caso de erro, retorna fallback simulado.
    """
    agora = datetime.now(timezone.utc)
    if _cache["timestamp"] and (agora - _cache["timestamp"]).seconds < 600:
        return _cache["data"]

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT_BH,
        "longitude": LON_BH,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,rain",
        "timezone": "America/Sao_Paulo"
    }

    try:
        resposta = requests.get(url, params=params, timeout=10)
        resposta.raise_for_status()
        dados = resposta.json()
        atual = dados["current"]

        chuva_mm = atual.get("rain", 0.0) if atual.get("rain") is not None else 0.0
        
        resultado = {
            "condicao": _mapear_condicao(atual["weather_code"]),
            "descricao": _descrever_condicao(atual["weather_code"]),
            "temperatura": atual["temperature_2m"],
            "sensacao_termica": atual["apparent_temperature"],
            "umidade": atual["relative_humidity_2m"],
            "chuva_mm": chuva_mm,
            "icone": _obter_icone(atual["weather_code"]),
            "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "simulado": False
        }

        _cache["timestamp"] = agora
        _cache["data"] = resultado
        return resultado

    except Exception as e:
        print(f"[weather] Erro na API Open-Meteo: {e}. Usando fallback simulado.")
        resultado = _previsao_simulada()
        resultado["simulado"] = True
        _cache["timestamp"] = agora
        _cache["data"] = resultado
        return resultado


def _mapear_condicao(codigo):
    if codigo in [95, 96, 99]:
        return "tempestade"
    elif codigo in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]:
        return "chuva"
    elif codigo in [45, 48]:
        return "neblina"
    elif codigo == 0:
        return "limpo"
    elif codigo == 1:
        return "limpo"
    elif codigo in [2, 3]:
        return "nublado"
    else:
        return "nublado"


def _descrever_condicao(codigo):
    descricoes = {
        0: "céu limpo",
        1: "predominantemente limpo",
        2: "parcialmente nublado",
        3: "nublado",
        45: "neblina",
        48: "nevoeiro",
        51: "garoa leve",
        61: "chuva leve",
        63: "chuva moderada",
        65: "chuva forte",
        80: "pancadas de chuva",
        95: "tempestade",
        96: "tempestade com granizo"
    }
    return descricoes.get(codigo, f"condição código {codigo}")


def _obter_icone(codigo):
    if codigo == 0:
        return "☀️"
    elif codigo in [1, 2]:
        return "⛅"
    elif codigo == 3:
        return "☁️"
    elif codigo in [45, 48]:
        return "🌫️"
    elif codigo in [51, 61, 80]:
        return "🌦️"
    elif codigo in [63, 65, 81, 82]:
        return "🌧️"
    elif codigo in [95, 96, 99]:
        return "⛈️"
    else:
        return "🌡️"


def _previsao_simulada():
    agora = datetime.now()
    hora = agora.hour
    if hora < 10:
        return {"condicao": "limpo", "descricao": "céu limpo (simulado)", "temperatura": 20.0,
                "sensacao_termica": 19.5, "umidade": 65, "chuva_mm": 0, "icone": "☀️",
                "data_hora": agora.strftime("%Y-%m-%d %H:%M:%S")}
    elif hora < 15:
        return {"condicao": "nublado", "descricao": "parcialmente nublado (simulado)", "temperatura": 27.0,
                "sensacao_termica": 28.5, "umidade": 55, "chuva_mm": 0, "icone": "⛅",
                "data_hora": agora.strftime("%Y-%m-%d %H:%M:%S")}
    else:
        return {"condicao": "chuva", "descricao": "pancadas de chuva (simulado)", "temperatura": 24.0,
                "sensacao_termica": 25.0, "umidade": 80, "chuva_mm": 5.2, "icone": "🌧️",
                "data_hora": agora.strftime("%Y-%m-%d %H:%M:%S")}
