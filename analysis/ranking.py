import pandas as pd


def calc_ranking_with_success(data, nb_collectes=None):

    tmp = data.copy()

    # =========================
    # SCORE
    # =========================

    tmp["Score"] = pd.to_numeric(
        tmp["Score"],
        errors="coerce"
    ).fillna(0)

    # =========================
    # SUCCÈS
    # =========================

    tmp["Succes"] = (
        tmp["Comportement"].isin([2, 3, 4])
    )

    # =========================
    # CAS RANKING 10 DERNIÈRES COLLECTES
    # =========================

    if nb_collectes is not None:

        # Tous les boucs présents dans les données
        boucs = tmp["Code animal"].dropna().unique()

        # Score total réellement obtenu
        scores = (
            tmp.groupby("Code animal")["Score"]
            .sum()
        )

        # Nombre de réussites
        succes = (
            tmp.groupby("Code animal")["Succes"]
            .sum()
        )

        result = pd.DataFrame(index=boucs)

        result["Score_moyen"] = (
            scores / nb_collectes
        )

        result["Nb_succes"] = (
            succes
            .reindex(boucs)
            .fillna(0)
        )

        result["Nb_total"] = nb_collectes

    # =========================
    # ANNÉE / HISTORIQUE
    # =========================

    else:

        result = (
            tmp.groupby("Code animal")
            .agg(
                Score_moyen=("Score", "mean"),
                Nb_succes=("Succes", "sum"),
                Nb_total=("Succes", "size")
            )
        )

    # =========================
    # TAUX DE RÉUSSITE
    # =========================

    result["Taux_reussite"] = (
        result["Nb_succes"]
        / result["Nb_total"]
        * 100
    )

    return result.sort_values(
        "Score_moyen",
        ascending=False
    )
