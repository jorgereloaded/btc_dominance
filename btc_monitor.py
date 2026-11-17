
import csv
import os
import requests
from datetime import datetime, timezone

API_KEY = os.environ.get("COINGECKO_API_KEY")
COINALYZE_API_KEY = os.environ.get("COINALYZE_API_KEY")

if not API_KEY:
    print("¡ALERTA! La variable COINGECKO_API_KEY está vacía.")
else:
    print("API Key de CoinGecko cargada correctamente.")

if not COINALYZE_API_KEY:
    print("¡ALERTA! La variable COINALYZE_API_KEY está vacía.")
else:
    print("API Key de Coinalyze cargada correctamente.")

HEADERS = {
    "x-cg-demo-api-key": API_KEY
} if API_KEY else {}

COINALYZE_HEADERS = {
    "api_key": COINALYZE_API_KEY
} if COINALYZE_API_KEY else {}

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

# Siete contratos perpetuos de BTC seleccionados
SIMBOLOS_COINALYZE = [
    "BTCUSDT_PERP.A",  # Binance
    "BTCUSDT_PERP.3",  # OKX
    "BTC-PERPETUAL.2", # Deribit
    "BTC.H",           # Hyperliquid
    "pf_xbtusd.K"      # Kraken
]


def obtener_derivados():

    open_interest_total = None
    funding_rate_ponderado = None

    if not COINALYZE_API_KEY:
        print("No se pueden consultar derivados: falta la API Key.")
        return [None, None]

    simbolos = ",".join(SIMBOLOS_COINALYZE)

    # Open Interest de los siete exchanges, convertido a USD
    datos_oi = {}

    try:
        url_oi = "https://api.coinalyze.net/v1/open-interest"

        respuesta_oi = requests.get(
            url_oi,
            headers=COINALYZE_HEADERS,
            params={
                "symbols": simbolos,
                "convert_to_usd": "true"
            },
            timeout=30
        )

        print("Estado HTTP Coinalyze Open Interest:",
              respuesta_oi.status_code)

        respuesta_oi.raise_for_status()

        registros_oi = respuesta_oi.json()

        print("\n--- OPEN INTEREST POR EXCHANGE ---")

        for simbolo in SIMBOLOS_COINALYZE:
            if simbolo in {
                r.get("symbol") for r in registros_oi
            }:
                print(simbolo, "| OK")
            else:
                print(simbolo, "| SIN DATOS")
                
        for registro in registros_oi:
            simbolo = registro.get("symbol")
            valor = registro.get("value")

            if simbolo and valor is not None:
                datos_oi[simbolo] = float(valor)

        if datos_oi:
            open_interest_total = sum(datos_oi.values())

            print(
                "Open Interest obtenido:",
                len(datos_oi),
                "de",
                len(SIMBOLOS_COINALYZE),
                "exchanges."
            )
        else:
            print("Coinalyze no devolvió valores de Open Interest.")

    except Exception as e:
        print("AVISO: Error al obtener Open Interest:", e)

    # Funding Rate actual de los siete exchanges
    try:
        url_funding = "https://api.coinalyze.net/v1/funding-rate"

        respuesta_funding = requests.get(
            url_funding,
            headers=COINALYZE_HEADERS,
            params={
                "symbols": simbolos
            },
            timeout=30
        )

        print("Estado HTTP Coinalyze Funding Rate:",
              respuesta_funding.status_code)

        respuesta_funding.raise_for_status()

        registros_funding = respuesta_funding.json()
        
        print("\n--- FUNDING RATE POR EXCHANGE ---")

        for simbolo in SIMBOLOS_COINALYZE:
            if simbolo in {
                r.get("symbol") for r in registros_funding
            }:
                print(simbolo, "| OK")
            else:
                print(simbolo, "| SIN DATOS")
        
        suma_ponderada = 0.0
        suma_open_interest = 0.0
        exchanges_ponderados = 0

        for registro in registros_funding:

            simbolo = registro.get("symbol")
            funding = registro.get("value")

            # Solo ponderamos cuando tenemos ambos datos
            if (
                simbolo in datos_oi
                and funding is not None
                and datos_oi[simbolo] > 0
            ):
                oi = datos_oi[simbolo]
                funding = float(funding)

                suma_ponderada += funding * oi
                suma_open_interest += oi
                exchanges_ponderados += 1

        if suma_open_interest > 0:

            funding_rate_ponderado = (
                suma_ponderada / suma_open_interest
            )

            print(
                "Funding Rate ponderado obtenido:",
                exchanges_ponderados,
                "exchanges."
            )

        else:
            print(
                "No se pudo calcular el Funding Rate ponderado."
            )

    except Exception as e:
        print("AVISO: Error al obtener Funding Rate:", e)

    return [
        open_interest_total,
        funding_rate_ponderado
    ]


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

    # Obtener Open Interest y Funding Rate de Coinalyze
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
