
import csv
import os
import requests
from datetime import datetime, timezone
API_KEY = os.environ["COINGECKO_API_KEY"]

HEADERS = {
    "x-cg-demo-api-key": API_KEY
}
ARCHIVO = "btc_dominance.csv"

COLUMNAS = [
    "numero_fila",
    "fecha",
    "btc_price_usd",
    "btc_market_cap_usd",
    "btc_dominance_pct",
    "total_market_cap_usd",
    "stablecoins_market_cap_usd",
    "stablecoins_dominance_pct",
    "total_volume_24h_usd"
]


def obtener_datos():
    # 1. Datos generales del mercado cripto
    url_global = "https://api.coingecko.com/api/v3/global"
    respuesta = requests.get(
    url_global,
    headers=HEADERS,
    timeout=30)
    respuesta.raise_for_status()
    global_data = respuesta.json()["data"]

    capitalizacion_total = float(
        global_data["total_market_cap"]["usd"]
    )
    volumen_total = float(
        global_data["total_volume"]["usd"]
    )
    dominancia_btc = float(
        global_data["market_cap_percentage"]["btc"]
    )

    # 2. Precio y capitalización de Bitcoin
    url_btc = "https://api.coingecko.com/api/v3/simple/price"
    respuesta = requests.get(
        url_btc,
        headers=HEADERS,
        params={
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_market_cap": "true"
        },
        timeout=30
    )
    respuesta.raise_for_status()
    datos_btc = respuesta.json()["bitcoin"]

    precio_btc = float(datos_btc["usd"])
    capitalizacion_btc = float(datos_btc["usd_market_cap"])

    # 3. Las 10 stablecoins principales por capitalización
    url_stablecoins = (
        "https://api.coingecko.com/api/v3/coins/markets"
    )
    respuesta = requests.get(
        url_stablecoins,
        headers=HEADERS,
        params={
            "vs_currency": "usd",
            "category": "stablecoins",
            "order": "market_cap_desc",
            "per_page": 10,
            "page": 1
        },
        timeout=30
    )
    respuesta.raise_for_status()
    stablecoins = respuesta.json()

    if not stablecoins:
        raise ValueError(
            "CoinGecko no devolvió datos de stablecoins"
        )

    capitalizacion_stablecoins = sum(
        float(moneda["market_cap"])
        for moneda in stablecoins
        if moneda.get("market_cap") is not None
    )

    dominancia_stablecoins = (
        capitalizacion_stablecoins / capitalizacion_total * 100
    )

    fecha = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return [
        fecha,
        precio_btc,
        capitalizacion_btc,
        dominancia_btc,
        capitalizacion_total,
        capitalizacion_stablecoins,
        dominancia_stablecoins,
        volumen_total
    ]


def guardar_fila(datos):
    # Crear el CSV nuevo si todavía no existe
    if not os.path.exists(ARCHIVO):
        with open(ARCHIVO, "w", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            escritor.writerow(COLUMNAS)

    # Comprobar que el archivo tenga las columnas esperadas
    with open(ARCHIVO, "r", newline="", encoding="utf-8") as f:
        lector = csv.reader(f)
        encabezado = next(lector, [])

        if encabezado != COLUMNAS:
            raise ValueError(
                "El CSV existente no tiene las columnas esperadas."
            )

        cantidad_filas = sum(1 for _ in lector)

    numero_fila = cantidad_filas + 1

    with open(ARCHIVO, "a", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow([numero_fila] + datos)


if __name__ == "__main__":
    try:
        datos = obtener_datos()
        guardar_fila(datos)

        print(
            f"Fila {datos[0]} | "
            f"{datos[1]} UTC | "
            f"BTC: ${datos[2]:,.2f} | "
            f"Capitalización BTC: ${datos[3]:,.0f} | "
            f"Dominancia BTC: {datos[4]:.2f}% | "
            f"Stablecoins: ${datos[6]:,.0f}"
        )

    except Exception as e:
        print(f"Error: {e}")
        raise
