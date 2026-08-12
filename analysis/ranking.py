import pandas as pd


def calc_ranking_with_success(data, nb_collectes=None):

    tmp = data.copy()

    # =========================
    # SCORE
    # =========================

    # Conversion numérique
    tmp["Score"] = pd.to_numeric(
        tmp["Score"],
        errors="coerce"
    )

    # Une case Score vide = 0
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
            Nb_succes=("Succes", "sum")
        )
    )

    # =========================
    # NOMBRE TOTAL DE COLLECTES
    # =========================

    if nb_collectes is None:

        # Pour année / historique :
        # nombre de lignes réellement présentes
        result["Nb_total"] = (
            tmp.groupby("Code animal")
            .size()
        )

    else:

        # Pour les 10 dernières collectes :
        # tout le monde est comparé sur les mêmes 10 collectes
        result["Nb_total"] = nb_collectes

    # =========================
    # TAUX DE RÉUSSITE
    # =========================

    result["Taux_reussite"] = (
        result["Nb_succes"]
        / result["Nb_total"]
        * 100
    )

    # =========================
    # TRI
    # =========================

    return result.sort_values(
        "Score_moyen",
        ascending=False
    )
