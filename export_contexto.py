"""
Gera um arquivo consolidado com todo o conteúdo do projeto para
ser enviado a uma IA em um novo chat do zero.
"""
import os
from pathlib import Path

OUTPUT_FILE = "context/contexto_ia.txt"
EXCLUDE = {".git", "__pycache__", "venv", "models", "*.pyc", ".env", "contexto_ia.txt"}

def gerar_contexto():
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("=" * 80 + "\n")
        out.write("STREETSMART BH — CONTEXTO COMPLETO DO PROJETO\n")
        out.write("=" * 80 + "\n\n")

        for root, dirs, files in os.walk("."):
            if any(ex in root for ex in [".git", "__pycache__", "venv"]):
                continue
            for file in sorted(files):
                if file.endswith(".pyc") or file == "contexto_ia.txt" or file == ".env":
                    continue
                path = Path(root) / file
                out.write(f"\n{'=' * 80}\n")
                out.write(f"FILE: {path}\n{'=' * 80}\n\n")
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        out.write(f.read())
                except Exception:
                    out.write("[arquivo binário]\n")
                out.write("\n")

    print(f"✅ Contexto exportado para {OUTPUT_FILE}")

if __name__ == "__main__":
    gerar_contexto()