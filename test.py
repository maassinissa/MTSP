import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import shutil
import subprocess
import time

# === Création des dossiers ===
os.makedirs("tests", exist_ok=True)
os.makedirs("resultats", exist_ok=True)

def next_index(folder, prefix, ext):
    files = [f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(ext)]
    nums = [int(f.replace(prefix, "").replace(ext, "")) for f in files if f.replace(prefix, "").replace(ext, "").isdigit()]
    return max(nums, default=0) + 1

# === Paramètres ===
vr = 50 * 1_000_000 / 3600
vp = 7 * 1_000_000 / 3600

# === Log file ===
log_file = os.path.join("C:/Users/TRETEC/Contacts/Desktop/MTSP/MTSP", "logefile.csv")
if not os.path.exists(log_file):
    pd.DataFrame(columns=["index", "entrées", "sorties", "parkings", "objectifs", "noeuds_total", "temps_execution_ms"]).to_csv(log_file, index=False)

# === Utilisation des fichiers existants de testC.py ===
print("\n🔁 Lancement résolution avec les données Avignon (testC.py)")

index = next_index("tests", "TEST_", ".csv")
shutil.copy("TEST.csv", f"tests/TEST_{index}.csv")
shutil.copy("positions.csv", f"tests/positions_{index}.csv")

# === Exécution Julia ===
print("⏳ Lancement Julia ...")
start_time = time.perf_counter()
try:
    subprocess.run([
        "julia", "-e",
        'cd("C:/Users/TRETEC/Contacts/Desktop/MTSP/MTSP"); include("MTSP.jl")'
    ], check=True)
    print("✅ Julia terminé.")
except Exception as e:
    print(f"❌ Julia a échoué : {e}")

elapsed_ms = int((time.perf_counter() - start_time) * 1000)
print(f"⏱️ Temps : {elapsed_ms} ms")

# === Lecture chemin optimal ===
chemin_optimal = []
chemin_file = "chemin.txt"
result_file = f"resultats/resultat_{index}.txt"

if os.path.exists(chemin_file):
    with open(chemin_file, "r", encoding="utf-8") as f:
        for line in f:
            if "→" in line:
                try:
                    left, right = line.strip().split("→")
                    depart = left.split(":")[-1].strip()
                    arrivee = right.strip()
                    chemin_optimal.append((depart, arrivee))
                except:
                    print("Erreur lecture chemin.")
    shutil.copy(chemin_file, result_file)
else:
    print("Pas de chemin.txt généré.")
    exit()

# === Affichage graphique ===
positions_df = pd.read_csv(f"tests/positions_{index}.csv")
positions = {row["id"]: np.array([row["x"], row["y"]]) for _, row in positions_df.iterrows()}
df = pd.read_csv(f"tests/TEST_{index}.csv")
data = df.to_records(index=False)

fig, ax = plt.subplots(figsize=(10, 10))

# Détection des types de noeuds
I = [v for v in positions if v.startswith("E")]
O = [v for v in positions if v.startswith("S")]
P = [v for v in positions if v.startswith("P")]
D = [v for v in positions if v.startswith("D")]
couleurs = {**{v: 'green' for v in I}, **{v: 'red' for v in O}, **{v: 'blue' for v in P}, **{v: 'orange' for v in D}}

for v, pos in positions.items():
    ax.plot(pos[0], pos[1], 'o', color=couleurs.get(v, 'black'), markersize=10)
    ax.text(pos[0] + 1000, pos[1] + 1000, v, fontsize=9)

for i, j, cout in data:
    pos_i = positions[i]
    pos_j = positions[j]
    is_optimal = (i, j) in chemin_optimal
    color = 'red' if is_optimal else 'gray'
    lw = 2 if is_optimal else 0.5
    ax.annotate("", xy=pos_j, xytext=pos_i, arrowprops=dict(arrowstyle="->", color=color, lw=lw))
    mx, my = (pos_i + pos_j) / 2
    ax.text(mx, my, f"{cout} ms", fontsize=7)

ax.set_title("Graphe avec chemin optimal (rouge)")
ax.set_aspect('equal')
plt.grid(True)
plt.tight_layout()
plt.savefig(f"resultats/graphe_{index}.png")
plt.close()

# === Log CSV ===
ligne = {
    "index": index,
    "entrées": len(I),
    "sorties": len(O),
    "parkings": len(P),
    "objectifs": len(D),
    "noeuds_total": len(positions),
    "temps_execution_ms": elapsed_ms
}

df_log = pd.read_csv(log_file)
df_log = pd.concat([df_log, pd.DataFrame([ligne])], ignore_index=True)
df_log.to_csv(log_file, index=False)
print(f"📝 Résultat loggé dans {log_file}")
