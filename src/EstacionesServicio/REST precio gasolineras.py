import aiohttp
import asyncio
import os
import ssl
import certifi
from datetime import datetime, timedelta

# Configuración
BASE_URL = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestresHist/FiltroCCAA/{date}/{ccaa}"
OUTPUT_DIR = "data"
CCAA_IDS = [1]  # de prueba: Andalucía y Aragón
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 9, 20)  # solo un mes de prueba
MAX_CONCURRENT = 10  # no saturar el servidor
RETRIES = 5

# Semáforo para limitar concurrencia
semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# Crear contexto SSL usando certifi
ssl_context = ssl.create_default_context(cafile=certifi.where())

# ⚠️ Si el error persiste, descomenta esto para ignorar SSL (no recomendado en producción)
# ssl_context = ssl.create_default_context()
# ssl_context.check_hostname = False
# ssl_context.verify_mode = ssl.CERT_NONE


async def fetch_and_save(session, date, ccaa):
    date_str = date.strftime("%d-%m-%Y")
    url = BASE_URL.format(date=date_str, ccaa=f"{ccaa:02d}")
    out_path = os.path.join(OUTPUT_DIR, f"{ccaa:02d}", str(date.year), f"{date.month:02d}")
    os.makedirs(out_path, exist_ok=True)
    file_path = os.path.join(out_path, f"{date_str}.json")
    log_path = os.path.join(OUTPUT_DIR, f"{ccaa:02d}", "log.txt")

    # Si ya existe, no volvemos a pedirlo
    if os.path.exists(file_path):
        return

    for attempt in range(1, RETRIES + 1):
        try:
            async with semaphore:  # limitar concurrencia
                async with session.get(url, timeout=30, ssl=ssl_context) as response:
                    if response.status == 200:
                        text = await response.text()
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(text)
                        print(f"✅ Guardado {file_path}")
                        return
                    else:
                        raise Exception(f"HTTP {response.status}")
        except Exception as e:
            print(f"⚠️ Error {url} (intento {attempt}): {e}")
            if attempt == RETRIES:
                with open(log_path, "a", encoding="utf-8") as log:
                    log.write(f"{date_str}: {e}\n")
            await asyncio.sleep(2 * attempt)  # backoff exponencial


async def process_ccaa(ccaa):
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        date = START_DATE
        while date <= END_DATE:
            await fetch_and_save(session, date, ccaa)
            date += timedelta(days=1)


async def main():
    await asyncio.gather(*(process_ccaa(ccaa) for ccaa in CCAA_IDS))


if __name__ == "__main__":
    asyncio.run(main())
