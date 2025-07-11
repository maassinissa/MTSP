Projet MTSP 
Ce projet consiste à résoudre un problème de cheminement optimal appelé MTSP . Il utilise des données de la ville d’Avignon via OpenStreetMap ainsi que des instances générées aléatoirement. Le but est de calculer les trajets optimaux en fonction de différentes configurations de nœuds (entrées, sorties, parkings, objectifs).
Explication des fichiers et dossiers

  ....testC.py

Ce script est utilisé pour générer une instance réelle sur la ville d’Avignon. Il sélectionne aléatoirement des entrées, sorties, parkings et objectifs à partir des données géographiques et génère deux fichiers :

positions.csv : contient les coordonnées des nœuds (E, S, P, D)

TEST.csv : contient les arcs possibles entre les nœuds avec leur coût (temps de trajet)


 ...test.py


Ce script exécute l’algorithme Julia pour résoudre le problème et visualiser le résultat.

Il contient deux blocs de code :

 Un actif qui utilise les données Avignon (positions.csv + TEST.csv)

 Un commenté qui génère plein d’instances aléatoires pour faire des tests automatiques

Il exécute Julia via MTSP.jl, récupère le chemin.txt, puis trace le graphe final avec le chemin optimal en rouge.



...MTSP.jl



C’est le programme principal en Julia qui résout mathématiquement le MTSP avec des contraintes. Il lit positions.csv et TEST.csv, calcule le chemin optimal, puis l’écrit dans chemin.txt.




...positions.csv



Contient les coordonnées (x, y) de chaque nœud :

E : entrées

S : sorties

P : parkings

D : objectifs



 ...  TEST.csv


Contient la liste des arcs entre les nœuds et le coût associé (en millisecondes).

 ... chemin.txt


Fichier texte généré automatiquement par le programme Julia, indiquant le chemin optimal sous forme de séquence de nœuds.


 ...logefile.csv


Journal (log) des différentes instances testées avec leurs paramètres et temps d’exécution.

  ...d.lp


Fichier contenant le modèle linéaire (format LP), utile pour le debug ou l’analyse mathématique du problème.


Dossiers


 ... tests


Contient les sauvegardes de toutes les instances générées, sous forme :

positions_1.csv, positions_2.csv, ...

TEST_1.csv, TEST_2.csv, …



...résultats


Contient les résultats graphiques et textuels :

graphe_X.png : graphe avec le chemin optimal en rouge

resultat_X.txt : copie du chemin.txt pour chaque instance
















