import pandas as pd


def calc_ranking_with_success(data):

    tmp = data.copy()

    # =========================
    # SCORE
    # =========================

    tmp["Score"] = pd.to_numeric(
        tmp["Score"],
        errors="coerce"
    )

    # Case Score vide = 0
    tmp["Score"] = tmp["Score"].fillna(0)

    # =========================
    # SUCCÈS
    # =========================

    tmp["Succes"] = (
        tmp["Comportement"].isin([2, 3, 4])
    )

    # =========================
    # RANKING
    # =========================

    result = (
        tmp.groupby("Code animal")
        .agg(
            Score_moyen=("Score", "mean"),
            Nb_succes=("Succes", "sum")
        )
    )

    return result.sort_values(
        "Score_moyen",
        ascending=False
    )
