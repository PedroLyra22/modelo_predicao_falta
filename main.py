import pandas as pd
import joblib

MODEL = "modelo_falta_escola_1500.joblib"
model = joblib.load(MODEL)

features = [
    "Jogos Futebol", "Clima", "Choveu?", "Dia da Semana",
    "Feriado (antes)", "Feriado (depois)", "Trânsito", "TURNO"
]

def prever_falta(
    jogos_futebol,
    clima,
    choveu,
    dia_da_semana,
    feriado_antes,
    feriado_depois,
    transito,
    turno
):
    entrada = pd.DataFrame([{
        "Jogos Futebol": jogos_futebol,
        "Clima": clima,
        "Choveu?": choveu,
        "Dia da Semana": dia_da_semana,
        "Feriado (antes)": feriado_antes,
        "Feriado (depois)": feriado_depois,
        "Trânsito": transito,
        "TURNO": turno
    }])

    previsao = float(model.predict(entrada[features])[0])
    return round(previsao, 1)

resultado = prever_falta(
    jogos_futebol=0,
    clima="Ensolarado",
    choveu=0,
    dia_da_semana="Quarta",
    feriado_antes=0,
    feriado_depois=0,
    transito=4,
    turno="Noite"
)

print(resultado)