import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

CSV = "base_1500_linhas_sao_paulo.csv"
TARGET = "%"

df = pd.read_csv(CSV)
df = df.dropna(subset=[TARGET])
df = df[df[TARGET] >= 0]

features = [
    "Jogos Futebol", "Clima", "Choveu?", "Dia da Semana",
    "Feriado (antes)", "Feriado (depois)", "Trânsito", "TURNO"
]
X = df[features].copy()
y = df[TARGET].astype(float)

numeric = ["Jogos Futebol", "Choveu?", "Feriado (antes)", "Feriado (depois)", "Trânsito"]
categorical = ["Clima", "Dia da Semana", "TURNO"]

preprocess = ColumnTransformer([
    ("num", SimpleImputer(strategy="median"), numeric),
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical)
])

models = {
    "RandomForest": RandomForestRegressor(n_estimators=400, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingRegressor(random_state=42),
    "HistGradientBoosting": HistGradientBoostingRegressor(random_state=42),
    "Ridge": Ridge(alpha=1.0)
}

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

results = {}
best_name, best_score, best_model = None, np.inf, None

for name, model in models.items():
    pipe = Pipeline([("prep", preprocess), ("model", model)])
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    r2 = r2_score(y_test, pred)
    results[name] = {"MAE": mae, "RMSE": rmse, "R2": r2}
    if mae < best_score:
        best_name, best_score, best_model = name, mae, pipe

print("Resultados:")
for k, v in results.items():
    print(k, {m: round(s, 3) for m, s in v.items()})
print("Melhor modelo:", best_name)

joblib.dump(best_model, "modelo_falta_escola_1500.joblib")

# Exemplo de previsão
novo = pd.DataFrame([{
    "Jogos Futebol": 1, "Clima": "Chuvoso", "Choveu?": 1,
    "Dia da Semana": "Sexta", "Feriado (antes)": 1, "Feriado (depois)": 0,
    "Trânsito": 4, "TURNO": "Noite"
}])
print("Previsão de falta (%):", round(best_model.predict(novo)[0], 1))
