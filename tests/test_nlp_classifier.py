from engines import nlp_classifier


def test_classificar_evento_returns_safe_fallback_on_model_failure(monkeypatch):
    def quebrar_modelo():
        raise RuntimeError("falha de teste")

    monkeypatch.setattr(nlp_classifier, "_carregar_modelo", quebrar_modelo)

    resultado = nlp_classifier.classificar_evento("Show na Savassi")

    assert resultado["tipo"] == "evento"
    assert resultado["confianca"] == 0.0
    assert resultado["alternativas"] == []
