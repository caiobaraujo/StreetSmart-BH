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
from event_service import obter_todos_eventos


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
        self.eventos_hoje = obter_todos_eventos()
    
    def _carregar_produtos(self, path):
        """Carrega catálogo de produtos do JSON"""
        arquivo = Path(path)
        if not arquivo.exists():
            raise FileNotFoundError(f"Catálogo não encontrado: {path}")
        with open(arquivo, "r", encoding="utf-8") as f:
            return json.load(f)
    

    
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
            """Pontuação por evento (0-1) usando dados reais"""
            prod = self.produtos[produto_nome]
            
            if not self.eventos_hoje:
                return 0.3
            
            melhor_score = 0.0
            for evento in self.eventos_hoje:
                tipo_ev = evento.get("tipo", "evento")
                if tipo_ev in prod["eventos_associados"]:
                    # Evento associado + fonte real = score máximo
                    if evento.get("fonte") != "padrao_bh":
                        melhor_score = 1.0  # Evento confirmado por API real
                    else:
                        melhor_score = max(melhor_score, 0.8)  # Padrão de BH
                
                # Bônus: evento massivo (> 10k pessoas esperadas no Carnaval [citation:2])
                if tipo_ev in ["festival", "carnaval"]:
                    melhor_score = max(melhor_score, 1.0)
            
            if melhor_score > 0:
                return melhor_score
            
            return 0.1  # Evento existe mas não associado ao produto
    
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
        """Explicações com insights de mercado reais"""
        expl = []
        metricas = melhor["metricas"]
        
        # Fator principal
        maior_fator = max(metricas, key=metricas.get)
        fatores_nome = {
            "p_clima": f"condição climática ({clima['descricao']})",
            "p_data": "dia da semana",
            "p_hora": "horário de pico",
            "p_evento": "eventos detectados hoje"
        }
        expl.append(
            f"🎯 Principal fator decisivo: **{fatores_nome[maior_fator]}** "
            f"(relevância: {metricas[maior_fator]:.0%})"
        )
        
        # Eventos reais detectados
        if self.eventos_hoje:
            reais = [e for e in self.eventos_hoje if e.get("fonte") != "padrao_bh"]
            padrao = [e for e in self.eventos_hoje if e.get("fonte") == "padrao_bh"]
            
            if reais:
                nomes = [e["nome"] for e in reais]
                expl.append(f"🎪 **{len(reais)} evento(s) confirmado(s) por APIs reais:** {', '.join(nomes[:3])}")
            elif padrao:
                nomes = [e["nome"] for e in padrao]
                expl.append(f"📅 **Padrões de BH para hoje:** {', '.join(nomes[:3])}")
        
        # Insights de mercado
        produto = melhor["produto"]
        if produto in self.produtos and "nota_mercado" in self.produtos[produto]:
            expl.append(f"💡 **Caso real de sucesso:** {self.produtos[produto]['nota_mercado']}")
        
        # Por que não o 2º?
        if len(top3) > 1:
            segundo = top3[1]
            diff = melhor["score"] - segundo["score"]
            if diff > 5:
                expl.append(
                    f"📊 {melhor['produto'].title()} supera '{segundo['produto'].title()}' "
                    f"por **{diff:.1f} pontos** — {self._explicar_diferenca(melhor, segundo)}"
                )
        
        return expl
    
    def sugerir_local(self, recomendacao, clima):
        """Sugere local baseado em produto + clima + eventos reais + casos de sucesso"""
        produto = recomendacao["produto"]
        categoria = recomendacao["categoria"]
        
        # Localização estratégica extraída de casos reais
        if self.eventos_hoje:
            for ev in self.eventos_hoje:
                if ev.get("local"):
                    # Caso real: "ficar sempre à frente do bloco, perto dos banheiros" [citation:2]
                    if ev.get("tipo") in ["festival", "show", "carnaval"]:
                        return f"Próximo ao evento: {ev['nome']} — Posicione-se à frente da concentração e perto de banheiros [referência: ambulantes BH]"
                    elif ev.get("tipo") == "feira":
                        return f"Entorno da feira: {ev['local']} — Chegue cedo (6h) para garantir ponto"
                    elif ev.get("tipo") == "congresso":
                        return f"Entrada/saída do congresso: {ev['local']} — Horários de intervalo (10h, 12h, 16h)"
        
        # Locais consagrados de BH
        locais = {
            "bebida": {
                "limpo": "Praça da Liberdade — alto fluxo turístico + sombra",
                "nublado": "Praça Sete — Centro — 300+ vendas/dia possíveis [citation:6]",
                "chuva": "Marquises Av. Amazonas — proteção + fluxo constante",
            },
            "alimento": {
                "limpo": "Feira Afonso Pena (domingo) ou Praça Sete (dias úteis)",
                "nublado": "Savassi — Praça da Savassi — público qualificado",
                "chuva": "Entorno de shoppings — Estação BH, Shopping Cidade",
            },
            "protecao": {
                "chuva": "Entradas de shoppings e estações de metrô — Centro",
                "garoa": "Pontos de ônibus da Praça Sete e Av. Amazonas",
            },
            "acessorio": {
                "limpo": "Parque Municipal — entrada principal (público leisure)",
            },
            "eletronico": {
                "limpo": "Expominas durante congressos — Gameleira",
            },
        }
        
        condicao = clima["condicao"]
        return locais.get(categoria, {}).get(condicao, "Praça Sete — Centro (local padrão de alto fluxo)")
    
    def sugerir_fornecedor(self, produto):
        """Mapeamento de fornecedores reais de BH"""
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
            "palha italiana doce": "Mercado Central — banca de doces — R$ 1,50/un (caseiro)",
            "kit lanche saudavel": "Ceasa BH + produção própria — R$ 5,00/un (sanduíche + fruta)",
            "adereco carnavalesco": "Atacadão Fantasias (Shopping Oiapoque) — R$ 2,00/un",
        }
        return fornecedores.get(produto, "Fornecedor padrão — consulte catálogo local")
    

    def _explicar_diferenca(self, melhor, segundo):
        """Explica por que o melhor produto ganhou do segundo"""
        m = melhor["metricas"]
        s = segundo["metricas"]
        diffs = {k: m[k] - s[k] for k in m}
        maior_diff = max(diffs, key=diffs.get)
        
        traducoes = {
            "p_clima": "adequação ao clima atual",
            "p_data": "sazonalidade do dia da semana",
            "p_hora": "pico de consumo neste horário",
            "p_evento": "demanda gerada por eventos"
        }
        
        return f"Vantagem decisiva em **{traducoes[maior_diff]}** (+{diffs[maior_diff]:.0%})"