from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os

# URL de la web
url = "https://coches.idae.es/base-datos/marca-y-modelo"

# Configuración para Edge
options = webdriver.EdgeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Edge(options=options)
wait = WebDriverWait(driver, 15)

# Nombre del archivo CSV
csv_file = "coches_idae.csv"

# Si existe, lo borramos para empezar de cero
if os.path.exists(csv_file):
    os.remove(csv_file)

# Lista de motorizaciones (value, nombre)
motorizaciones = [
    ("11", "Autonomía extendida"),
    ("9", "Bioetanol"),
    ("6", "Eléctricos puros"),
    ("7", "Gas natural"),
    ("8", "Gases licuados del petróleo (GLP)"),
    ("2", "Gasóleo"),
    ("1", "Gasolina"),
    ("4", "Híbridos de gasóleo"),
    ("3", "Híbridos de gasolina"),
    ("12", "Híbridos enchufables"),
    ("5", "Pila de combustible"),
]

# === Bucle por cada motorización ===
for value, nombre_motor in motorizaciones:
    print(f"🔄 Procesando motorización: {nombre_motor}")

    driver.get(url)

    # Seleccionar motorización
    select_motor = wait.until(EC.presence_of_element_located((By.ID, "motorizacion")))
    Select(select_motor).select_by_value(value)
    time.sleep(1)

    # Pulsar "Buscar"
    buscar_btn = wait.until(EC.element_to_be_clickable(
        (By.XPATH, "//button[contains(text(),'Buscar')]")
    ))
    buscar_btn.click()
    time.sleep(2)

    # Seleccionar 100 resultados por página
    select_element = wait.until(EC.presence_of_element_located((By.NAME, "datos_wltp_length")))
    Select(select_element).select_by_value("100")
    time.sleep(2)

    pagina = 1
    while True:
        print(f"📑 {nombre_motor} - página {pagina}...")

        # Esperar a que la tabla esté cargada
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#datos_wltp tbody tr")))

        data = []
        filas = driver.find_elements(By.CSS_SELECTOR, "#datos_wltp tbody tr")

        for i in range(len(filas)):
            try:
                # Rebuscar la fila en cada iteración para evitar "stale element"
                celdas = driver.find_elements(By.CSS_SELECTOR, "#datos_wltp tbody tr")[i].find_elements(By.TAG_NAME, "td")
                if len(celdas) == 6:
                    modelo = celdas[0].text.strip()
                    clasificacion = ""
                    try:
                        img = celdas[1].find_element(By.TAG_NAME, "img")
                        clasificacion = img.get_attribute("title")
                    except:
                        clasificacion = ""
                    consumo_min = celdas[2].text.strip()
                    consumo_max = celdas[3].text.strip()
                    emisiones_min = celdas[4].text.strip()
                    emisiones_max = celdas[5].text.strip()

                    data.append([
                        modelo, clasificacion, consumo_min, consumo_max,
                        emisiones_min, emisiones_max, nombre_motor
                    ])
            except Exception as e:
                print(f"⚠️ Fila {i} saltada por error: {e}")
                continue

        # Guardar en CSV
        df_temp = pd.DataFrame(data, columns=[
            "Modelo", "Clasificación Energética",
            "Consumo Mínimo", "Consumo Máximo",
            "Emisiones Mínimo", "Emisiones Máximo",
            "Motorización"
        ])
        with open(csv_file, "a", encoding="utf-8-sig", newline="") as f:
            df_temp.to_csv(f, header=not os.path.exists(csv_file), index=False)

        print(f"✅ Guardados {len(df_temp)} registros")

        # Pasar a la siguiente página
        next_button = driver.find_element(By.ID, "datos_wltp_next")
        if "disabled" in next_button.get_attribute("class"):
            print(f"🏁 Última página de {nombre_motor}.")
            break
        else:
            next_link = next_button.find_element(By.TAG_NAME, "a")
            next_link.click()
            pagina += 1
            time.sleep(1.5)

print("💾 Scraping completado. Todo guardado en coches_idae.csv")
driver.quit()
