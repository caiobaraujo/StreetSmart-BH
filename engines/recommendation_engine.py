"""
Motor de Recomendação StreetSmart BH v3.0
Híbrido: Regras determinísticas + XGBoost + NLP
"""
import json
import datetime
import numpy as np
from pathlib import Path
from engines.weather_service import obter_previsao_bh
from engines.event_service import obter_todos_eventos
from engines.nlp_classifier import classificar_evento
import xgboost as xgb

_DEFAULT_MODEL = object()


class ProductCatalogError(ValueError):
    """Raised when the product catalog is empty or malformed."""


class RecommendationEngine:
    REQUIRED_PRODUCT_FIELDS = {
        "categoria",
        "preco_venda",
        "custo",
        "margem",
        "climas_favoraveis",
        "climas_desfavoraveis",
        "dias_favoraveis",
        "horarios_pico",
        "eventos_associados",
    }
    NUMERIC_PRODUCT_FIELDS = {"preco_venda", "custo", "margem"}
    LIST_PRODUCT_FIELDS = {
        "climas_favoraveis",
        "climas_desfavoraveis",
        "dias_favoraveis",
        "horarios_pico",
        "eventos_associados",
    }

    def __init__(
        self,
        produtos_path="data/produtos.json",
        weather_provider=obter_previsao_bh,
        event_provider=obter_todos_eventos,
        nlp_classifier=classificar_evento,
        now_provider=None,
        model=_DEFAULT_MODEL,
    ):
        self.produtos = self._carregar_produtos(produtos_path)
        self.pesos = {
            "clima": 0.30, "data": 0.10, "hora": 0.15,
            "evento": 0.25, "ml": 0.20
        }
        self.weather_provider = weather_provider
        self.event_provider = event_provider
        self.nlp_classifier = nlp_classifier
        self.now_provider = now_provider or datetime.datetime.now
        self.eventos_hoje = self.event_provider()
        self.model = self._carregar_modelo_ml() if model is _DEFAULT_MODEL else model

    def _carregar_produtos(self, path):
        arquivo = Path(path)
        if not arquivo.exists():
            raise FileNotFoundError(f"Catálogo não encontrado: {path}")
        with open(arquivo, "r", encoding="utf-8") as f:
            produtos = json.load(f)
        self._validar_catalogo_produtos(produtos)
        return produtos

    def _validar_catalogo_produtos(self, produtos):
        if not isinstance(produtos, dict):
            raise ProductCatalogError("O catálogo de produtos deve ser um objeto JSON com produtos nomeados.")
        if not produtos:
            raise ProductCatalogError("O catálogo de produtos está vazio.")

        for nome_produto, atributos in produtos.items():
            if not isinstance(atributos, dict):
                raise ProductCatalogError(
                    f"Produto '{nome_produto}' inválido: a configuração do produto deve ser um objeto."
                )

            faltando = sorted(self.REQUIRED_PRODUCT_FIELDS - atributos.keys())
            if faltando:
                raise ProductCatalogError(
                    f"Produto '{nome_produto}' inválido: campo obrigatório ausente: {faltando[0]}"
                )

            categoria = atributos.get("categoria")
            if not isinstance(categoria, str) or not categoria.strip():
                raise ProductCatalogError(
                    f"Produto '{nome_produto}' inválido: campo 'categoria' deve ser uma string não vazia."
                )

            for field in self.NUMERIC_PRODUCT_FIELDS:
                valor = atributos.get(field)
                if not isinstance(valor, (int, float)) or isinstance(valor, bool):
                    raise ProductCatalogError(
                        f"Produto '{nome_produto}' inválido: campo '{field}' deve ser numérico."
                    )

            for field in self.LIST_PRODUCT_FIELDS:
                valor = atributos.get(field)
                if not isinstance(valor, list):
                    raise ProductCatalogError(
                        f"Produto '{nome_produto}' inválido: campo '{field}' deve ser uma lista."
                    )

            horarios_pico = atributos.get("horarios_pico", [])
            if not horarios_pico:
                raise ProductCatalogError(
                    f"Produto '{nome_produto}' inválido: campo 'horarios_pico' não pode ser vazio."
                )

    def _carregar_modelo_ml(self):
        modelo_path = "models/xgboost_model.json"
        if Path(modelo_path).exists():
            model = xgb.Booster()
            model.load_model(modelo_path)
            print("[engine] ✅ Modelo XGBoost carregado")
            return model
        print("[engine] ⚠️ Modelo ML não encontrado")
        return None

    def _classificar_eventos_com_nlp(self):
        for evento in self.eventos_hoje:
            if "tipo_nlp" not in evento:
                resultado = self.nlp_classifier(evento.get("nome", ""))
                evento["tipo_nlp"] = resultado["tipo"]
                evento["confianca_nlp"] = resultado["confianca"]

    def _score_clima(self, produto_nome, clima):
        prod = self.produtos[produto_nome]
        condicao = clima["condicao"]
        if condicao in prod["climas_favoraveis"]: return 1.0
        elif condicao in prod["climas_desfavoraveis"]: return 0.0
        temp = clima["temperatura"]
        if "agua" in produto_nome.lower() or "suco" in produto_nome.lower():
            return min(temp / 35.0, 1.0)
        elif "cafe" in produto_nome.lower() or "quente" in produto_nome.lower():
            return max(1.0 - (temp / 30.0), 0.0)
        return 0.5

    def _score_data(self, produto_nome, data):
        prod = self.produtos[produto_nome]
        dia_semana = data.weekday()
        if dia_semana in prod["dias_favoraveis"]:
            return 0.7 if len(prod["dias_favoraveis"]) == 7 else 0.9
        return 0.1

    def _score_hora(self, produto_nome, hora):
        prod = self.produtos[produto_nome]
        if hora in prod["horarios_pico"]: return 1.0
        pico_mais_proximo = min(prod["horarios_pico"], key=lambda h: abs(h - hora))
        distancia = abs(pico_mais_proximo - hora)
        return max(0.0, 1.0 / (1.0 + distancia))

    def _score_evento(self, produto_nome):
        prod = self.produtos[produto_nome]
        if not self.eventos_hoje: return 0.1
        melhor_score = 0.0
        for evento in self.eventos_hoje:
            tipo = evento.get("tipo_nlp", evento.get("tipo", "evento"))
            if tipo in prod["eventos_associados"]:
                melhor_score = max(melhor_score, 1.0 if evento.get("fonte") != "padrao_bh" else 0.7)
            if tipo in ["carnaval de rua", "show musical"]:
                melhor_score = max(melhor_score, 0.9)
        return melhor_score if melhor_score > 0 else 0.1

    def _score_ml(self, produto_nome, clima, data, hora):
        if self.model is None: return 0.5
        prod = self.produtos[produto_nome]
        try:
            features = np.array([[
                float(clima["temperatura"]), float(clima["chuva_mm"]),
                float(clima["umidade"]), float(data.weekday()), float(hora),
                float(1 if self.eventos_hoje else 0), float(prod["preco_venda"]),
                float(prod["custo"]), float(prod["margem"]) / 100.0
            ]], dtype=np.float32)
            pred = self.model.predict(xgb.DMatrix(features))[0]
            return min(float(pred) / 50.0, 1.0)
        except Exception as e:
            print(f"[engine] Erro ao calcular score ML para '{produto_nome}': {e}")
            return 0.5

    def calcular_recomendacao(self, clima=None):
        if clima is None: clima = self.weather_provider()
        self._classificar_eventos_com_nlp()
        agora = self.now_provider()
        hora = agora.hour
        data = agora.date()
        resultados = []

        for nome_produto, atributos in self.produtos.items():
            p_clima = self._score_clima(nome_produto, clima)
            p_data = self._score_data(nome_produto, data)
            p_hora = self._score_hora(nome_produto, hora)
            p_evento = self._score_evento(nome_produto)
            p_ml = self._score_ml(nome_produto, clima, data, hora)

            score = (p_clima * self.pesos["clima"] + p_data * self.pesos["data"] +
                     p_hora * self.pesos["hora"] + p_evento * self.pesos["evento"] +
                     p_ml * self.pesos["ml"]) * 100

            lucro_unitario = atributos["preco_venda"] - atributos["custo"]
            vendas_estimadas = max(1, int(score / 100 * 50))
            lucro_estimado = lucro_unitario * vendas_estimadas

            resultados.append({
                "produto": nome_produto, "score": round(score, 1),
                "lucro_estimado": round(lucro_estimado, 2),
                "vendas_estimadas": vendas_estimadas,
                "margem": atributos["margem"], "custo": atributos["custo"],
                "preco_venda": atributos["preco_venda"],
                "categoria": atributos["categoria"],
                "metricas": {"p_clima": round(p_clima, 2), "p_data": round(p_data, 2),
                             "p_hora": round(p_hora, 2), "p_evento": round(p_evento, 2),
                             "p_ml": round(p_ml, 2)}
            })

        resultados.sort(key=lambda x: x["score"], reverse=True)
        top3 = resultados[:3]
        melhor = top3[0]

        return {
            "recomendacao": melhor, "alternativas": top3[1:],
            "explicacoes": self._gerar_explicacoes(melhor, top3, clima),
            "clima": clima, "eventos": self.eventos_hoje,
            "hora_consulta": agora.strftime("%H:%M"),
            "data_consulta": agora.strftime("%d/%m/%Y")
        }

    def _gerar_explicacoes(self, melhor, top3, clima):
        expl = []
        metricas = melhor["metricas"]
        maior_fator = max(metricas, key=metricas.get)
        fatores_nome = {
            "p_clima": f"condição climática ({clima['descricao']})",
            "p_data": "dia da semana", "p_hora": "horário de pico",
            "p_evento": "eventos detectados", "p_ml": "modelo preditivo (XGBoost)"
        }
        expl.append(f"🎯 Fator decisivo: **{fatores_nome.get(maior_fator, maior_fator)}** ({metricas[maior_fator]:.0%})")
        if clima.get("simulado"): expl.append("⚠️ Dados climáticos SIMULADOS")
        if self.eventos_hoje:
            reais = [e for e in self.eventos_hoje if e.get("fonte") != "padrao_bh"]
            if reais: expl.append(f"🎪 Eventos: {', '.join([e['nome'] for e in reais[:3]])}")
        produto = melhor["produto"]
        if produto in self.produtos and "nota_mercado" in self.produtos[produto]:
            expl.append(f"💡 {self.produtos[produto]['nota_mercado']}")
        return expl

    def sugerir_fornecedor(self, produto):
        fornecedores = {
            "guarda-chuva compacto": "Distribuidora Central (R. Curitiba, Centro) — R$ 8,00/un",
            "agua mineral gelada 500ml": "Fonte Fria Atacado (Ceasa BH) — R$ 1,20/un",
            "cafe quente 200ml": "Café do Zé (Santa Tereza) — R$ 2,00/un",
            "pastel frito na hora": "Pastelaria Bom Sabor (Mercado Central) — R$ 3,50/un",
            "suco natural laranja 300ml": "Feira do Produtor (Ceasa) — R$ 3,00/un",
            "oculos de sol": "Atacadão Acessórios (Shopping Oiapoque) — R$ 7,00/un",
            "carregador portatil": "Eletrônicos BH (Shopping Oiapoque) — R$ 25,00/un",
            "cerveja artesanal lata": "Cervejaria do Zé (Savassi) — R$ 6,00/un",
            "capa de chuva descartavel": "Distribuidora Central (Centro) — R$ 3,50/un",
            "drink pronto latinha": "Atacadão Bebidas (Av. Amazonas) — R$ 7,00/un",
            "palha italiana doce": "Mercado Central — banca de doces — R$ 1,50/un",
            "kit lanche saudavel": "Ceasa BH + produção própria — R$ 5,00/un",
            "adereco carnavalesco": "Atacadão Fantasias (Shopping Oiapoque) — R$ 2,00/un",
        }
        return fornecedores.get(produto, "Fornecedor padrão — consulte catálogo local")
