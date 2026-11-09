
import csv
import os
import requests
from datetime import datetime, timezone

API_KEY = os.environ["COINGECKO_API_KEY"]

HEADERS = {
    "x-cg-demo-api-key": API_KEY
}

ARCHIVO = "btc_dominance.csv"
HISTORICO = "btc_dominance_historico.csv"

COLUMNAS = [
    "numero_fila",
    "fecha",
    "btc_price_usd",
    "btc_market_cap_usd",
    "stablecoins_market_cap_usd",
    "altcoins_market_cap_usd",
    "total_market_cap_propio_usd",
    "btc_dominance_propia_pct",
    "stablecoins_dominance_propia_pct",
    "total_volume_26_usd"
]

# Identificadores de CoinGecko de stablecoins conocidas.
STABLECOINS_IDS = {
    "tether",
    "usd-coin",
    "usds",
    "ethena-usde",
    "dai",
    "first-digital-usd",
    "paypal-usd",
    "true-usd",
    "frax",
    "usdd",
    "paxos-standard",
    "gemini-dollar",
    "ripple-usd",
    "global-dollar",
    "usual-usd",
    "crvusd",
    "liquity-usd",
    "reserve-rights-token",
    "stasis-eurs",
    "euro-coin"
}


def obtener_datos():

    # UNA SOLA CONSULTA: las 250 criptomonedas principales
    url = "https://api.coingecko.com/api/v3/coins/markets"

    respuesta = requests.get(
        url,
        headers=HEADERS,
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": 1,
            "sparkline": "false"
        },
        timeout=30
    )

    respuesta.raise_for_status()
    print("Estado HTTP CoinGecko:", respuesta.status_code)
    print("Consulta realizada:", url)
    monedas = respuesta.json()

    if not monedas:
        raise ValueError("CoinGecko no devolvió datos.")

    # Bitcoin
    btc = next(
        (m for m in monedas if m["id"] == "bitcoin"),
        None
    )

    if not btc:
        raise ValueError("No se encontró Bitcoin.")

    precio_btc = float(btc["current_price"])
    capitalizacion_btc = float(btc["market_cap"])

    # Cinco stablecoins principales
    stablecoins = [
        m for m in monedas
        if m["id"] in STABLECOINS_IDS
        and m.get("market_cap") is not None
    ]

    stablecoins = sorted(
        stablecoins,
        key=lambda m: m["market_cap"],
        reverse=True
    )[:5]

    if len(stablecoins) < 5:
        raise ValueError(
            "No se encontraron cinco stablecoins."
        )

    # Veinte altcoins principales, excluyendo BTC y stablecoins
    altcoins = [
        m for m in monedas
        if m["id"] != "bitcoin"
        and m["id"] not in STABLECOINS_IDS
        and m.get("market_cap") is not None
    ][:20]

    if len(altcoins) < 20:
        raise ValueError("No se encontraron veinte altcoins.")

    # Capitalizaciones
    capitalizacion_stablecoins = sum(
        float(m["market_cap"]) for m in stablecoins
    )

    capitalizacion_altcoins = sum(
        float(m["market_cap"]) for m in altcoins
    )

    # Mercado propio: BTC + 5 stablecoins + 20 altcoins
    capitalizacion_total = (
        capitalizacion_btc
        + capitalizacion_stablecoins
        + capitalizacion_altcoins
    )

    dominancia_btc = (
        capitalizacion_btc / capitalizacion_total * 100
    )

    dominancia_stablecoins = (
        capitalizacion_stablecoins
        / capitalizacion_total * 100
    )

    # Volumen de las 26 monedas
    monedas_seleccionadas = [btc] + stablecoins + altcoins

    volumen_total = sum(
        float(m["total_volume"])
        for m in monedas_seleccionadas
        if m.get("total_volume") is not None
    )

    fecha = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return [
        fecha,
        precio_btc,
        capitalizacion_btc,
        capitalizacion_stablecoins,
        capitalizacion_altcoins,
        capitalizacion_total,
        dominancia_btc,
        dominancia_stablecoins,
        volumen_total
    ]


def preparar_csv():

    # Si existe el CSV anterior, conservarlo como histórico.
    if os.path.exists(ARCHIVO):

        with open(
            ARCHIVO, "r", newline="", encoding="utf-8"
        ) as f:
            encabezado = next(csv.reader(f), [])

        if encabezado != COLUMNAS:

            if os.path.exists(HISTORICO):
                raise ValueError(
                    "Ya existe el archivo histórico. "
                    "No se modificó ningún CSV."
                )

            os.replace(ARCHIVO, HISTORICO)

    # Crear el nuevo CSV
    if not os.path.exists(ARCHIVO):
        with open(
            ARCHIVO, "w", newline="", encoding="utf-8"
        ) as f:
            escritor = csv.writer(f)
            escritor.writerow(COLUMNAS)


def guardar_fila(datos):

    preparar_csv()

    with open(
        ARCHIVO, "r", newline="", encoding="utf-8"
    ) as f:
        lector = csv.reader(f)
        encabezado = next(lector, [])

        if encabezado != COLUMNAS:
            raise ValueError("Encabezado CSV incorrecto.")

        cantidad_filas = sum(1 for _ in lector)

    numero_fila = cantidad_filas + 1

    with open(
        ARCHIVO, "a", newline="", encoding="utf-8"
    ) as f:
        escritor = csv.writer(f)
        escritor.writerow([numero_fila] + datos)

    return numero_fila


if __name__ == "__main__":

    try:
        datos = obtener_datos()
        numero = guardar_fila(datos)

        print(
            f"Fila {numero} | {datos[0]} UTC | "
            f"BTC: ${datos[1]:,.2f} | "
            f"Capitalización propia: ${datos[5]:,.0f} | "
            f"Dominancia BTC: {datos[6]:.2f}% | "
            f"Stablecoins: {datos[7]:.2f}%"
        )

    except Exception as e:
        print(f"Error: {e}")
        raise
