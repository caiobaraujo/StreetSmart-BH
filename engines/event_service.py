"""
Serviço de eventos reais de Belo Horizonte
Fontes: Portal de Dados Abertos PBH, Sympla API, Eventbrite API
"""
import requests
import datetime
from pathlib import Path
import json
import os

# ═══════════════════════════════════════
# CONFIGURAÇÃO (chaves gratuitas)
# ═══════════════════════════════════════

# Portal de Dados Abertos PBH — API pública (sem chave)
PBH_API_URL = "https://dados.pbh.gov.br/api/3/action/datastore_search"
PBH_EVENTOS_RESOURCE = "f45e2b8a-3b1c-4c5d-9e7f-123456789abc"  # placeholder — será ajustado

# Sympla API — cadastro gratuito em https://www.sympla.com.br/api
# Gera token em: Minha Conta > Integrações > API
SYMPLA_TOKEN = os.getenv("SYMPLA_TOKEN", "")

# Eventbrite API — cadastro gratuito em https://www.eventbrite.com/platform
EVENTBRITE_TOKEN = os.getenv("EVENTBRITE_TOKEN", "")

# Cache local para evitar chamadas repetidas
CACHE_FILE = Path("data/eventos_cache.json")
CACHE_HORAS = 6  # atualiza a cada 6 horas


# ═══════════════════════════════════════
# EVENTOS DA PBH (oficiais/licenciados)
# ═══════════════════════════════════════

