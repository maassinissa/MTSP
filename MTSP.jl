using JuMP
using Cbc
using CSV
using DataFrames

# Chargement des données 
df = CSV.read("TEST.csv", DataFrame)
# Détection automatique des ensembles à partir du fichier CSV
V = unique(vcat(df.Depart, df.Arrivee)) |> sort
I = filter(x -> startswith(x, "E"), V)  # Entrées
O = filter(x -> startswith(x, "S"), V)  # Sorties
P = filter(x -> startswith(x, "P"), V)  # Parkings
D = filter(x -> startswith(x, "D"), V)  # Objectifs (commerces)

K = 1:(2 * length(D) + 5)

# Définir les arcs et les coûts
E_all = [(row.Depart, row.Arrivee) for row in eachrow(df)]
c = Dict((row.Depart, row.Arrivee) => row.Cout for row in eachrow(df))

# Arcs piétons et routiers
E_pieton = [(i,j) for (i,j) in E_all if (i in P && j in D) || (i in D && j in D) || (i in D && j in P)]
E_routier = [(i,j) for (i,j) in E_all if (i in I && j in P) || (i in P && j in O) || (i in P && j in P)]
E = union(E_pieton, E_routier)

# Définition du modèle 
model = Model(Cbc.Optimizer)
set_silent(model)

@variable(model, y[i in V, j in V, k in K], Bin)
@variable(model, x[i in V, j in V, k in K], Bin)

#  Fonction objectif 
@objective(model, Min, sum(c[(i,j)] * y[i,j,k] for (i,j) in E, k in K if haskey(c, (i,j))))

# Contraintes 

@constraint(model, [k in K], sum(y[i,j,k] for (i,j) in E) <= 1)

@constraint(model, sum(y[i,j,1] for i in I, j in P if (i,j) in E) == 1)
@constraint(model, sum(y[i,j,k] for i in I, j in P, k in 2:length(K) if (i,j) in E) == 0)
@constraint(model, sum(y[i,j,k] for i in P, j in O, k in K if (i,j) in E) == 1)

@constraint(model, [i in setdiff(V, union(I, O)), k in 1:(length(K)-1)],
    sum(y[j,i,k] for j in V if (j,i) in E) == sum(y[i,j,k+1] for j in V if (i,j) in E))

@constraint(model, [i in setdiff(V, union(I, O)), k in 1:(length(K)-1)],
    sum(x[j,i,k] for j in V if (j,i) in E_routier) == sum(x[i,j,k+1] for j in V if (i,j) in E_routier))

@constraint(model, [d in D], sum(y[i,d,k] for i in V, k in K if (i,d) in E_pieton) == 1)
@constraint(model, [(i,j) in E_pieton, k in K], x[i,j,k] == 0)
@constraint(model, [(i,j) in E_routier], sum(y[i,j,k] for k in K) == sum(x[i,j,k] for k in K))

for p in P
    @constraint(model,
        sum(y[p, d, k] for d in D, k in K if (p, d) in E_pieton) ==
        sum(y[d, p, k] for d in D, k in K if (d, p) in E_pieton)
    )
end



#  Résolution 
optimize!(model)
status = termination_status(model)
println("\nStatut de résolution : ", status)

if status == MOI.OPTIMAL || status == MOI.FEASIBLE_POINT
    println("Valeur optimale (temps total de déplacement) : ", objective_value(model))

    trajet = Dict{Int, Tuple{String,String}}()
    for k in K, i in V, j in V
        if haskey(c, (i,j)) && value(y[i,j,k]) > 0.5
            trajet[k] = (i, j)
        end
    end

    trajet_ordre = sort(collect(trajet), by = x -> x[1])
    println("\nChemin optimal utilisé par l’agent :")
    for (k, (i, j)) in trajet_ordre
        println("Étape $k : $i → $j")
    end
    println("\nNombre d’étapes utilisées : ", length(trajet_ordre))

    visites_D = Set{String}()
    for (_, (_, j)) in trajet_ordre
        if j in D
            push!(visites_D, j)
        end
    end
    println("\nTous les commerces visités ? ", visites_D == Set(D))
else
    println("Aucune solution réalisable trouvée. Vérifie les données ou les contraintes.")
end
#  Sauvegarde du chemin optimal dans chemin.txt 

open("chemin.txt", "w") do io
    for (k, (i, j)) in trajet_ordre
        println(io, "Étape $k : $i → $j")
    end
end

println(" Le chemin optimal a été enregistré dans chemin.txt.")

