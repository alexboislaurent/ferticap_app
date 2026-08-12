def calc_ranking_with_success(data):

    tmp = data.copy()

    # =========================
    # SCORE
    # =========================

    # Conversion numérique
    tmp["Score"] = pd.to_numeric(
        tmp["Score"],
        errors="coerce"
    )

    # Une cellule Score vide = score 0
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