def obter_eventos_pbh():
    """
    Busca eventos oficiais da PBH.
    Portal: https://dados.pbh.gov.br
    Retorna lista de dicts com: nome, tipo, data, local, publico_esperado
    """
    # A API da PBH usa CKAN. Tentamos buscar datasets de eventos/feiras
    try:
        # Endpoint de busca de datasets com tag "eventos" ou "feiras"
        url = "https://dados.pbh.gov.br/api/3/action/package_search"
        params = {
            "q": "eventos OR feiras",
            "rows": 10
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        dados = resp.json()
        
        eventos = []
        if dados.get("success"):
            for pacote in dados["result"]["results"]:
                eventos.append({
                    "nome": pacote.get("title", "Evento PBH"),
                    "tipo": "feira" if "feira" in pacote.get("title", "").lower() else "evento",
                    "local": pacote.get("organization", {}).get("title", "Belo Horizonte"),
                    "data": datetime.date.today().strftime("%Y-%m-%d"),
                    "fonte": "PBH",
                    "url": f"https://dados.pbh.gov.br/dataset/{pacote.get('name', '')}"
                })
        return eventos
    
    except requests.exceptions.ConnectionError:
        print("[event_service] PBH: sem conexão")
        return []
    except Exception as e:
        print(f"[event_service] PBH erro: {e}")
        return []


# ═══════════════════════════════════════
# SYMPLA API (eventos pagos e gratuitos)
# ═══════════════════════════════════════

def obter_eventos_sympla():
    """
    Busca eventos em BH pela API do Sympla.
    Documentação: https://developers.sympla.com.br
    Retorna lista de eventos com nome, data, local, categoria
    """
    if not SYMPLA_TOKEN:
        print("[event_service] Sympla: token não configurado")
        return []
    
    try:
        url = "https://api.sympla.com.br/public/v3/events"
        headers = {"s_token": SYMPLA_TOKEN}
        params = {
            "page_size": 20,
            "state": "MG"  # Filtra por Minas Gerais (não tem filtro direto por cidade na API pública)
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        dados = resp.json()
        
        eventos = []
        for ev in dados.get("data", []):
            # Filtra apenas eventos em BH pelo nome do local
            local = ev.get("address", {}).get("city", "")
            if "BELO HORIZONTE" in local.upper() or "BH" in local.upper():
                eventos.append({
                    "nome": ev.get("name", "Evento Sympla"),
                    "tipo": _classificar_evento(ev.get("name", "")),
                    "local": ev.get("address", {}).get("venue", "Belo Horizonte"),
                    "data": ev.get("start_date", "")[:10],
                    "fonte": "Sympla",
                    "url": ev.get("url", "")
                })
        
        return eventos
    
    except Exception as e:
        print(f"[event_service] Sympla erro: {e}")
        return []


# ═══════════════════════════════════════
# EVENTBRITE API (eventos internacionais + locais)
# ═══════════════════════════════════════

def obter_eventos_eventbrite():
    """
    Busca eventos em BH pela Eventbrite API v3.
    Documentação: https://www.eventbrite.com/platform/api
    Retorna lista de eventos
    """
    if not EVENTBRITE_TOKEN:
        print("[event_service] Eventbrite: token não configurado")
        return []
    
    try:
        url = "https://www.eventbriteapi.com/v3/events/search/"
        headers = {"Authorization": f"Bearer {EVENTBRITE_TOKEN}"}
        params = {
            "location.address": "Belo Horizonte",
            "location.within": "15km",
            "start_date.range_start": datetime.date.today().strftime("%Y-%m-%dT00:00:00Z"),
            "start_date.range_end": (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%dT23:59:59Z"),
            "page_size": 20
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        dados = resp.json()
        
        eventos = []
        for ev in dados.get("events", []):
            nome = ev.get("name", {}).get("text", "Evento Eventbrite")
            eventos.append({
                "nome": nome,
                "tipo": _classificar_evento(nome),
                "local": ev.get("venue_id", "Belo Horizonte"),
                "data": ev.get("start", {}).get("local", "")[:10],
                "fonte": "Eventbrite",
                "url": ev.get("url", "")
            })
        
        return eventos
    
    except Exception as e:
        print(f"[event_service] Eventbrite erro: {e}")
        return []


# ═══════════════════════════════════════
# CACHE E ORQUESTRAÇÃO
# ═══════════════════════════════════════

def _classificar_evento(nome):
    """Classifica o tipo de evento pelo nome"""
    nome = nome.lower()
    if any(p in nome for p in ["show", "musical", "rock", "sertanejo", "funk"]):
        return "show"
    elif any(p in nome for p in ["feira", "mercado", "artesanato", "gastronom"]):
        return "feira"
    elif any(p in nome for p in ["congresso", "palestra", "workshop", "conferência"]):
        return "congresso"
    elif any(p in nome for p in ["jogo", "campeonato", "futebol", "partida"]):
        return "jogo"
    elif any(p in nome for p in ["festival", "carnaval", "bloco"]):
        return "festival"
    elif any(p in nome for p in ["teatro", "comédia", "stand-up"]):
        return "show"
    return "evento"


def _carregar_cache():
    """Carrega cache do disco se ainda válido"""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
            data_cache = datetime.datetime.fromisoformat(cache["timestamp"])
            if (datetime.datetime.now() - data_cache).seconds < CACHE_HORAS * 3600:
                return cache.get("eventos", [])
        except Exception as e:
            print(f"[event_service] Cache inválido, ignorando arquivo local: {e}")
    return None


def _salvar_cache(eventos):
    """Salva eventos em cache local"""
    CACHE_FILE.parent.mkdir(exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({
            "timestamp": datetime.datetime.now().isoformat(),
            "eventos": eventos
        }, f, ensure_ascii=False, indent=2)


def obter_todos_eventos():
    """
    Orquestra todas as fontes de eventos.
    Retorna lista consolidada de eventos do dia em BH.
    Com cache de 6 horas.
    """
    # Verifica cache
    cache = _carregar_cache()
    if cache is not None:
        print("[event_service] Retornando eventos do cache")
        return cache
    
    print("[event_service] Buscando eventos em tempo real...")
    todos = []
    
    # Coleta de cada fonte (falhas individuais não quebram o sistema)
    todos.extend(obter_eventos_pbh())
    todos.extend(obter_eventos_sympla())
    todos.extend(obter_eventos_eventbrite())
    
    # Se nada foi encontrado, usa fallback inteligente
    if not todos:
        todos = _eventos_fallback()
    
    # Remove duplicatas (mesmo nome e data)
    vistos = set()
    unicos = []
    for ev in todos:
        chave = (ev["nome"].lower().strip(), ev.get("data", ""))
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(ev)
    
    _salvar_cache(unicos)
    return unicos


def _eventos_fallback():
    """
    Fallback quando nenhuma API está disponível.
    Baseado em padrões reais de BH identificados na pesquisa de mercado.
    """
    hoje = datetime.date.today()
    dia_semana = hoje.weekday()
    eventos = []
    
    # Padrões reais de BH (fonte: pesquisa O TEMPO e PBH)
    if dia_semana == 6:  # Domingo
        eventos.append({
            "nome": "Feira Hippie (Av. Afonso Pena)",
            "tipo": "feira",
            "local": "Avenida Afonso Pena - Centro",
            "data": hoje.strftime("%Y-%m-%d"),
            "fonte": "padrao_bh",
            "url": ""
        })
    elif dia_semana == 5:  # Sábado
        eventos.append({
            "nome": "Blocos de rua / Eventos Savassi",
            "tipo": "festival",
            "local": "Savassi - Região Centro-Sul",
            "data": hoje.strftime("%Y-%m-%d"),
            "fonte": "padrao_bh",
            "url": ""
        })
    elif dia_semana in [2, 3]:  # Quarta/Quinta
        eventos.append({
            "nome": "Congressos Expominas",
            "tipo": "congresso",
            "local": "Expominas - Gameleira",
            "data": hoje.strftime("%Y-%m-%d"),
            "fonte": "padrao_bh",
            "url": ""
        })
    
    # Eventos fixos diários de BH (casos reais de sucesso)
    eventos.append({
        "nome": "Fluxo comercial Praça Sete",
        "tipo": "fluxo",
        "local": "Praça Sete - Centro",
        "data": hoje.strftime("%Y-%m-%d"),
        "fonte": "padrao_bh",
        "url": ""
    })
    
    return eventos
