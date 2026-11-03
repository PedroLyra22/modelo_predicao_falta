import datetime
import requests
from typing import Dict, Any, List

# Coordenadas padrão (São Paulo - SP: Centro / Praça da Sé)
DEFAULT_LAT = -23.5505
DEFAULT_LON = -46.6333
DEFAULT_CITY_CODE_CPTEC = 244  # São Paulo no CPTEC/INPE

def get_weather_category(weather_code: int, precipitation: float) -> str:
    """Mapeia os códigos WMO para as categorias do modelo."""
    if precipitation > 0.5 or weather_code in [51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99]:
        return "Chuvoso"
    elif weather_code in [0, 1]:
        return "Ensolarado"
    elif weather_code in [2]:
        return "Parcialmente nublado"
    elif weather_code in [3, 45, 48]:
        return "Nublado"
    elif weather_code >= 50:
        return "Chuvoso"
    return "Ensolarado"

def get_day_of_week_pt(date_obj: datetime.date) -> str:
    days = {
        0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta",
        4: "Sexta", 5: "Sábado", 6: "Domingo"
    }
    return days.get(date_obj.weekday(), "Segunda")

# 1. API Open-Meteo Weather
def fetch_open_weather(date_str: str, lat: float, lon: float) -> Dict[str, Any]:
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&daily=weathercode,precipitation_sum,temperature_2m_max,temperature_2m_min"
            f"&current_weather=true&timezone=America%2FSao_Paulo"
        )
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            daily = data.get("daily", {})
            dates = daily.get("time", [])
            if date_str in dates:
                idx = dates.index(date_str)
                code = daily.get("weathercode", [0])[idx]
                precip = float(daily.get("precipitation_sum", [0.0])[idx] or 0.0)
                temp_max = daily.get("temperature_2m_max", [None])[idx]
                temp_min = daily.get("temperature_2m_min", [None])[idx]
            else:
                curr = data.get("current_weather", {})
                code = curr.get("weathercode", 0)
                precip = 0.0
                temp_max = curr.get("temperature", 24.0)
                temp_min = temp_max - 5.0

            clima = get_weather_category(code, precip)
            return {
                "active": True,
                "clima": clima,
                "choveu": 1 if precip > 0.5 or clima == "Chuvoso" else 0,
                "precipitation_mm": precip,
                "temp_max": temp_max,
                "temp_min": temp_min,
                "api": "Open-Meteo Weather API"
            }
    except Exception as e:
        print(f"Erro Open-Meteo: {e}")
    return {"active": False, "clima": "Ensolarado", "choveu": 0, "precipitation_mm": 0.0, "api": "Open-Meteo Weather API"}

# 2. API BrasilAPI CPTEC / INPE
def fetch_cptec_weather() -> Dict[str, Any]:
    try:
        url = f"https://brasilapi.com.br/api/cptec/v1/clima/previsao/{DEFAULT_CITY_CODE_CPTEC}"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            clima_list = data.get("clima", [])
            desc = clima_list[0].get("condicao_desc", "Parcialmente Nublado") if clima_list else "Nublado"
            return {"active": True, "cptec_desc": desc, "api": "BrasilAPI CPTEC/INPE"}
    except Exception as e:
        print(f"Erro CPTEC: {e}")
    return {"active": False, "cptec_desc": "Normal", "api": "BrasilAPI CPTEC/INPE"}

# 3. API BrasilAPI Feriados Nacionais
def fetch_brasil_api_holidays(date_obj: datetime.date) -> Dict[str, Any]:
    try:
        url = f"https://brasilapi.com.br/api/feriados/v1/{date_obj.year}"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            holidays = {h["date"] for h in resp.json() if "date" in h}
            day_before = (date_obj - datetime.timedelta(days=1)).isoformat()
            day_after = (date_obj + datetime.timedelta(days=1)).isoformat()

            feriado_antes = 1 if day_before in holidays else 0
            feriado_depois = 1 if day_after in holidays else 0

            # Pontes em segundas e sextas
            if date_obj.weekday() == 0 and (date_obj - datetime.timedelta(days=3)).isoformat() in holidays:
                feriado_antes = 1
            elif date_obj.weekday() == 4 and (date_obj + datetime.timedelta(days=3)).isoformat() in holidays:
                feriado_depois = 1

            return {
                "active": True,
                "is_holiday_today": 1 if date_obj.isoformat() in holidays else 0,
                "feriado_antes": feriado_antes,
                "feriado_depois": feriado_depois,
                "api": "BrasilAPI Feriados"
            }
    except Exception as e:
        print(f"Erro BrasilAPI Feriados: {e}")
    return {"active": False, "is_holiday_today": 0, "feriado_antes": 0, "feriado_depois": 0, "api": "BrasilAPI Feriados"}

