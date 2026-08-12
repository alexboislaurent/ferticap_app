import pandas as pd


def calc_ranking_with_success(data, nb_collectes=None):

    data = data.copy()

    # Score vide = 0
    data["Score"] = pd.to_numeric(
        data["Score"],
        errors="coerce"
    ).fillna(0)

    # Réussite = comportement 2, 3 ou 4
    data["Succes"] = data["Comportement"].isin([2, 3, 4])

    # =========================
    # RANKING
    # =========================

    result = (
        data.groupby("Code animal")
        .agg(
            Score_total=("Score", "sum"),
            Nb_succes=("Succes", "sum")
        )
    )

    # 10 dernières collectes
    if nb_collectes is not None:
        result["Nb_total"] = nb_collectes

    # Année / historique
    else:
        result["Nb_total"] = (
            data.groupby("Code animal")
            .size()
        )

    # Taux de réussite
    result["Taux_reussite"] = (
        result["Nb_succes"]
        / result["Nb_total"]
        * 100
    )

    return result.sort_values(
        "Score_total",
        ascending=False
    )
