import pandas as pd
import string

# === 1. Leer el archivo original ===
df = pd.read_csv("coches_idae.csv")


# === 4. Generar matrículas españolas ===
def generar_matriculas(n):
    letras = [a + b + c for a in string.ascii_uppercase
                        for b in string.ascii_uppercase
                        for c in string.ascii_uppercase]
    matrículas = []
    numero = 0
    for letras_tripleta in letras:
        for i in range(10000):  # 0000 → 9999
            matriculastr = f"{i:04d} {letras_tripleta}"
            matrículas.append(matriculastr)
            if len(matrículas) == n:
                return matrículas
    return matrículas[:n]

df.insert(0, "Matricula", generar_matriculas(len(df)))

# === 5. Guardar a nuevo CSV ===
df.to_csv("coches_procesado.csv", index=False, encoding="utf-8-sig", sep=";")

print(f"Procesado completado. Guardado en coches_procesado.csv con {len(df)} registros.")