# 4. API ESPN Soccer Scoreboard (Futebol)
def fetch_espn_soccer(date_obj: datetime.date) -> Dict[str, Any]:
    try:
        date_formatted = date_obj.strftime("%Y%m%d")
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard?dates={date_formatted}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code == 200:
            events = resp.json().get("events", [])
            has_game = 1 if len(events) > 0 else (1 if date_obj.weekday() in [2, 5, 6] else 0)
            return {
                "active": True,
                "jogos_futebol": has_game,
                "qtd_jogos": len(events),
                "api": "ESPN Scoreboard Open API"
            }
    except Exception as e:
        print(f"Erro ESPN: {e}")
    has_fallback = 1 if date_obj.weekday() in [2, 5, 6] else 0
    return {"active": False, "jogos_futebol": has_fallback, "qtd_jogos": 0, "api": "ESPN Scoreboard Open API"}

# 5. API Open-Meteo Air Quality (Monóxido de Carbono e Poluição Veicular)
def fetch_air_quality(lat: float, lon: float) -> Dict[str, Any]:
    try:
        url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=carbon_monoxide,european_aqi"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            curr = resp.json().get("current", {})
            co = float(curr.get("carbon_monoxide", 300.0) or 300.0)
            aqi = int(curr.get("european_aqi", 60) or 60)
            return {"active": True, "co_level": co, "aqi": aqi, "api": "Open-Meteo Air Quality API"}
    except Exception as e:
        print(f"Erro Air Quality: {e}")
    return {"active": False, "co_level": 300.0, "aqi": 60, "api": "Open-Meteo Air Quality API"}

# 6. API Open-Meteo Flood (Risco de Alagamento em Rios Urbanos Tietê/Pinheiros)
def fetch_flood_risk(lat: float, lon: float) -> Dict[str, Any]:
    try:
        url = f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}&daily=river_discharge"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            discharges = resp.json().get("daily", {}).get("river_discharge", [15.0])
            val = float(discharges[0]) if discharges and discharges[0] is not None else 15.0
            return {"active": True, "river_discharge": round(val, 1), "api": "Open-Meteo Flood & Rivers API"}
    except Exception as e:
        print(f"Erro Flood: {e}")
    return {"active": False, "river_discharge": 15.0, "api": "Open-Meteo Flood & Rivers API"}

# 7. API Sunrise-Sunset (Luz Solar e Horários do Turno)
def fetch_sunrise_sunset(lat: float, lon: float) -> Dict[str, Any]:
    try:
        url = f"https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            res = resp.json().get("results", {})
            return {
                "active": True,
                "sunrise": res.get("sunrise"),
                "sunset": res.get("sunset"),
                "api": "Sunrise-Sunset Open API"
            }
    except Exception as e:
        print(f"Erro Sunrise: {e}")
    return {"active": False, "api": "Sunrise-Sunset Open API"}

# 8. API IBGE Localidades
def fetch_ibge_city() -> Dict[str, Any]:
    try:
        url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios/3550308"
        resp = requests.get(url, timeout=4)
        if resp.status_code == 200:
            data = resp.json()
            return {"active": True, "municipio": data.get("nome"), "api": "IBGE Localidades API"}
    except Exception as e:
        print(f"Erro IBGE: {e}")
    return {"active": False, "municipio": "São Paulo", "api": "IBGE Localidades API"}

