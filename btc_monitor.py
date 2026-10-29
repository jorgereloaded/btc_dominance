import csv
import os
import requests
from datetime import datetime, timezone

ARCHIVO = "btc_dominance.csv"

def obtener_datos():
    # Precio de BTC desde Binance
    r = requests.get(
        "https://api.binance.com/api/v3/ticker/price",
        params={"symbol": "BTCUSDT"},
        timeout=20
    )
    r.raise_for_status()
    precio = float(r.json()["price"])

    # Dominancia desde CoinGecko
    r = requests.get(
        "https://api.coingecko.com/api/v3/global",
        timeout=20
    )
    r.raise_for_status()
    datos = r.json()["data"]
    dominancia = float(datos["market_cap_percentage"]["btc"])

    # Hora UTC
    tiempo = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    return tiempo, precio, dominancia

def guardar_fila(tiempo, precio, dominancia):
    existe = os.path.exists(ARCHIVO)

    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)

        if not existe or os.path.getsize(ARCHIVO) == 0:
            escritor.writerow([
                "time", "btc_price_usd", "btc_dominance_pct"
            ])

        escritor.writerow([tiempo, precio, dominancia])

if __name__ == "__main__":
    try:
        tiempo, precio, dominancia = obtener_datos()
        guardar_fila(tiempo, precio, dominancia)

        print(
            f"{tiempo} UTC | BTC: ${precio:,.2f} "
            f"| Dominancia: {dominancia:.2f}%"
        )
    except Exception as e:
        print(f"Error: {e}")
        raise
