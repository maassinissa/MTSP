
# pour l'instance d'avignon
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
print("\n Lancement résolution avec les données Avignon (testC.py)")

index = next_index("tests", "TEST_", ".csv")
shutil.copy("TEST.csv", f"tests/TEST_{index}.csv")
shutil.copy("positions.csv", f"tests/positions_{index}.csv")

# === Exécution Julia ===
print(" Lancement Julia ...")
start_time = time.perf_counter()
try:
    subprocess.run([
        "julia", "-e",
        'cd("C:/Users/TRETEC/Contacts/Desktop/MTSP/MTSP"); include("MTSP.jl")'
    ], check=True)
    print(" Julia terminé.")
except Exception as e:
    print(f" Julia a échoué : {e}")

elapsed_ms = int((time.perf_counter() - start_time) * 1000)
print(f" Temps : {elapsed_ms} ms")

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
print(f" Résultat loggé dans {log_file}")


""" (pour plusieurs instances)
import numpy as np
import pandas as pd
import itertools
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


# === Paramètres de base ===
largeur_carre = 100_000
vr = 50 * 1_000_000 / 3600
vp = 7 * 1_000_000 / 3600
marge_percent = 0.15  # 15%
taille = largeur_carre
marge = marge_percent * taille


# === Fichier de log ===
log_file = os.path.join("C:/Users/TRETEC/Contacts/Desktop/MTSP/MTSP", "logefile.csv")
if not os.path.exists(log_file):
    pd.DataFrame(columns=["index", "entrées", "sorties", "parkings", "objectifs", "noeuds_total", "temps_execution_ms"]).to_csv(log_file, index=False)


# === Boucles sur les configurations ===
for n_entrees in range(1, 6):
    for n_sorties in range(1, 6):
        for n_parkings in range(1, 4):
            for n_objectifs in range(3, 21):
                print(f"\n Instance : E={n_entrees} S={n_sorties} P={n_parkings} D={n_objectifs}")
               
                I = [f"E{i}" for i in range(1, n_entrees + 1)]
                O = [f"S{i}" for i in range(1, n_sorties + 1)]
                P = [f"P{i}" for i in range(1, n_parkings + 1)]
                D = [f"D{i}" for i in range(1, n_objectifs + 1)]
                V = I + O + P + D


                # === Positionnement des noeuds ===
                def random_bord_position():
                    côté = np.random.choice(["haut", "bas", "gauche", "droite"])
                    if côté == "haut":
                        return np.array([np.random.uniform(0, taille), taille - np.random.uniform(0, marge)])
                    elif côté == "bas":
                        return np.array([np.random.uniform(0, taille), np.random.uniform(0, marge)])
                    elif côté == "gauche":
                        return np.array([np.random.uniform(0, marge), np.random.uniform(0, taille)])
                    else:
                        return np.array([taille - np.random.uniform(0, marge), np.random.uniform(0, taille)])


                positions = {}
                for e in I + O:
                    positions[e] = random_bord_position()
                centre_min = marge
                centre_max = taille - marge
                for v in P + D:
                    positions[v] = np.random.rand(2) * (centre_max - centre_min) + centre_min


                # === Arcs & Coûts ===
                arcs = []
                for i in I:
                    for p in P:
                        arcs.append((i, p))
                for p in P:
                    for o in O:
                        arcs.append((p, o))
                for p1, p2 in itertools.permutations(P, 2):
                    arcs.append((p1, p2))
                for p in P:
                    for d in D:
                        arcs.append((p, d))
                for d1, d2 in itertools.permutations(D, 2):
                    arcs.append((d1, d2))
                for d in D:
                    for p in P:
                        arcs.append((d, p))


                data = []
                for (i, j) in arcs:
                    dist = np.linalg.norm(positions[i] - positions[j])
                    vitesse = vr if (i in I and j in P) or (i in P and j in O) or (i in P and j in P) else vp
                    temps_ms = int(round((dist / vitesse) * 1000)) + 1
                    data.append([i, j, temps_ms])


                df = pd.DataFrame(data, columns=["Depart", "Arrivee", "Cout"])
                df.to_csv("TEST.csv", index=False)
                pd.DataFrame([(k, *v) for k, v in positions.items()],
                            columns=["Noeud", "x", "y"]).to_csv("positions.csv", index=False)


                index = next_index("tests", "TEST_", ".csv")
                shutil.copy("TEST.csv", f"tests/TEST_{index}.csv")
                shutil.copy("positions.csv", f"tests/positions_{index}.csv")


                # === Exécution Julia ===
                print(" Lancement Julia ...")
                start_time = time.perf_counter()
                try:
                    subprocess.run([
                        "julia", "-e",
                        'cd("C:/Users/TRETEC/Contacts/Desktop/MTSP/MTSP"); include("MTSP.jl")'
                    ], check=True)
                    print(" Julia terminé.")
                except Exception as e:
                    print(f" Julia a échoué : {e}")
                    continue  # passer à l’instance suivante


                elapsed_ms = int((time.perf_counter() - start_time) * 1000)
                print(f"⏱ Temps : {elapsed_ms} ms")


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
                    continue


                # === Affichage graphique ===
                positions_df = pd.read_csv(f"tests/positions_{index}.csv")
                positions = {row["Noeud"]: np.array([row["x"], row["y"]]) for _, row in positions_df.iterrows()}
                df = pd.read_csv(f"tests/TEST_{index}.csv")
                data = df.to_records(index=False)


                fig, ax = plt.subplots(figsize=(10, 10))
                couleurs = {**{v: 'green' for v in I}, **{v: 'red' for v in O}, **{v: 'blue' for v in P}, **{v: 'orange' for v in D}}


                for v, pos in positions.items():
                    ax.plot(pos[0], pos[1], 'o', color=couleurs[v], markersize=10)
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
                ax.set_xlim(0, largeur_carre + 10_000)
                ax.set_ylim(0, largeur_carre + 10_000)
                ax.set_aspect('equal')
                plt.grid(True)
                plt.tight_layout()
                plt.savefig(f"resultats/graphe_{index}.png")
                plt.close()


                # === Log CSV ===
                ligne = {
                    "index": index,
                    "entrées": n_entrees,
                    "sorties": n_sorties,
                    "parkings": n_parkings,
                    "objectifs": n_objectifs,
                    "noeuds_total": len(V),
                    "temps_execution_ms": elapsed_ms
                }


                df_log = pd.read_csv(log_file)
                df_log = pd.concat([df_log, pd.DataFrame([ligne])], ignore_index=True)
                df_log.to_csv(log_file, index=False)
                print(f" Résultat loggé dans {log_file}")
"""