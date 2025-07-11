import osmnx as ox
import pandas as pd
import numpy as np
import itertools
from shapely.geometry import Point
import pyproj

# === 1. Téléchargement de la carte d'Avignon ===
place_name = "Avignon, Vaucluse, France"
graph = ox.graph_from_place(place_name, network_type='walk')
nodes, edges = ox.graph_to_gdfs(graph)

# === 2. Conversion en coordonnées métriques (Lambert 93) ===
lambert = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:2154", always_xy=True)
nodes[['x', 'y']] = nodes.apply(lambda row: pd.Series(lambert.transform(row['x'], row['y'])), axis=1)

# === 3. Récupération des POIs ===
tags = {
    'amenity': True,
    'tourism': True,
    'shop': True,
    'leisure': True,
    'parking': True
}
pois = ox.features_from_place(place_name, tags)
pois = pois[pois.geometry.type == 'Point'].to_crs(epsg=2154)

# === 4. Fonctions robustes ===
def safe_filter(df, key, value=None):
    if key in df.columns:
        if value is not None:
            return df[df[key] == value]
        else:
            return df[df[key].notnull()]
    return pd.DataFrame(columns=df.columns)

def safe_sample(df, n, random_state=None):
    if len(df) >= n:
        return df.sample(n=n, random_state=random_state)
    elif len(df) > 0:
        print(f" Moins de {n} éléments trouvés pour échantillonnage, on prend tout ({len(df)}).")
        return df
    else:
        print(" Aucun élément trouvé pour l'échantillonnage.")
        return pd.DataFrame(columns=df.columns)

# === 5. Sélection des POIs ===
entries = nodes.sample(n=3, random_state=1)
exits = nodes.sample(n=3, random_state=2)
parkings = safe_sample(safe_filter(pois, 'amenity', 'parking'), 3, random_state=3)

targets = pd.concat([
    safe_filter(pois, 'tourism'),
    safe_filter(pois, 'shop')
]).drop_duplicates()

targets = safe_sample(targets, 10, random_state=4)

# === 6. Attribution des IDs ===
def assign_ids(df, prefix):
    df = df.copy()
    df['id'] = [f"{prefix}{i+1}" for i in range(len(df))]
    return df

entries = assign_ids(entries, "E")
exits = assign_ids(exits, "S")
parkings = assign_ids(parkings, "P")
targets = assign_ids(targets, "D")

# === 7. Fusion dans un seul tableau de positions ===
positions = pd.concat([
    entries[['id', 'x', 'y']],
    exits[['id', 'x', 'y']],
    parkings[['id']].assign(x=parkings.geometry.x, y=parkings.geometry.y),
    targets[['id']].assign(x=targets.geometry.x, y=targets.geometry.y)
]).set_index('id')

# === 8. Génération des arcs (TEST.csv) ===
def euclidean_ms(p1, p2, speed_kmh):
    speed_mps = speed_kmh * 1000 / 3600
    dist = np.linalg.norm(p1 - p2)
    return int(round(dist / speed_mps * 1000)) + 1

I = [i for i in positions.index if i.startswith("E")]
O = [i for i in positions.index if i.startswith("S")]
P = [i for i in positions.index if i.startswith("P")]
D = [i for i in positions.index if i.startswith("D")]
vr = 50  # km/h
vp = 7   # km/h

arcs = []

# Arcs routiers
for i, j in itertools.product(I, P):
    c = euclidean_ms(positions.loc[i], positions.loc[j], vr)
    arcs.append([i, j, c])
for i, j in itertools.product(P, O):
    c = euclidean_ms(positions.loc[i], positions.loc[j], vr)
    arcs.append([i, j, c])
for i, j in itertools.permutations(P, 2):
    c = euclidean_ms(positions.loc[i], positions.loc[j], vr)
    arcs.append([i, j, c])

# Arcs piétons
for i, j in itertools.product(P, D):
    c = euclidean_ms(positions.loc[i], positions.loc[j], vp)
    arcs.append([i, j, c])
for i, j in itertools.permutations(D, 2):
    c = euclidean_ms(positions.loc[i], positions.loc[j], vp)
    arcs.append([i, j, c])
for i, j in itertools.product(D, P):
    c = euclidean_ms(positions.loc[i], positions.loc[j], vp)
    arcs.append([i, j, c])

# === 9. Sauvegarde ===
positions.reset_index().to_csv("positions.csv", index=False)
pd.DataFrame(arcs, columns=["Depart", "Arrivee", "Cout"]).to_csv("TEST.csv", index=False)
print(" Fichiers 'positions.csv' et 'TEST.csv' générés.")