def calculate_traffic_level(
    date_obj: datetime.date,
    turno: str,
    choveu: int,
    feriado_antes: int,
    co_level: float,
    river_discharge: float
) -> int:
    """Calcula nível de trânsito de 1 a 5 cruzando dia, turno, chuva, poluição e alagamento."""
    weekday = date_obj.weekday()
    if weekday in [5, 6]:
        base = 2
    elif turno in ["Manhã", "Noite"]:
        base = 4 if weekday in [2, 4] else 3
    else:
        base = 3

    if choveu == 1:
        base += 1
    if feriado_antes == 1:
        base += 1
    if co_level > 400.0:
        base += 1
    if river_discharge > 25.0:  # Alerta de cheia nos rios Tietê/Pinheiros
        base += 1

    return max(1, min(5, base))

def get_complete_open_data(
    date_str: str = None,
    lat: float = None,
    lon: float = None,
    turno: str = "Manhã",
    location_query: str = None
) -> Dict[str, Any]:
    """Consulta agregada de 8 APIs abertas."""
    if not date_str:
        date_obj = datetime.date.today()
    else:
        date_obj = datetime.date.fromisoformat(date_str)

    lat = lat if lat is not None else DEFAULT_LAT
    lon = lon if lon is not None else DEFAULT_LON

    # Executa consultas
    w_data = fetch_open_weather(date_obj.isoformat(), lat, lon)
    cptec_data = fetch_cptec_weather()
    h_data = fetch_brasil_api_holidays(date_obj)
    soccer_data = fetch_espn_soccer(date_obj)
    air_data = fetch_air_quality(lat, lon)
    flood_data = fetch_flood_risk(lat, lon)
    sun_data = fetch_sunrise_sunset(lat, lon)
    ibge_data = fetch_ibge_city()

    # Cálculo do trânsito inteligente com base nos dados cruzados
    transito_calculado = calculate_traffic_level(
        date_obj=date_obj,
        turno=turno,
        choveu=w_data["choveu"],
        feriado_antes=h_data["feriado_antes"],
        co_level=air_data.get("co_level", 300.0),
        river_discharge=flood_data.get("river_discharge", 15.0)
    )

    dia_semana = get_day_of_week_pt(date_obj)

    connected_apis = [
        {"name": "Open-Meteo Weather", "status": "online" if w_data["active"] else "fallback", "desc": "Clima, chuva e temperatura"},
        {"name": "BrasilAPI Feriados", "status": "online" if h_data["active"] else "fallback", "desc": "Feriados e pontes de emenda"},
        {"name": "ESPN Scoreboard API", "status": "online" if soccer_data["active"] else "fallback", "desc": "Jogos de futebol no dia"},
        {"name": "Open-Meteo Air Quality", "status": "online" if air_data["active"] else "fallback", "desc": "Monóxido de carbono e poluição veicular"},
        {"name": "Open-Meteo Flood/Rivers", "status": "online" if flood_data["active"] else "fallback", "desc": "Vazão de rios Tietê/Pinheiros (alagamentos)"},
        {"name": "BrasilAPI CPTEC/INPE", "status": "online" if cptec_data["active"] else "fallback", "desc": "Previsão oficial nacional de SP"},
        {"name": "IBGE Cidades API", "status": "online" if ibge_data["active"] else "fallback", "desc": "Dados do município (SP)"},
        {"name": "Sunrise-Sunset API", "status": "online" if sun_data["active"] else "fallback", "desc": "Iluminação solar por turno"}
    ]

    return {
        "date": date_obj.isoformat(),
        "dia_da_semana": dia_semana,
        "clima": w_data["clima"],
        "choveu": w_data["choveu"],
        "precipitation_mm": w_data.get("precipitation_mm", 0.0),
        "feriado_antes": h_data["feriado_antes"],
        "feriado_depois": h_data["feriado_depois"],
        "is_holiday_today": h_data["is_holiday_today"],
        "jogos_futebol": soccer_data["jogos_futebol"],
        "transito": transito_calculado,
        "apis_consultadas": connected_apis,
        "total_apis": len(connected_apis)
    }
