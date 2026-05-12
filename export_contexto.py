"""
Generate a consolidated project snapshot for AI handoff.

The canonical technical memory for future AI/Codex sessions is:
    context/AI_PROJECT_MEMORY.md

This script generates context/contexto_ia.txt as a versioned snapshot that
includes key files in a stable order and excludes secrets/noisy artifacts.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_FILE = PROJECT_ROOT / "context" / "contexto_ia.txt"
PRIORITY_FILES = [
    Path("context/AI_PROJECT_MEMORY.md"),
    Path("context/contexto.md"),
    Path("app.py"),
    Path("engines/app_support.py"),
    Path("engines/recommendation_engine.py"),
    Path("export_contexto.py"),
    Path("requirements.txt"),
]
EXCLUDED_DIR_NAMES = {".git", "__pycache__", "venv", ".pytest_cache", ".mypy_cache", "models"}
EXCLUDED_FILE_NAMES = {".env", "contexto_ia.txt"}
EXCLUDED_SUFFIXES = {".pyc"}
EXCLUDED_RELATIVE_PATHS = {
    Path("data/eventos_cache.json"),
    Path("data/feedback.csv"),
    Path("data/training_data.csv"),
}


def _is_excluded(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)

    if any(part in EXCLUDED_DIR_NAMES for part in relative.parts[:-1]):
        return True
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    if relative in EXCLUDED_RELATIVE_PATHS:
        return True
    return False


def collect_project_files(root: Path = PROJECT_ROOT) -> list[Path]:
    root = root.resolve()
    discovered: list[Path] = []

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _is_excluded(path, root):
            continue
        discovered.append(path)

    ordered: list[Path] = []
    seen: set[Path] = set()

    for relative in PRIORITY_FILES:
        candidate = (root / relative).resolve()
        if candidate in discovered and candidate not in seen:
            ordered.append(candidate)
            seen.add(candidate)

    for path in discovered:
        if path not in seen:
            ordered.append(path)
            seen.add(path)

    return ordered


def render_context_snapshot(root: Path = PROJECT_ROOT) -> str:
    root = root.resolve()
    files = collect_project_files(root)
    lines = [
        "=" * 80,
        "STREETSMART BH — AI CONTEXT SNAPSHOT",
        "=" * 80,
        "",
        "Canonical source of truth for AI/Codex agents:",
        "  - context/AI_PROJECT_MEMORY.md",
        "",
        "This file is a generated snapshot. Regenerate it with:",
        "  - python export_contexto.py",
        "Versioning policy:",
        "  - this repository keeps contexto_ia.txt committed as an intentional snapshot",
        "  - regenerate it after architecture, contract, or core behavior changes",
        "",
        "Secrets policy:",
        "  - .env is excluded",
        "  - generated caches/noisy artifacts are excluded when configured",
        "",
        "Included files:",
    ]
    lines.extend(f"  - {path.relative_to(root)}" for path in files)
    lines.append("")

    for path in files:
        relative = path.relative_to(root)
        lines.extend(
            [
                "=" * 80,
                f"FILE: {relative}",
                "=" * 80,
                "",
            ]
        )
        try:
            lines.append(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            lines.append("[binary or non-UTF-8 file omitted]")
        lines.append("")

    return "\n".join(lines)


def gerar_contexto(output_file: Path = OUTPUT_FILE, root: Path = PROJECT_ROOT) -> Path:
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    content = render_context_snapshot(root)
    output_file.write_text(content, encoding="utf-8")
    print(f"✅ Contexto exportado para {output_file}")
    return output_file


def check_context_snapshot(output_file: Path = OUTPUT_FILE, root: Path = PROJECT_ROOT) -> bool:
    output_file = Path(output_file)
    expected_content = render_context_snapshot(root)

    if not output_file.exists():
        print(f"❌ Snapshot ausente: {output_file}")
        print("   Rode `python export_contexto.py` para gerar o snapshot versionado.")
        return False

    current_content = output_file.read_text(encoding="utf-8")
    if current_content != expected_content:
        print(f"❌ Snapshot desatualizado: {output_file}")
        print("   Rode `python export_contexto.py` para regenerar o arquivo antes de commitar.")
        return False

    print(f"✅ Snapshot atualizado: {output_file}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verifica se context/contexto_ia.txt está atualizado sem modificar o arquivo",
    )
    args = parser.parse_args(argv)

    if args.check:
        return 0 if check_context_snapshot() else 1

    gerar_contexto()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
