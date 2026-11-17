
import csv
import os
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("COINGECKO_API_KEY")

if not API_KEY:
    print("¡ALERTA! La variable COINGECKO_API_KEY está vacía.")
else:
    print("API Key de CoinGecko cargada correctamente.")

HEADERS = {
    "x-cg-demo-api-key": API_KEY
} if API_KEY else {}

ARCHIVO = "btc_dominance.csv"
HISTORICO = "btc_dominance_historico.csv"

COLUMNAS_ANTERIORES = [
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

COLUMNAS = COLUMNAS_ANTERIORES + [
    "btc_open_interest_usd",
    "btc_funding_rate"
]

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


def obtener_derivados():

    open_interest = None
    funding_rate = None

    # Open Interest de BTCUSDT
    try:
        url_oi = "https://fapi.binance.com/futures/data/openInterestHist"

        respuesta_oi = requests.get(
            url_oi,
            params={
                "symbol": "BTCUSDT",
                "period": "5m",
                "limit": 1
            },
            timeout=20
        )

        respuesta_oi.raise_for_status()
        registros = respuesta_oi.json()

        if registros:
            open_interest = float(
                registros[-1]["sumOpenInterestValue"]
            )
            print("Open Interest de Binance obtenido.")
        else:
            print("Binance no devolvió Open Interest.")

    except Exception as e:
        print("AVISO: Error al obtener Open Interest:", e)

    # Funding Rate de BTCUSDT
    try:
        url_funding = "https://fapi.binance.com/fapi/v1/premiumIndex"

        respuesta_funding = requests.get(
            url_funding,
            params={"symbol": "BTCUSDT"},
            timeout=20
        )

        respuesta_funding.raise_for_status()
        datos_funding = respuesta_funding.json()

        funding_rate = float(
            datos_funding["lastFundingRate"]
        )

        print("Funding Rate de Binance obtenido.")

    except Exception as e:
        print("AVISO: Error al obtener Funding Rate:", e)

    return [open_interest, funding_rate]


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
        raise ValueError("No se encontraron cinco stablecoins.")

    # Veinte altcoins principales
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

    # Obtener los dos indicadores de Binance
    derivados = obtener_derivados()

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
    ] + derivados


def preparar_csv():

    if os.path.exists(ARCHIVO):

        with open(
            ARCHIVO, "r", newline="", encoding="utf-8"
        ) as f:
            lector = csv.reader(f)
            encabezado = next(lector, [])
            filas = list(lector)

        if encabezado == COLUMNAS:
            return

        if encabezado == COLUMNAS_ANTERIORES:

            temporal = ARCHIVO + ".tmp"

            with open(
                temporal, "w", newline="", encoding="utf-8"
            ) as f:
                escritor = csv.writer(f)
                escritor.writerow(COLUMNAS)

                for fila in filas:
                    escritor.writerow(fila + ["", ""])

            os.replace(temporal, ARCHIVO)

            print(
                "CSV ampliado conservando todos los registros anteriores."
            )
            return

        raise ValueError(
            "El encabezado del CSV no coincide. "
            "No se modificó ningún archivo."
        )

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
            f"Stablecoins: {datos[7]:.2f}% | "
            f"Open Interest: {datos[9]} | "
            f"Funding Rate: {datos[10]}"
        )

    except Exception as e:
        print(f"Error: {e}")
        raise
