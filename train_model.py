"""
Gera dados de treinamento e treina XGBoost (sem feature names para evitar bugs)
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path
import random
import xgboost as xgb

random.seed(42)
np.random.seed(42)

with open("data/produtos.json", "r") as f:
    produtos = json.load(f)

produtos_lista = list(produtos.keys())
condicoes_clima = ["limpo", "nublado", "chuva", "garoa", "tempestade", "neblina"]
categorias_evento = [
    "show musical", "evento esportivo", "feira de artesanato",
    "feira gastronômica", "congresso corporativo", "evento religioso",
    "festa universitária", "carnaval de rua", "teatro ou comédia",
    "manifestação política", "evento familiar", "evento infantil", "nenhum"
]

linhas = []
for _ in range(5000):
    produto = random.choice(produtos_lista)
    p = produtos[produto]
    clima = random.choice(condicoes_clima)
    temp = random.uniform(15, 38)
    chuva = random.uniform(0, 20) if clima in ["chuva", "tempestade", "garoa"] else 0
    evento_tipo = random.choice(categorias_evento)
    tem_evento = 1 if evento_tipo != "nenhum" else 0
    dia = random.choice(range(7))
    hora = random.choice(range(6, 24))
    preco = p["preco_venda"]
    custo = p["custo"]
    margem = p["margem"] / 100.0
    lucro_unit = preco - custo

    score_base = 0.1
    if clima in p["climas_favoraveis"]: score_base += 0.3
    if dia in p["dias_favoraveis"]: score_base += 0.2
    if hora in p["horarios_pico"]: score_base += 0.3
    if evento_tipo in p["eventos_associados"]: score_base += 0.2

    vendas = max(0, int(score_base * random.uniform(10, 80) + np.random.normal(0, 5)))

    linhas.append({
        "f0": round(temp, 1), "f1": round(chuva, 1), "f2": random.randint(30, 100),
        "f3": dia, "f4": hora, "f5": tem_evento,
        "f6": preco, "f7": custo, "f8": round(margem, 3),
        "vendas": vendas
    })

df = pd.DataFrame(linhas)
df.to_csv("data/training_data.csv", index=False)
print(f"✅ {len(df)} amostras geradas")

X = df[["f0","f1","f2","f3","f4","f5","f6","f7","f8"]].values
y = df["vendas"].values

dtrain = xgb.DMatrix(X, label=y)  # Sem feature_names

model = xgb.train(
    {"max_depth": 6, "learning_rate": 0.1, "objective": "reg:squarederror", "seed": 42, "verbosity": 0},
    dtrain, num_boost_round=100
)

Path("models").mkdir(exist_ok=True)
model.save_model("models/xgboost_model.json")
print("✅ Modelo salvo (sem feature names)")
