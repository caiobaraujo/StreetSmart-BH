"""
Classificador NLP para eventos de BH usando BERTimbau
Modelo gratuito, roda localmente sem GPU obrigatória
"""
from transformers import pipeline

# Carrega o modelo uma única vez (cache do transformers)
_classifier = None

# Categorias que realmente importam para recomendação de produtos
CATEGORIAS = [
    "show musical",
    "evento esportivo",
    "feira de artesanato",
    "feira gastronômica",
    "congresso corporativo",
    "evento religioso",
    "festa universitária",
    "carnaval de rua",
    "teatro ou comédia",
    "manifestação política",
    "evento familiar",
    "evento infantil"
]


def _carregar_modelo():
    global _classifier
    if _classifier is None:
        print("[nlp] Carregando BERTimbau...")
        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1  # -1 = CPU, use 0 se tiver GPU NVIDIA
        )
    return _classifier


def classificar_evento(nome_evento: str) -> dict:
    """
    Recebe o nome de um evento e retorna classificação com scores.
    Ex: "Show do Milton Nascimento" → {"tipo": "show musical", "confianca": 0.95}
    """
    if not nome_evento or len(nome_evento) < 3:
        return {"tipo": "evento", "confianca": 0.0}

    try:
        model = _carregar_modelo()
        resultado = model(nome_evento, CATEGORIAS)
        return {
            "tipo": resultado["labels"][0],
            "confianca": resultado["scores"][0],
            "alternativas": list(zip(resultado["labels"][1:3], resultado["scores"][1:3]))
        }
    except Exception as e:
        print(f"[nlp] Erro ao classificar evento '{nome_evento}': {e}")
        return {"tipo": "evento", "confianca": 0.0, "alternativas": []}
