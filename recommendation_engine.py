"""
Motor de Recomendação StreetSmart BH
Utiliza matriz de decisão com pesos normalizados para ranquear produtos
Baseado em 4 fatores: clima, dia da semana, horário e eventos
"""
import json
import datetime
import math
from pathlib import Path
from weather_service import obter_previsao_bh


class RecommendationEngine:
    """
    Motor de recomendação multi-fatorial.
    
    A recomendação final é um score normalizado (0-100) calculado como:
    Score = (P_clima * W_clima) + (P_data * W_data) + (P_hora * W_hora) + (P_evento * W_evento)
    
    Onde:
    - P_* são pontuações de 0 a 1 para cada fator
    - W_* são pesos que determinam a importância relativa
    
    Pesos iniciais (ajustáveis com dados reais):
    - Clima: 35% (maior impacto comprovado em vendas de rua)
    - Data:  15% (sazonalidade semanal)
    - Hora:  20% (padrões de consumo por horário)
    - Evento: 30% (demanda concentrada e previsível)
    """
    
    def __init__(self, produtos_path="data/produtos.json"):
        self.produtos = self._carregar_produtos(produtos_path)
        
        # Pesos estatísticos (serão calibrados com ML supervisionado futuramente)
        self.pesos = {
            "clima": 0.35,
            "data": 0.15,
            "hora": 0.20,
            "evento": 0.30
        }
        
        # Eventos mapeados (simulação — será substituído por API real no futuro)
        self.eventos_hoje = self._detectar_eventos()
    
    def _carregar_produtos(self, path):
        """Carrega catálogo de produtos do JSON"""
        arquivo = Path(path)
        if not arquivo.exists():
            raise FileNotFoundError(f"Catálogo não encontrado: {path}")
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _detectar_eventos(self):
        """
        Detecta eventos do dia (simulado).
        Passo 4 substituirá por API real (Portal de Dados Abertos PBH + scraping).
        """
        hoje = datetime.date.today()
        eventos_simulados = []
        
        # Simulação: shows aos sábados, feiras aos domingos, congressos em dias úteis
        if hoje.weekday() == 5:  # Sábado
            eventos_simulados.append({"tipo": "show", "nome": "Show no Mineirão"})
        elif hoje.weekday() == 6:  # Domingo
            eventos_simulados.append({"tipo": "feira", "nome": "Feira Hippie"})
        elif hoje.weekday() in [2, 3]:  # Quarta/Quinta
            eventos_simulados.append({"tipo": "congresso", "nome": "Congresso no Expominas"})
        
        return eventos_simulados
    
    def _score_clima(self, produto_nome, clima):
        """
        Calcula pontuação climática (0-1).
        Retorna 1.0 se o clima atual é ideal para o produto,
        0.0 se desfavorável, valores intermediários caso contrário.
        """
        prod = self.produtos[produto_nome]
        condicao = clima["condicao"]
        
        if condicao in prod["climas_favoraveis"]:
            return 1.0
        elif condicao in prod["climas_desfavoraveis"]:
            return 0.0
        
        # Temperatura como fator secundário
        temp = clima["temperatura"]
        if "agua" in produto_nome.lower() or "suco" in produto_nome.lower():
            # Bebidas geladas: demanda cresce com temperatura
            return min(temp / 35.0, 1.0)
        elif "cafe" in produto_nome.lower() or "quente" in produto_nome.lower():
            # Bebidas quentes: demanda cresce com frio
            return max(1.0 - (temp / 30.0), 0.0)
        
        return 0.5  # Neutro
    
    def _score_data(self, produto_nome, data):
        """
        Pontuação por dia da semana (0-1).
        Produtos têm dias mais favoráveis (ex: pastel no fim de semana).
        """
        prod = self.produtos[produto_nome]
        dia_semana = data.weekday()
        
        if dia_semana in prod["dias_favoraveis"]:
            # Se todo dia é favorável, retorna score médio-alto
            if len(prod["dias_favoraveis"]) == 7:
                return 0.7
            # Dias específicos: score proporcional
            return 0.9
        return 0.1
    
    def _score_hora(self, produto_nome, hora):
        """
        Pontuação por horário (0-1).
        Verifica se a hora está dentro dos picos de consumo do produto.
        """
        prod = self.produtos[produto_nome]
        
        if hora in prod["horarios_pico"]:
            return 1.0
        
        # Distância do pico mais próximo (decaimento gaussiano)
        pico_mais_proximo = min(prod["horarios_pico"], key=lambda h: abs(h - hora))
        distancia = abs(pico_mais_proximo - hora)
        
        # Decaimento: score cai pela metade a cada 2 horas de distância
        return max(0.0, 1.0 / (1.0 + distancia))
    
    def _score_evento(self, produto_nome):
        """
        Pontuação por evento (0-1).
        Verifica se há evento hoje associado ao produto.
        """
        prod = self.produtos[produto_nome]
        
        if not self.eventos_hoje:
            return 0.3  # Sem eventos: score neutro-baixo
        
        for evento in self.eventos_hoje:
            if evento["tipo"] in prod["eventos_associados"]:
                return 1.0
        
        return 0.1  # Evento existe mas não é associado
    
    def calcular_recomendacao(self, clima=None):
        """
        Calcula score final para todos os produtos e retorna o melhor.
        
        Args:
            clima: dict com dados climáticos (usa API se None)
        
        Returns:
            dict com recomendação completa e métricas
        """
        if clima is None:
            clima = obter_previsao_bh()
        
        agora = datetime.datetime.now()
        hora = agora.hour
        data = agora.date()
        
        resultados = []
        
        for nome_produto, atributos in self.produtos.items():
            # Calcula cada pontuação individual
            p_clima = self._score_clima(nome_produto, clima)
            p_data = self._score_data(nome_produto, data)
            p_hora = self._score_hora(nome_produto, hora)
            p_evento = self._score_evento(nome_produto)
            
            # Score ponderado final (0-100)
            score = (
                p_clima * self.pesos["clima"] +
                p_data * self.pesos["data"] +
                p_hora * self.pesos["hora"] +
                p_evento * self.pesos["evento"]
            ) * 100
            
            # Lucro estimado (considera margem e score de sucesso)
            lucro_unitario = atributos["preco_venda"] - atributos["custo"]
            lucro_estimado = lucro_unitario * (score / 100) * 50  # 50 unidades esperadas
            
            resultados.append({
                "produto": nome_produto,
                "score": round(score, 1),
                "lucro_estimado": round(lucro_estimado, 2),
                "margem": atributos["margem"],
                "custo": atributos["custo"],
                "preco_venda": atributos["preco_venda"],
                "categoria": atributos["categoria"],
                "metricas": {
                    "p_clima": round(p_clima, 2),
                    "p_data": round(p_data, 2),
                    "p_hora": round(p_hora, 2),
                    "p_evento": round(p_evento, 2)
                }
            })
        
        # Ordena por score decrescente
        resultados.sort(key=lambda x: x["score"], reverse=True)
        
        # Top 3 para comparação
        top3 = resultados[:3]
        melhor = top3[0]
        
        # Gera explicações
        explicacoes = self._gerar_explicacoes(melhor, top3, clima)
        
        return {
            "recomendacao": melhor,
            "alternativas": top3[1:],
            "explicacoes": explicacoes,
            "clima": clima,
            "eventos": self.eventos_hoje,
            "hora_consulta": agora.strftime("%H:%M"),
            "data_consulta": agora.strftime("%d/%m/%Y")
        }
    
    def _gerar_explicacoes(self, melhor, top3, clima):
        """Gera explicações textuais baseadas nas métricas"""
        expl = []
        metricas = melhor["metricas"]
        
        # Maior influência
        maior_fator = max(metricas, key=metricas.get)
        fatores_nome = {
            "p_clima": f"clima ({clima['descricao']})",
            "p_data": f"dia da semana",
            "p_hora": f"horário atual",
            "p_evento": "evento detectado" if self.eventos_hoje else "ausência de eventos"
        }
        expl.append(
            f"🎯 Principal fator: {fatores_nome[maior_fator]} "
            f"(score: {metricas[maior_fator]:.0%})"
        )
        
        # Por que não o segundo colocado?
        if len(top3) > 1:
            segundo = top3[1]
            diff = melhor["score"] - segundo["score"]
            if diff > 10:
                expl.append(
                    f"📊 {melhor['produto']} supera '{segundo['produto']}' "
                    f"por {diff:.1f} pontos — margem e adequação ao clima decisivos"
                )
        
        # Evento?
        if self.eventos_hoje:
            nomes = [e["nome"] for e in self.eventos_hoje]
            expl.append(f"🎪 Evento(s) hoje: {', '.join(nomes)} — demanda concentrada prevista")
        
        # Clima
        expl.append(
            f"🌤️ Condição atual ({clima['descricao']}, {clima['temperatura']:.0f}°C) "
            f"favorece produtos da categoria '{melhor['categoria']}'"
        )
        
        return expl
    
    def sugerir_local(self, recomendacao, clima):
        """Sugere local baseado no produto e condições"""
        produto = recomendacao["produto"]
        categoria = recomendacao["categoria"]
        
        # Mapeamento produto → local (será refinado com dados de fluxo real)
        locais = {
            "bebida": {
                "limpo": "Praça da Liberdade — alto fluxo turístico",
                "nublado": "Praça Sete — Centro — movimento constante",
                "chuva": "Marquises da Av. Amazonas — proteção + fluxo",
            },
            "alimento": {
                "limpo": "Feira da Afonso Pena — público qualificado",
                "nublado": "Savassi — praças e bares",
                "chuva": "Shoppings (entorno) — Estação BH",
            },
            "protecao": {
                "chuva": "Entradas de shoppings e metrô — Centro",
                "garoa": "Pontos de ônibus — Praça Sete",
            },
            "acessorio": {
                "limpo": "Parque Municipal — público leisure",
            },
            "eletronico": {
                "limpo": "Congressos e eventos — Expominas",
            },
        }
        
        condicao = clima["condicao"]
        cat_locais = locais.get(categoria, {})
        local = cat_locais.get(condicao, "Praça Sete — Centro (local padrão)")
        
        # Ajusta por evento
        if self.eventos_hoje:
            for ev in self.eventos_hoje:
                if ev["tipo"] in self.produtos[produto].get("eventos_associados", []):
                    local = f"Entorno do evento: {ev['nome']}"
        
        return local
    
    def sugerir_fornecedor(self, produto):
        """Mapeia produto → fornecedor (será expandido com API de preços)"""
        fornecedores = {
            "guarda-chuva compacto": "Distribuidora Central (Centro) — R$ 8,00/un",
            "agua mineral gelada 500ml": "Fonte Fria Atacado — R$ 1,20/un",
            "cafe quente 200ml": "Café do Zé (Santa Tereza) — R$ 2,00/un",
            "pastel frito na hora": "Pastelaria Bom Sabor — R$ 3,50/un",
            "suco natural laranja 300ml": "Feira do Produtor (Ceasa) — R$ 3,00/un",
            "oculos de sol": "Atacadão Acessórios — R$ 7,00/un",
            "carregador portatil": "Eletrônicos BH (Shopping Oiapoque) — R$ 25,00/un",
            "cerveja artesanal lata": "Cervejaria do Zé (Savassi) — R$ 6,00/un",
            "capa de chuva descartavel": "Distribuidora Central (Centro) — R$ 3,50/un",
        }
        return fornecedores.get(produto, "Fornecedor padrão — consulte catálogo local")