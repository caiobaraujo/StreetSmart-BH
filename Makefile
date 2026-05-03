.PHONY: install train run export clean

install:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	cp .env.example .env 2>/dev/null || true
	@echo "✅ Configure seu .env com a chave OpenWeather"

train:
	. venv/bin/activate && python train_model.py

run:
	. venv/bin/activate && streamlit run app.py --server.port 8501

export:
	. venv/bin/activate && python export_contexto.py
	@echo "✅ Contexto exportado para context/contexto_ia.txt"

clean:
	rm -rf __pycache__ engines/__pycache__ models/*
	rm -f data/eventos_cache.json context/contexto_ia.txt
