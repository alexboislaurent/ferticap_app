import pandas as pd


def calc_ranking_with_success(data, total_collectes=None):

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
    # CALCUL PAR BOUC
    # =========================

    result = (
        tmp.groupby("Code animal")
        .agg(
            Score_moyen=("Score", "mean"),
            Nb_succes=("Succes", "sum"),
            Nb_total=("Succes", "size")
        )
    )

    # =========================
    # NOMBRE TOTAL DE COLLECTES
    # =========================

    if total_collectes is not None:

        result["Nb_total"] = total_collectes

        result["Taux_reussite"] = (
            result["Nb_succes"]
            / total_collectes
            * 100
        )

        # Moyenne sur les 10 collectes
        result["Score_moyen"] = (
            result["Score_moyen"]
            * (
                result["Nb_succes"]
                / result["Nb_total"]
            )
        )

    else:

        result["Taux_reussite"] = (
            result["Nb_succes"]
            / result["Nb_total"]
            * 100
        )

    return result.sort_values(
        "Score_moyen",
        ascending=False
    )
