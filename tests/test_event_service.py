from engines import event_service


def test_carregar_cache_ignores_malformed_json(tmp_path, monkeypatch):
    cache_file = tmp_path / "eventos_cache.json"
    cache_file.write_text("{not-valid-json", encoding="utf-8")

    monkeypatch.setattr(event_service, "CACHE_FILE", cache_file)

    assert event_service._carregar_cache() is None
