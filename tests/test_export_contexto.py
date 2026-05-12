from pathlib import Path

from export_contexto import check_context_snapshot, collect_project_files, gerar_contexto, render_context_snapshot


def test_collect_project_files_prioritizes_ai_memory_and_excludes_env(tmp_path):
    (tmp_path / "context").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "engines").mkdir()
    (tmp_path / ".env").write_text("SECRET=1\n", encoding="utf-8")
    (tmp_path / "context" / "AI_PROJECT_MEMORY.md").write_text("# memory\n", encoding="utf-8")
    (tmp_path / "context" / "contexto.md").write_text("# contexto\n", encoding="utf-8")
    (tmp_path / "context" / "contexto_ia.txt").write_text("old snapshot\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('app')\n", encoding="utf-8")
    (tmp_path / "engines" / "app_support.py").write_text("# helper\n", encoding="utf-8")
    (tmp_path / "data" / "eventos_cache.json").write_text('{"eventos": []}\n', encoding="utf-8")
    (tmp_path / "data" / "training_data.csv").write_text("x,y\n1,2\n", encoding="utf-8")

    files = collect_project_files(tmp_path)
    relative_files = [path.relative_to(tmp_path).as_posix() for path in files]

    assert relative_files[0] == "context/AI_PROJECT_MEMORY.md"
    assert ".env" not in relative_files
    assert "context/contexto_ia.txt" not in relative_files
    assert "data/eventos_cache.json" not in relative_files
    assert "data/training_data.csv" not in relative_files


def test_render_context_snapshot_marks_ai_memory_as_canonical(tmp_path):
    (tmp_path / "context").mkdir()
    (tmp_path / "context" / "AI_PROJECT_MEMORY.md").write_text("# memory\n", encoding="utf-8")
    (tmp_path / "context" / "contexto.md").write_text("# contexto\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('app')\n", encoding="utf-8")

    snapshot = render_context_snapshot(tmp_path)

    assert "Canonical source of truth for AI/Codex agents:" in snapshot
    assert "context/AI_PROJECT_MEMORY.md" in snapshot
    assert "this repository keeps contexto_ia.txt committed as an intentional snapshot" in snapshot
    assert "FILE: context/AI_PROJECT_MEMORY.md" in snapshot


def test_check_context_snapshot_passes_when_snapshot_is_current(tmp_path):
    (tmp_path / "context").mkdir()
    (tmp_path / "context" / "AI_PROJECT_MEMORY.md").write_text("# memory\n", encoding="utf-8")
    (tmp_path / "context" / "contexto.md").write_text("# contexto\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('app')\n", encoding="utf-8")

    output_file = tmp_path / "context" / "contexto_ia.txt"
    gerar_contexto(output_file=output_file, root=tmp_path)

    assert check_context_snapshot(output_file=output_file, root=tmp_path) is True
    assert output_file.exists()


def test_check_context_snapshot_detects_stale_snapshot_without_rewriting(tmp_path):
    (tmp_path / "context").mkdir()
    (tmp_path / "context" / "AI_PROJECT_MEMORY.md").write_text("# memory\n", encoding="utf-8")
    (tmp_path / "context" / "contexto.md").write_text("# contexto\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('app')\n", encoding="utf-8")

    output_file = tmp_path / "context" / "contexto_ia.txt"
    output_file.write_text("stale snapshot\n", encoding="utf-8")

    assert check_context_snapshot(output_file=output_file, root=tmp_path) is False
    assert output_file.read_text(encoding="utf-8") == "stale snapshot\n"


def test_gerar_contexto_writes_snapshot_file(tmp_path):
    (tmp_path / "context").mkdir()
    (tmp_path / "context" / "AI_PROJECT_MEMORY.md").write_text("# memory\n", encoding="utf-8")
    (tmp_path / "context" / "contexto.md").write_text("# contexto\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('app')\n", encoding="utf-8")

    output_file = tmp_path / "context" / "contexto_ia.txt"
    gerar_contexto(output_file=output_file, root=tmp_path)

    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8") == render_context_snapshot(tmp_path)
