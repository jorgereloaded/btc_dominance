import csv
import os
import requests
from datetime import datetime, timezone

ARCHIVO = "btc_dominance.csv"


def obtener_datos():
    # Obtener el precio de Bitcoin desde CoinGecko
    url_precio = "https://api.coingecko.com/api/v3/simple/price"
    respuesta = requests.get(
        url_precio,
        params={"ids": "bitcoin", "vs_currencies": "usd"},
        timeout=30
    )
    respuesta.raise_for_status()
    precio = float(respuesta.json()["bitcoin"]["usd"])

    # Obtener la dominancia de Bitcoin desde CoinGecko
    url_global = "https://api.coingecko.com/api/v3/global"
    respuesta = requests.get(url_global, timeout=30)
    respuesta.raise_for_status()
    datos = respuesta.json()["data"]
    dominancia = float(datos["market_cap_percentage"]["btc"])

    tiempo = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return tiempo, precio, dominancia


def guardar_fila(tiempo, precio, dominancia):
    existe = os.path.exists(ARCHIVO)

    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)

        if not existe or os.path.getsize(ARCHIVO) == 0:
            escritor.writerow([
                "time",
                "btc_price_usd",
                "btc_dominance_pct"
            ])

        escritor.writerow([tiempo, precio, dominancia])


if __name__ == "__main__":
    try:
        tiempo, precio, dominancia = obtener_datos()
        guardar_fila(tiempo, precio, dominancia)

        print(
            f"{tiempo} UTC | BTC: ${precio:,.2f} | "
            f"Dominancia: {dominancia:.2f}%"
        )

    except Exception as e:
        print(f"Error: {e}")
        raise
